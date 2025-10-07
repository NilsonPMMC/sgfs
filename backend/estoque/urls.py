# estoque/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ItemViewSet, CategoriaDeItensViewSet, DoacaoRecebidaViewSet,
    KitViewSet, DoacaoRealizadaViewSet, MovimentacaoEstoqueViewSet,
    EntidadeRelatorioAPIView
)

router = DefaultRouter()
router.register(r'itens', ItemViewSet, basename='item')
router.register(r'categorias-itens', CategoriaDeItensViewSet, basename='categoria-item')
router.register(r'doacoes-recebidas', DoacaoRecebidaViewSet, basename='doacao-recebida')
router.register(r'kits', KitViewSet, basename='kit')
router.register(r'doacoes-realizadas', DoacaoRealizadaViewSet, basename='doacao-realizada')
router.register(r'movimentacoes-estoque', MovimentacaoEstoqueViewSet, basename='movimentacao-estoque')

urlpatterns = [
    path('', include(router.urls)),
    path('relatorios/entidade/<int:pk>/', EntidadeRelatorioAPIView.as_view()),
]