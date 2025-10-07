# crm/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EntidadeViewSet, CategoriaEntidadeViewSet, PessoaFisicaViewSet, 
    ResponsavelViewSet, BeneficiarioViewSet, ContatoViewSet,
    AniversariantesDoDiaView, AgendaContatosView, DoadorSearchView,
    DashboardView, CurrentUserView, AlertaViewSet
)

# Cria um router e registra nosso viewset com ele.
router = DefaultRouter()
router.register(r'entidades', EntidadeViewSet, basename='entidade')
router.register(r'categorias', CategoriaEntidadeViewSet, basename='categoria')
router.register(r'pessoas', PessoaFisicaViewSet, basename='pessoa')
router.register(r'responsaveis', ResponsavelViewSet, basename='responsavel')
router.register(r'beneficiarios', BeneficiarioViewSet, basename='beneficiario')
router.register(r'contatos', ContatoViewSet, basename='contato')
router.register(r'alertas', AlertaViewSet, basename='alerta')

# As URLs da API são determinadas automaticamente pelo router.
urlpatterns = [
    path('', include(router.urls)),
    path('aniversariantes/', AniversariantesDoDiaView.as_view(), name='aniversariantes-do-dia'),
    path('agenda/', AgendaContatosView.as_view(), name='agenda-contatos'),
    path('doador-search/', DoadorSearchView.as_view(), name='doador-search'),
    path('dashboard/', DashboardView.as_view(), name='dashboard-data'),
    path('users/me/', CurrentUserView.as_view(), name='current-user'),
]