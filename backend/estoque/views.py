# estoque/views.py
from rest_framework import viewsets, pagination, status
from django.db.models import Sum, F, IntegerField, DecimalField
from django.db.models.functions import Coalesce
import math
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from .models import Item, CategoriaDeItens, MovimentacaoEstoque, DoacaoRecebida, Kit, DoacaoRealizada, ItemSaida, KitSaida, ItemKit, ItemDoacaoRecebida
from .serializers import ItemSerializer, CategoriaDeItensSerializer, DoacaoRecebidaSerializer, KitSerializer, DoacaoRealizadaSerializer

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
            # Remove as movimentações antigas desta doação (mesmo critério usado no save())
            MovimentacaoEstoque.objects.filter(
                observacao=f"Entrada via doação ID {doacao.id}"
            ).delete()

            # Remove itens antigos
            doacao.itens_doados.all().delete()

            # Validação mínima e recriação
            if itens_data is None:
                itens_data = []
            if not isinstance(itens_data, list):
                return Response({'itens_doados': 'Deve ser uma lista.'}, status=400)

            objs = []
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
                objs.append(ItemDoacaoRecebida(doacao=doacao, item_id=item_id, quantidade=quantidade))

            # Ao criar os itens, o save() de ItemDoacaoRecebida cria as entradas de estoque automaticamente
            ItemDoacaoRecebida.objects.bulk_create(objs)

        return Response(self.get_serializer(doacao).data, status=200)

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
    """ API para registrar a saída de doações, com validação de estoque. """
    queryset = DoacaoRealizada.objects.all()
    serializer_class = DoacaoRealizadaSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        dados = request.data
        itens_saida_data = dados.pop('itens_saida', [])
        kits_saida_data = dados.pop('kits_saida', [])

        necessidades = {}
        for item_data in itens_saida_data:
            item_id = item_data['item']
            necessidades[item_id] = necessidades.get(item_id, 0) + float(item_data['quantidade'])
        
        for kit_data in kits_saida_data:
            kit = Kit.objects.get(id=kit_data['kit'])
            for item_no_kit in kit.itens_do_kit.all():
                item_id = item_no_kit.item.id
                qtde_total_item = float(item_no_kit.quantidade) * int(kit_data['quantidade'])
                necessidades[item_id] = necessidades.get(item_id, 0) + qtde_total_item
        
        itens_a_verificar = Item.objects.filter(id__in=necessidades.keys()).annotate(
            estoque_atual=Coalesce(Sum('movimentacoes__quantidade'), 0.0, output_field=DecimalField())
        )
        for item in itens_a_verificar:
            if (item.estoque_atual or 0) < necessidades[item.id]:
                raise ValidationError(f"Estoque insuficiente para o item '{item.nome}'. Saldo atual: {item.estoque_atual or 0}, Saída solicitada: {necessidades[item.id]}")

        entidade_gestora_id = dados.pop('entidade_gestora')
        doacao = DoacaoRealizada.objects.create(
            entidade_gestora_id=entidade_gestora_id,
            **dados
        )

        for item_id, quantidade in necessidades.items():
            MovimentacaoEstoque.objects.create(
                item_id=item_id,
                tipo_movimento='S',
                quantidade=-quantidade,
                observacao=f"Saída via doação realizada ID {doacao.id}"
            )
        
        for item_data in itens_saida_data:
            ItemSaida.objects.create(
                doacao_realizada=doacao,
                item_id=item_data['item'],
                quantidade=item_data['quantidade']
            )
        for kit_data in kits_saida_data:
            KitSaida.objects.create(
                doacao_realizada=doacao,
                kit_id=kit_data['kit'],
                quantidade=kit_data['quantidade']
            )

        serializer = self.get_serializer(doacao)
        return Response(serializer.data, status=201)