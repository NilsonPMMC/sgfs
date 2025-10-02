# estoque/admin.py

from django.contrib import admin
from .models import CategoriaDeItens, Item

@admin.register(CategoriaDeItens)
class CategoriaDeItensAdmin(admin.ModelAdmin):
    """
    Configuração para a gestão de Categorias de Itens no painel admin.
    """
    list_display = ('nome',)  # Mostra o nome da categoria na lista
    search_fields = ('nome',) # Adiciona uma barra de busca para o nome


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """
    Configuração para a gestão de Itens, agora com mais detalhes.
    """
    # Mostra o nome, a categoria associada e a unidade de medida na lista principal
    list_display = ('nome', 'categoria', 'unidade_medida')
    
    # Adiciona um filtro na barra lateral para filtrar itens por categoria
    list_filter = ('categoria',)
    
    # Adiciona uma barra de busca que procura no nome e na descrição do item
    search_fields = ('nome', 'descricao')
    
    # Organiza os campos no formulário de edição
    fieldsets = (
        (None, {
            'fields': ('nome', 'categoria', 'unidade_medida')
        }),
        ('Detalhes Adicionais', {
            'fields': ('descricao',),
            'classes': ('collapse',) # Começa "recolhido" para uma interface mais limpa
        }),
    )