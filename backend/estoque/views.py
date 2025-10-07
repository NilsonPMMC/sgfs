# estoque/views.py
from rest_framework import viewsets, pagination, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum, DecimalField
from django.db.models.functions import Coalesce
from django.utils.timezone import now
import math
import json
from .models import (
    Item, CategoriaDeItens, MovimentacaoEstoque, DoacaoRecebida, Kit,
    DoacaoRealizada, ItemSaida, KitSaida, ItemKit, ItemDoacaoRecebida
)
from .serializers import (
    ItemSerializer, CategoriaDeItensSerializer, DoacaoRecebidaSerializer,
    KitSerializer, DoacaoRealizadaSerializer, MovimentacaoEstoqueSerializer
)
from crm.models import Entidade

class CategoriaDeItensViewSet(viewsets.ModelViewSet):
    """ API para gerenciar as Categorias de Itens. """
    queryset = CategoriaDeItens.objects.all().order_by('nome')
    serializer_class = CategoriaDeItensSerializer

class ItemViewSet(viewsets.ModelViewSet):
    """
    Endpoint da API que permite que Itens sejam visualizados ou editados.
    Agora inclui o cálculo de estoque.
    """
    serializer_class = ItemSerializer
    search_fields = ['nome', 'descricao']
    
    def get_queryset(self):
        """
        Sobrescreve o queryset para incluir a soma das movimentações de estoque.
        """
        return Item.objects.annotate(
            estoque_atual=Coalesce(Sum('movimentacoes__quantidade'), 0.0, output_field=DecimalField())
        ).order_by('nome')

class DoacaoRecebidaViewSet(viewsets.ModelViewSet):
    """ API para gerenciar as Doações Recebidas """
    permission_classes = [IsAuthenticated]

    queryset = DoacaoRecebida.objects.all().order_by('-data_doacao')
    serializer_class = DoacaoRecebidaSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        # Se o frontend não enviou content_type, preenche automaticamente com Entidade
        if not data.get('content_type'):
            from django.contrib.contenttypes.models import ContentType
            from crm.models import Entidade  # ajuste se seu app for outro
            ct = ContentType.objects.get_for_model(Entidade)
            data['content_type'] = ct.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        doacao = self.get_object()

        # NÃO mutar request.data (QueryDict) – copie:
        data = request.data.copy()

        # Só altere a lista se o payload trouxer 'itens_doados'
        has_itens = 'itens_doados' in data
        itens_data = data.pop('itens_doados', None)

        # Se veio como string JSON, tentar parsear
        if isinstance(itens_data, str):
            import json
            try:
                itens_data = json.loads(itens_data)
            except json.JSONDecodeError:
                return Response({'itens_doados': 'Formato inválido (JSON esperado).'}, status=400)

        # Atualiza campos simples (data_doacao, observacoes, content/object_id, etc.)
        serializer = self.get_serializer(doacao, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        doacao = serializer.save()

        # Se o cliente enviou itens_doados, substitui a lista (apaga e recria)
        if has_itens:
            # Remove as movimentações antigas desta doação
            MovimentacaoEstoque.objects.filter(
                observacao=f"Entrada via doação ID {doacao.id}"
            ).delete()

            # Remove itens antigos
            doacao.itens_doados.all().delete()

            # (re)cria itens chamando save() para gerar as movimentações
            if itens_data is None:
                itens_data = []
            if not isinstance(itens_data, list):
                return Response({'itens_doados': 'Deve ser uma lista.'}, status=400)

            for idx, i in enumerate(itens_data):
                if not isinstance(i, dict):
                    return Response({f'itens_doados[{idx}]': 'Objeto inválido.'}, status=400)

                item_id = i.get('item_id') or i.get('item')
                quantidade = i.get('quantidade')

                try:
                    quantidade = float(quantidade)
                except (TypeError, ValueError):
                    return Response({f'itens_doados[{idx}].quantidade': 'Número inválido.'}, status=400)

                if not item_id:
                    return Response({f'itens_doados[{idx}].item': 'Obrigatório.'}, status=400)
                if quantidade <= 0:
                    return Response({f'itens_doados[{idx}].quantidade': 'Deve ser > 0.'}, status=400)

                # IMPORTANTE: usar create() para disparar o save() do modelo
                ItemDoacaoRecebida.objects.create(
                    doacao=doacao,
                    item_id=item_id,
                    quantidade=quantidade
                )

        return Response(self.get_serializer(doacao).data, status=200)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        # remove as movimentações criadas pelo save() de ItemDoacaoRecebida
        MovimentacaoEstoque.objects.filter(
            observacao=f"Entrada via doação ID {obj.id}"
        ).delete()
        # apagar a doação vai apagar ItemDoacaoRecebida via CASCADE
        super().destroy(request, *args, **kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)

class StandardResultsSetPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class KitViewSet(viewsets.ModelViewSet):
    """ API para gerenciar os Kits e seus itens, agora com cálculo de montagem. """
    queryset = Kit.objects.all().order_by('nome')
    serializer_class = KitSerializer
    pagination_class = StandardResultsSetPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        queryset = queryset.prefetch_related(
            'itens_do_kit__item__movimentacoes'
        )

        itens_ids = ItemKit.objects.filter(kit__in=queryset).values_list('item_id', flat=True)
        estoques = {
            item.id: item.estoque_atual or 0
            for item in Item.objects.filter(id__in=itens_ids).annotate(
                estoque_atual=Coalesce(Sum('movimentacoes__quantidade'), 0, output_field=DecimalField())
            )
        }

        for kit in queryset:
            quantidades_possiveis = []
            if not kit.itens_do_kit.all().exists():
                kit.quantidade_montavel = 0
                continue

            for item_no_kit in kit.itens_do_kit.all():
                estoque_do_item = estoques.get(item_no_kit.item.id, 0)
                if item_no_kit.quantidade > 0:
                    qnt_possivel = math.floor(float(estoque_do_item) / float(item_no_kit.quantidade))
                    quantidades_possiveis.append(qnt_possivel)
                else:
                    quantidades_possiveis.append(float('inf')) 
            
            kit.quantidade_montavel = min(quantidades_possiveis) if quantidades_possiveis else 0

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class DoacaoRealizadaViewSet(viewsets.ModelViewSet):
    queryset = DoacaoRealizada.objects.all()
    serializer_class = DoacaoRealizadaSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        # 1) SEMPRE trabalhe numa cópia
        dados = request.data.copy()

        # 2) Extraia listas e normalize (podem vir como string JSON)
        itens_saida_data = dados.pop('itens_saida', [])
        kits_saida_data = dados.pop('kits_saida', [])

        if isinstance(itens_saida_data, str):
            try:
                itens_saida_data = json.loads(itens_saida_data) or []
            except json.JSONDecodeError:
                raise ValidationError({'itens_saida': 'Formato inválido (JSON esperado).'})

        if isinstance(kits_saida_data, str):
            try:
                kits_saida_data = json.loads(kits_saida_data) or []
            except json.JSONDecodeError:
                raise ValidationError({'kits_saida': 'Formato inválido (JSON esperado).'})

        if not isinstance(itens_saida_data, list):
            raise ValidationError({'itens_saida': 'Deve ser uma lista.'})
        if not isinstance(kits_saida_data, list):
            raise ValidationError({'kits_saida': 'Deve ser uma lista.'})

        # 3) Agregue necessidades (itens + kits)
        necessidades = {}
        for idx, i in enumerate(itens_saida_data):
            item_id = i.get('item')
            qtd = i.get('quantidade')
            try:
                qtd = float(qtd)
            except (TypeError, ValueError):
                raise ValidationError({f'itens_saida[{idx}].quantidade': 'Número inválido.'})
            if not item_id:
                raise ValidationError({f'itens_saida[{idx}].item': 'Obrigatório.'})
            if qtd <= 0:
                raise ValidationError({f'itens_saida[{idx}].quantidade': 'Deve ser > 0.'})
            necessidades[item_id] = necessidades.get(item_id, 0) + qtd

        for idx, k in enumerate(kits_saida_data):
            kit_id = k.get('kit')
            qtd_kits = k.get('quantidade')
            try:
                qtd_kits = int(qtd_kits)
            except (TypeError, ValueError):
                raise ValidationError({f'kits_saida[{idx}].quantidade': 'Número inválido.'})
            if not kit_id:
                raise ValidationError({f'kits_saida[{idx}].kit': 'Obrigatório.'})
            if qtd_kits <= 0:
                raise ValidationError({f'kits_saida[{idx}].quantidade': 'Deve ser > 0.'})

            kit = Kit.objects.get(id=kit_id)
            for item_no_kit in kit.itens_do_kit.all():
                item_id = item_no_kit.item_id
                necessidades[item_id] = necessidades.get(item_id, 0) + float(item_no_kit.quantidade) * qtd_kits

        # 4) Valide estoque
        itens_a_verificar = Item.objects.filter(id__in=necessidades.keys()).annotate(
            estoque_atual=Coalesce(Sum('movimentacoes__quantidade'), 0.0, output_field=DecimalField())
        )
        for item in itens_a_verificar:
            if (item.estoque_atual or 0) < necessidades[item.id]:
                raise ValidationError(
                    f"Estoque insuficiente para o item '{item.nome}'. "
                    f"Saldo atual: {item.estoque_atual or 0}, Saída solicitada: {necessidades[item.id]}"
                )

        # 5) Crie a doação (copiando campos simples)
        entidade_gestora_id = dados.pop('entidade_gestora')
        doacao = DoacaoRealizada.objects.create(
            entidade_gestora_id=entidade_gestora_id,
            **dados
        )

        # 6) Movimentações (uma por item agregado)
        movs = [
            MovimentacaoEstoque(
                item_id=item_id,
                tipo_movimento='S',
                quantidade=-qtd_total,
                observacao=f"Saída via doação realizada ID {doacao.id}"
            )
            for item_id, qtd_total in necessidades.items()
        ]
        MovimentacaoEstoque.objects.bulk_create(movs)

        # 7) Registros de itens/kits da saída (para histórico)
        ItemSaida.objects.bulk_create([
            ItemSaida(doacao_realizada=doacao, item_id=i['item'], quantidade=i['quantidade'])
            for i in itens_saida_data
        ])
        KitSaida.objects.bulk_create([
            KitSaida(doacao_realizada=doacao, kit_id=k['kit'], quantidade=k['quantidade'])
            for k in kits_saida_data
        ])

        # 8) Retorno
        return Response(self.get_serializer(doacao).data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        # remove as movimentações de saída lançadas no create()
        MovimentacaoEstoque.objects.filter(
            observacao=f"Saída via doação realizada ID {obj.id}"
        ).delete()
        # apaga a doação (e itens/kits de saída)
        super().destroy(request, *args, **kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)

class MovimentacaoEstoqueViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MovimentacaoEstoqueSerializer

    def get_queryset(self):
        return MovimentacaoEstoque.objects.select_related('item','usuario_responsavel').order_by('-data_movimento')

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        # aceita "item" como alias de "item_id"
        if 'item' in data and 'item_id' not in data:
            data['item_id'] = data.pop('item')
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class EntidadeRelatorioAPIView(APIView):
    """
    Retorna dados da entidade + histórico de doações (entradas e saídas)
    """
    def get(self, request, pk):
        try:
            ent = Entidade.objects.select_related('categoria').get(pk=pk)
        except Entidade.DoesNotExist:
            return Response({'detail':'Entidade não encontrada.'}, status=404)

        # entradas: entidade como doadora (ContentType Entidade + object_id = pk)
        from django.contrib.contenttypes.models import ContentType
        ct_entidade = ContentType.objects.get_for_model(Entidade)
        entradas = DoacaoRecebida.objects.filter(content_type=ct_entidade, object_id=pk).order_by('-data_doacao')

        # saídas: entidade como beneficiária/gestora
        saidas = DoacaoRealizada.objects.filter(entidade_gestora_id=pk).order_by('-data_saida')

        # serializa
        s_ent = {
            'id': ent.id,
            'nome': ent.nome,
            'nome_fantasia': ent.nome_fantasia,
            'razao_social': ent.razao_social,
            'documento': ent.documento,
            'bairro': ent.bairro,
            'data_cadastro': getattr(ent, 'data_cadastro', None),
            'categoria': {'id': getattr(ent.categoria, 'id', None), 'nome': getattr(ent.categoria, 'nome', None)} if getattr(ent, 'categoria', None) else None
        }
        s_entradas = DoacaoRecebidaSerializer(entradas, many=True).data
        s_saidas   = DoacaoRealizadaSerializer(saidas, many=True).data

        ultimo = None
        if saidas.exists():
            ultimo = saidas.first().data_saida

        resumo = {
            'entradas': entradas.count(),
            'saidas': saidas.count(),
            'ultimo_atendimento': ultimo
        }
        return Response({
            'entidade': s_ent,
            'resumo': resumo,
            'entradas': s_entradas,
            'saidas': s_saidas
        })