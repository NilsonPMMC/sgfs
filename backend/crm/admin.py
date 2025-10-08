# crm/admin.py
import logging
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.http import HttpResponse
from django.db.models import Q
from .models import (
    CategoriaEntidade, Entidade, Contato,
    PessoaFisica, Responsavel, Beneficiario
)
import csv

logger = logging.getLogger('sgfs_app')

# =========================
# AÇÕES COMUNS (CSV, toggles)
# =========================

def export_as_csv_action(description="Exportar selecionados para CSV"):
    def action(modeladmin, request, queryset):
        meta = modeladmin.model._meta
        fields = [f.name for f in meta.fields]
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{meta.model_name}.csv"'
        writer = csv.writer(resp)
        writer.writerow(fields)
        for obj in queryset:
            writer.writerow([getattr(obj, f, "") for f in fields])
        return resp
    action.short_description = description
    return action

@admin.action(description="Marcar selecionados como DOADOR")
def marcar_como_doador(modeladmin, request, queryset):
    queryset.update(eh_doador=True)

@admin.action(description="Marcar selecionados como NÃO DOADOR")
def desmarcar_como_doador(modeladmin, request, queryset):
    queryset.update(eh_doador=False)

@admin.action(description="Marcar selecionados como GESTOR/RECEBEDOR")
def marcar_como_gestor(modeladmin, request, queryset):
    queryset.update(eh_gestor=True)

@admin.action(description="Marcar selecionados como NÃO GESTOR/RECEBEDOR")
def desmarcar_como_gestor(modeladmin, request, queryset):
    queryset.update(eh_gestor=False)

@admin.action(description="Ativar beneficiários selecionados")
def ativar_beneficiarios(modeladmin, request, queryset):
    queryset.update(ativo=True)

@admin.action(description="Desativar beneficiários selecionados")
def desativar_beneficiarios(modeladmin, request, queryset):
    queryset.update(ativo=False)


# =========================
# INLINES
# =========================

class ContatoInline(admin.TabularInline):
    model = Contato
    extra = 1
    autocomplete_fields = ["entidade"]  # ajuda se trocar entidade aqui
    fields = ("tipo_contato", "valor", "descricao")


class ResponsavelInline(admin.TabularInline):
    model = Responsavel
    extra = 0
    autocomplete_fields = ["pessoa_fisica"]
    fields = ("pessoa_fisica", "cargo")


class BeneficiarioInline(admin.TabularInline):
    model = Beneficiario
    extra = 0
    # entidade_intermediaria é a própria Entidade na tela pai
    autocomplete_fields = ["pessoa_fisica"]
    fields = ("pessoa_fisica", "data_vinculo", "ativo")
    readonly_fields = ("data_vinculo",)


# =========================
# ADMINS
# =========================

@admin.register(CategoriaEntidade)
class CategoriaEntidadeAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)
    actions = [export_as_csv_action()]


@admin.register(Entidade)
class EntidadeAdmin(admin.ModelAdmin):
    list_display = (
        "nome_fantasia", "razao_social", "documento",
        "categoria", "eh_doador", "eh_gestor",
        "vigencia_de", "vigencia_ate",
    )
    search_fields = (
        "nome_fantasia", "razao_social", "documento",
        "bairro", "logradouro", "cep",
    )
    list_filter = (
        "categoria", "eh_doador", "eh_gestor",
        ("vigencia_de", admin.DateFieldListFilter),
        ("vigencia_ate", admin.DateFieldListFilter),
    )
    inlines = [ContatoInline, ResponsavelInline, BeneficiarioInline]
    actions = [
        export_as_csv_action(),
        marcar_como_doador, desmarcar_como_doador,
        marcar_como_gestor, desmarcar_como_gestor,
    ]
    list_select_related = ("categoria",)
    fieldsets = (
        ("Identificação", {
            "fields": ("razao_social", "nome_fantasia", "documento", "categoria")
        }),
        ("Endereço", {
            "classes": ("collapse",),
            "fields": ("logradouro", "numero", "bairro", "cep"),
        }),
        ("Vigência/Observações", {
            "classes": ("collapse",),
            "fields": ("data_cadastro", "vigencia_de", "vigencia_ate", "observacoes"),
        }),
        ("Perfis", {
            "fields": ("eh_doador", "eh_gestor"),
        }),
    )


@admin.register(Contato)
class ContatoAdmin(admin.ModelAdmin):
    list_display = ("entidade", "tipo_contato", "valor", "descricao")
    list_filter = ("tipo_contato",)
    search_fields = ("valor", "descricao", "entidade__nome_fantasia", "entidade__razao_social", "entidade__documento")
    autocomplete_fields = ["entidade"]
    actions = [export_as_csv_action()]
    list_select_related = ("entidade",)


@admin.register(PessoaFisica)
class PessoaFisicaAdmin(admin.ModelAdmin):
    list_display = ("nome_completo", "cpf", "telefone", "email", "data_nascimento")
    search_fields = ("nome_completo", "cpf", "email", "telefone")
    list_filter = (("data_nascimento", admin.DateFieldListFilter),)
    actions = [export_as_csv_action()]


@admin.register(Responsavel)
class ResponsavelAdmin(admin.ModelAdmin):
    list_display = ("pessoa_fisica", "cargo", "entidade")
    search_fields = (
        "cargo",
        "pessoa_fisica__nome_completo", "pessoa_fisica__cpf",
        "entidade__nome_fantasia", "entidade__razao_social", "entidade__documento",
    )
    autocomplete_fields = ["pessoa_fisica", "entidade"]
    list_select_related = ("pessoa_fisica", "entidade")
    actions = [export_as_csv_action()]


@admin.register(Beneficiario)
class BeneficiarioAdmin(admin.ModelAdmin):
    list_display = ("pessoa_fisica", "entidade_intermediaria", "data_vinculo", "ativo")
    search_fields = (
        "pessoa_fisica__nome_completo", "pessoa_fisica__cpf",
        "entidade_intermediaria__nome_fantasia",
        "entidade_intermediaria__razao_social",
        "entidade_intermediaria__documento",
    )
    list_filter = (("data_vinculo", admin.DateFieldListFilter), "ativo")
    autocomplete_fields = ["pessoa_fisica", "entidade_intermediaria"]
    list_select_related = ("pessoa_fisica", "entidade_intermediaria")
    actions = [export_as_csv_action(), ativar_beneficiarios, desativar_beneficiarios]


# Branding
admin.site.site_header = "SGFS — Administração"
admin.site.site_title  = "SGFS Admin"
admin.site.index_title = "Gestão Administrativa (CRM)"
admin.site.unregister(User)

def send_new_password(modeladmin, request, queryset):
    logger.info(f"--- INICIANDO AÇÃO ADMIN: ENVIAR NOVA SENHA ---")
    
    # URL base do seu site
    base_url = "https://fundosocial.mogidascruzes.sp.gov.br"

    for user in queryset:
        try:
            password = get_random_string(12)
            user.set_password(password)
            user.save(update_fields=['password'])

            context = {
                'user_name': user.first_name or user.username,
                'password': password,
                'introductory_text': 'Conforme solicitado, uma nova senha de acesso foi gerada para você pelo administrador do sistema.',
                # CORREÇÃO: Construindo a URL do logo de forma explícita e completa
                'logo_url': f"{base_url}/static/crm/images/logo_sgfs.png",
                'login_url': f"{base_url}/login"
            }

            html_content = render_to_string('crm/password_email.html', context)
            text_content = f"Olá {context['user_name']},\n\nSua nova senha de acesso é: {password}"

            email = EmailMultiAlternatives(
                "Sua Nova Senha de Acesso ao SGFS",
                text_content,
                None,
                [user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)

            logger.info(f"E-mail de nova senha enviado com SUCESSO para {user.email}.")
        except Exception as e:
            logger.error(f"FALHA ao enviar nova senha para {user.email}: {e}", exc_info=True)
            modeladmin.message_user(request, f"Ocorreu um erro ao enviar a senha para {user.email}.", messages.ERROR)

    modeladmin.message_user(request, f"Uma nova senha foi enviada para os {queryset.count()} usuários selecionados.", messages.SUCCESS)
    logger.info(f"--- FIM DA AÇÃO ADMIN ---")

send_new_password.short_description = "Gerar e enviar nova senha por e-mail"

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    actions = [send_new_password]
    search_fields = ('username', 'first_name', 'last_name', 'email')