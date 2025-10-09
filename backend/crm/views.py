# crm/views.py
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, BooleanFilter, NumberFilter
from django.contrib.contenttypes.models import ContentType
from django.db.models.functions import Coalesce, TruncMonth
from django.db.models import Sum, F, IntegerField, DecimalField, Count, Q, Max
from django.utils import timezone
from datetime import date, timedelta
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Entidade, CategoriaEntidade, PessoaFisica, Responsavel, Beneficiario, Contato, Alerta
from .serializers import (
    EntidadeSerializer, CategoriaEntidadeSerializer, PessoaFisicaSerializer,
    ResponsavelSerializer, BeneficiarioSerializer, ResponsavelWriteSerializer, BeneficiarioWriteSerializer,
    ContatoSerializer, ContatoWriteSerializer, UserSerializer, AlertaSerializer
)
from estoque.models import Item, DoacaoRealizada, DoacaoRecebida
from estoque.serializers import DoacaoRealizadaSerializer, DoacaoRecebidaSerializer

class CurrentUserView(APIView):
    """ Retorna os dados do usuário atualmente logado. """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class CategoriaEntidadeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint que apenas lista as categorias de entidades.
    """
    queryset = CategoriaEntidade.objects.all().order_by('nome')
    serializer_class = CategoriaEntidadeSerializer

class EntidadeFilter(FilterSet):
    permission_classes = [IsAuthenticated]
    
    eh_gestor = BooleanFilter(field_name="eh_gestor")
    eh_doador = BooleanFilter(field_name="eh_doador")
    categoria = NumberFilter(field_name="categoria_id")

    class Meta:
        model = Entidade
        fields = ["eh_gestor", "eh_doador", "categoria"]

class EntidadeViewSet(viewsets.ModelViewSet):
    """
    Endpoint da API que permite que as entidades sejam visualizadas ou editadas.
    """
    permission_classes = [IsAuthenticated]

    queryset = Entidade.objects.all().order_by('nome_fantasia')
    serializer_class = EntidadeSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = EntidadeFilter
    search_fields = ['nome_fantasia', 'documento', 'razao_social']
    ordering_fields = ["razao_social", "nome_fantasia", "id"]
    ordering = ["razao_social"]

    def get_queryset(self):
        qs = super().get_queryset()

        classificacao = self.request.query_params.get('classificacao')
        if classificacao == 'gestor':
            qs = qs.filter(eh_gestor=True)
        elif classificacao == 'doador':
            qs = qs.filter(eh_doador=True)
        elif classificacao == 'ambos':
            qs = qs.filter(eh_gestor=True, eh_doador=True)

        categoria = self.request.query_params.get('categoria')
        if categoria:
            qs = qs.filter(categoria_id=categoria)

        bairro = self.request.query_params.get('bairro')
        if bairro:
            qs = qs.filter(bairro__icontains=bairro)

        # IMPORTANTÍSSIMO: seu relatório envia “search”
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(nome_fantasia__icontains=search) |
                Q(razao_social__icontains=search) |
                Q(documento__icontains=search)
            )

        return qs

    # NOVA AÇÃO: Histórico de Atendimentos (Saídas)
    @action(detail=True, methods=['get'])
    def atendimentos(self, request, pk=None):
        entidade = self.get_object()
        # Filtra todas as doações realizadas para esta entidade
        queryset = DoacaoRealizada.objects.filter(entidade_gestora=entidade).order_by('-data_saida')
        serializer = DoacaoRealizadaSerializer(queryset, many=True)
        return Response(serializer.data)

    # NOVA AÇÃO: Histórico de Doações (Entradas)
    @action(detail=True, methods=['get'])
    def doacoes(self, request, pk=None):
        entidade = self.get_object()
        # Filtra todas as doações recebidas desta entidade (usando o GenericForeignKey)
        content_type = ContentType.objects.get_for_model(Entidade)
        queryset = DoacaoRecebida.objects.filter(content_type=content_type, object_id=entidade.id).order_by('-data_doacao')
        serializer = DoacaoRecebidaSerializer(queryset, many=True)
        return Response(serializer.data)

class PessoaFisicaViewSet(viewsets.ModelViewSet):
    """
    Endpoint da API que permite que Pessoas Físicas sejam visualizadas ou editadas.
    """
    permission_classes = [IsAuthenticated]

    queryset = PessoaFisica.objects.all().order_by('nome_completo')
    serializer_class = PessoaFisicaSerializer
    search_fields = ['nome_completo', 'cpf']

class ResponsavelViewSet(viewsets.ModelViewSet):
    """ API para gerenciar o vínculo de Responsáveis """
    permission_classes = [IsAuthenticated]

    queryset = Responsavel.objects.all()
    serializer_class = ResponsavelSerializer

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ResponsavelWriteSerializer
        return super().get_serializer_class()

class BeneficiarioViewSet(viewsets.ModelViewSet):
    """ API para gerenciar o vínculo de Beneficiários """
    permission_classes = [IsAuthenticated]

    queryset = Beneficiario.objects.all()
    serializer_class = BeneficiarioSerializer

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BeneficiarioWriteSerializer
        return super().get_serializer_class()

class ContatoViewSet(viewsets.ModelViewSet):
    """ API para gerenciar os Contatos """
    permission_classes = [IsAuthenticated]
    
    queryset = Contato.objects.all()
    serializer_class = ContatoSerializer
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ContatoWriteSerializer
        return super().get_serializer_class()

class AniversariantesDoDiaView(APIView):
    """
    Retorna uma lista de pessoas que fazem aniversário no dia atual.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        hoje = date.today()
        aniversariantes = PessoaFisica.objects.filter(
            data_nascimento__day=hoje.day,
            data_nascimento__month=hoje.month
        )
        serializer = PessoaFisicaSerializer(aniversariantes, many=True)
        return Response(serializer.data)

class AgendaContatosView(APIView):
    """
    Retorna uma lista "achatada" de todos os vínculos (Responsáveis e Beneficiados),
    combinando dados da pessoa, do vínculo e da entidade.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        contatos_finais = []

        responsaveis = Responsavel.objects.select_related('pessoa_fisica', 'entidade').all()
        for resp in responsaveis:
            contatos_finais.append({
                'id_vinculo': f"resp-{resp.id}",
                'pessoa_id': resp.pessoa_fisica.id,
                'nome_completo': resp.pessoa_fisica.nome_completo,
                'telefone': resp.pessoa_fisica.telefone,
                'email': resp.pessoa_fisica.email,
                'entidade_nome': resp.entidade.nome_fantasia,
                'entidade_id': resp.entidade.id,
                'tipo_vinculo': 'Responsável',
                'cargo': resp.cargo,
            })

        beneficiados = Beneficiario.objects.select_related('pessoa_fisica', 'entidade_intermediaria').all()
        for ben in beneficiados:
            contatos_finais.append({
                'id_vinculo': f"ben-{ben.id}",
                'pessoa_id': ben.pessoa_fisica.id,
                'nome_completo': ben.pessoa_fisica.nome_completo,
                'telefone': ben.pessoa_fisica.telefone,
                'email': ben.pessoa_fisica.email,
                'entidade_nome': ben.entidade_intermediaria.nome_fantasia,
                'entidade_id': ben.entidade_intermediaria.id,
                'tipo_vinculo': 'Beneficiado',
                'cargo': None,
            })

        contatos_finais = sorted(contatos_finais, key=lambda c: c['nome_completo'])
        
        return Response(contatos_finais)

class DoadorSearchView(APIView):
    """
    Busca tanto em PessoaFisica quanto em Entidade e retorna uma lista unificada.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        query = request.query_params.get('query', '')
        resultados = []

        if query:
            # Busca em Pessoas Físicas
            pessoas = PessoaFisica.objects.filter(nome_completo__icontains=query)[:5]
            ct_pessoa = ContentType.objects.get_for_model(PessoaFisica)
            for pessoa in pessoas:
                resultados.append({
                    'id': pessoa.id,
                    'nome': pessoa.nome_completo,
                    'tipo': 'Pessoa Física',
                    'content_type_id': ct_pessoa.id
                })
            
            # Busca em Entidades
            entidades = Entidade.objects.filter(nome_fantasia__icontains=query)[:5]
            ct_entidade = ContentType.objects.get_for_model(Entidade)
            for entidade in entidades:
                resultados.append({
                    'id': entidade.id,
                    'nome': entidade.nome_fantasia,
                    'tipo': 'Entidade',
                    'content_type_id': ct_entidade.id
                })

        return Response(resultados)

class DashboardView(APIView):
    """
    Agrega todos os dados necessários para o painel de controle principal.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        hoje = date.today()
        ano_atual = hoje.year
        trinta_dias_atras = hoje - timedelta(days=30)

        # 1. Indicadores de Estoque
        total_itens = Item.objects.count()
        # (A lógica de estoque baixo/zerado depende de movimentações, vamos adicionar um placeholder)
        itens_com_estoque = Item.objects.annotate(
            estoque=Coalesce(Sum('movimentacoes__quantidade'), 0.0, output_field=DecimalField())
        )
        itens_zerados = itens_com_estoque.filter(estoque__lte=0).count()
        itens_estoque_baixo = itens_com_estoque.filter(estoque__gt=0, estoque__lte=10).count()

        # 2. Indicadores de Doações (Últimos 30 dias)
        doacoes_recebidas_recente = DoacaoRecebida.objects.filter(data_doacao__gte=trinta_dias_atras).count()
        doacoes_realizadas_recente = DoacaoRealizada.objects.filter(data_saida__gte=trinta_dias_atras).count()

        # 3. Ranking de Entidades Gestoras (por nº de doações recebidas)
        ranking_entidades = DoacaoRealizada.objects.values('entidade_gestora__nome_fantasia') \
            .annotate(total=Count('id')) \
            .order_by('-total')[:5] # Top 5

        # 4. Ranking de Doadores (genérico, precisa ser refinado se quiser juntar PF e PJ)
        # Por enquanto, vamos rankear apenas Entidades Doadoras
        ranking_doadores = DoacaoRecebida.objects.filter(content_type=ContentType.objects.get_for_model(Entidade)) \
            .values('object_id') \
            .annotate(total=Count('id')) \
            .order_by('-total')[:5]
        # Mapeia os IDs para nomes
        doadores_entidades = Entidade.objects.filter(id__in=[d['object_id'] for d in ranking_doadores])
        mapa_doadores = {ent.id: ent.nome_fantasia for ent in doadores_entidades}
        ranking_doadores_final = [
            {'nome_doador': mapa_doadores.get(d['object_id']), 'total': d['total']} for d in ranking_doadores
        ]

        # 5. Aniversariantes (da semana)
        proximos_7_dias = hoje + timedelta(days=7)
        aniversariantes = []
        # Caso 1: A semana está dentro do mesmo mês
        if hoje.month == proximos_7_dias.month:
            aniversariantes = PessoaFisica.objects.filter(
                data_nascimento__month=hoje.month,
                data_nascimento__day__gte=hoje.day,
                data_nascimento__day__lte=proximos_7_dias.day
            ).order_by('data_nascimento__day')
        # Caso 2: A semana vira o mês
        else:
            aniversariantes = PessoaFisica.objects.filter(
                Q(data_nascimento__month=hoje.month, data_nascimento__day__gte=hoje.day) |
                Q(data_nascimento__month=proximos_7_dias.month, data_nascimento__day__lte=proximos_7_dias.day)
            ).order_by('data_nascimento__month', 'data_nascimento__day')
        
        # 6. Movimentações Mensais
        meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        entradas_por_mes = {i: 0 for i in range(1, 13)}
        saidas_por_mes = {i: 0 for i in range(1, 13)}

        entradas_qs = DoacaoRecebida.objects.filter(data_doacao__year=ano_atual).annotate(month=TruncMonth('data_doacao')).values('month').annotate(total=Count('id')).values('month', 'total')
        for entrada in entradas_qs:
            entradas_por_mes[entrada['month'].month] = entrada['total']

        saidas_qs = DoacaoRealizada.objects.filter(data_saida__year=ano_atual).annotate(month=TruncMonth('data_saida')).values('month').annotate(total=Count('id')).values('month', 'total')
        for saida in saidas_qs:
            saidas_por_mes[saida['month'].month] = saida['total']
        
        movimentacoes_mensais = {
            "labels": meses,
            "entradas": list(entradas_por_mes.values()),
            "saidas": list(saidas_por_mes.values())
        }

        # Monta a resposta final
        data = {
            'indicadores_estoque': {
                'total_itens': total_itens,
                'itens_zerados': itens_zerados,
                'itens_estoque_baixo': itens_estoque_baixo,
            },
            'indicadores_doacoes': {
                'entradas_30d': doacoes_recebidas_recente,
                'saidas_30d': doacoes_realizadas_recente,
            },
            'ranking_entidades_gestoras': list(ranking_entidades),
            'ranking_doadores': ranking_doadores_final,
            'aniversariantes_semana': PessoaFisicaSerializer(aniversariantes, many=True).data,
            'movimentacoes_mensais': movimentacoes_mensais
        }
        
        return Response(data)

class AlertaViewSet(viewsets.ModelViewSet):
    queryset = Alerta.objects.all().order_by('-criado_em')
    serializer_class = AlertaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['lido']

    def get_queryset(self):
        qs = super().get_queryset()
        lido = self.request.query_params.get('lido')
        if lido is not None:
            if lido.lower() in ('true', '1'):
                qs = qs.filter(lido=True)
            if lido.lower() in ('false', '0'):
                qs = qs.filter(lido=False)
        return qs

    @action(detail=False, methods=['post'])
    def marcar_todos_como_lidos(self, request):
        count = Alerta.objects.filter(lido=False).update(lido=True)
        return Response({'marked': count})

    @action(detail=True, methods=['post'])
    def marcar_como_lido(self, request, pk=None):
        alerta = self.get_object()
        alerta.lido = True
        alerta.save(update_fields=['lido'])
        return Response({'ok': True})

    @action(detail=False, methods=['post'])
    def gerar_pendentes(self, request):
        hoje = timezone.now().date()
        limite = hoje - timedelta(days=60)
        gestoras = Entidade.objects.filter(eh_gestor=True)
        criados = 0
        for g in gestoras:
            ultima_saida = (DoacaoRealizada.objects
                            .filter(entidade_gestora=g)
                            .order_by('-data_saida')
                            .values_list('data_saida', flat=True)
                            .first())

            if (not ultima_saida) or (ultima_saida <= limite):
                titulo = 'Entidade sem atendimento há 60+ dias'
                existe = Alerta.objects.filter(entidade=g, titulo=titulo, lido=False).exists()
                if not existe:
                    Alerta.objects.create(
                        titulo=titulo,
                        mensagem=f'A entidade {g.nome_fantasia or g.razao_social} está sem atendimento desde {ultima_saida.strftime("%d/%m/%Y") if ultima_saida else "sempre"}.',
                        entidade=g,
                        severity='warn'
                    )
                    criados += 1
        return Response({'gerados': criados}, status=status.HTTP_201_CREATED)

    # --- NOVA AÇÃO ADICIONADA ---
    @action(detail=False, methods=['post'], url_path='gerar-alertas-vigencia')
    def gerar_alertas_vigencia(self, request):
        """
        Gera (idempotente) alertas para entidades com vigência vencida ou próxima do vencimento.
        """
        hoje = timezone.now().date()
        limite_vencimento = hoje + timedelta(days=30)
        criados = 0

        # 1. Alertas para vigências vencidas
        entidades_vencidas = Entidade.objects.filter(vigencia_ate__lt=hoje)
        for entidade in entidades_vencidas:
            titulo = 'Vigência de atendimento vencida'
            # Evita duplicar o mesmo alerta se ele ainda não foi lido
            existe = Alerta.objects.filter(entidade=entidade, titulo=titulo, lido=False).exists()
            if not existe:
                Alerta.objects.create(
                    titulo=titulo,
                    mensagem=f'A vigência da entidade {entidade.nome_fantasia or entidade.razao_social} venceu em {entidade.vigencia_ate.strftime("%d/%m/%Y")}.',
                    entidade=entidade,
                    severity='danger' # Alerta de perigo (vermelho)
                )
                criados += 1

        # 2. Alertas para vigências próximas do vencimento (próximos 30 dias)
        entidades_proximas = Entidade.objects.filter(vigencia_ate__gte=hoje, vigencia_ate__lte=limite_vencimento)
        for entidade in entidades_proximas:
            titulo = 'Vigência próxima do vencimento'
            existe = Alerta.objects.filter(entidade=entidade, titulo=titulo, lido=False).exists()
            if not existe:
                dias_restantes = (entidade.vigencia_ate - hoje).days
                Alerta.objects.create(
                    titulo=titulo,
                    mensagem=f'A vigência da entidade {entidade.nome_fantasia or entidade.razao_social} vencerá em {dias_restantes} dias ({entidade.vigencia_ate.strftime("%d/%m/%Y")}).',
                    entidade=entidade,
                    severity='warn' # Alerta de aviso (amarelo)
                )
                criados += 1
                
        return Response({'gerados': criados}, status=status.HTTP_201_CREATED)