# crm/admin.py
from django.contrib import admin
from .models import CategoriaEntidade, Entidade, Contato, PessoaFisica, Responsavel, Beneficiario

# Customização para exibir contatos diretamente na página da Entidade
class ContatoInline(admin.TabularInline):
    model = Contato
    extra = 1 # Quantos campos de contato em branco exibir

@admin.register(Entidade)
class EntidadeAdmin(admin.ModelAdmin):
    list_display = ('nome_fantasia', 'razao_social', 'cnpj', 'categoria', 'eh_doador', 'eh_gestor')
    search_fields = ('nome_fantasia', 'razao_social', 'cnpj')
    list_filter = ('categoria', 'eh_doador', 'eh_gestor')
    inlines = [ContatoInline] # Adiciona os contatos na mesma tela

@admin.register(PessoaFisica)
class PessoaFisicaAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'cpf', 'telefone', 'email')
    search_fields = ('nome_completo', 'cpf')

# Registra os outros modelos de forma simples
admin.site.register(CategoriaEntidade)
admin.site.register(Responsavel)
admin.site.register(Beneficiario)