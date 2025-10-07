# estoque/admin.py
from django.contrib import admin
from django.http import HttpResponse
from django.db.models import Sum, F
from django.utils.html import format_html
import csv

from .models import (
    CategoriaDeItens, Item, Kit, ItemKit,
    DoacaoRecebida, ItemDoacaoRecebida,
    DoacaoRealizada, ItemSaida, KitSaida,
    MovimentacaoEstoque
)

# =========================
# AÇÕES COMUNS (CSV)
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

# =========================
# BÁSICOS
# =========================

@admin.register(CategoriaDeItens)
class CategoriaDeItensAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)
    actions = [export_as_csv_action()]


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("nome", "categoria", "unidade_medida")
    list_filter = ("categoria",)
    search_fields = ("nome", "descricao")
    fieldsets = (
        (None, {"fields": ("nome", "categoria", "unidade_medida")}),
        ("Detalhes Adicionais", {"fields": ("descricao",), "classes": ("collapse",)}),
    )
    autocomplete_fields = ("categoria",)
    actions = [export_as_csv_action()]


# =========================
# KIT + ITENS DO KIT
# =========================

class ItemKitInline(admin.TabularInline):
    model = ItemKit
    extra = 0
    autocomplete_fields = ("item",)
    fields = ("item", "quantidade")
    # unique_together (kit, item) já protege duplicados


@admin.register(Kit)
class KitAdmin(admin.ModelAdmin):
    list_display = ("nome", "descricao_resumida", "total_itens_ponderado")
    search_fields = ("nome", "descricao")
    inlines = [ItemKitInline]
    actions = [export_as_csv_action()]

    def descricao_resumida(self, obj):
        return (obj.descricao[:60] + "…") if obj.descricao and len(obj.descricao) > 60 else obj.descricao
    descricao_resumida.short_description = "Descrição"

    def total_itens_ponderado(self, obj):
        # soma das quantidades dos itens que compõem o kit
        agg = obj.itens_do_kit.aggregate(total=Sum("quantidade"))
        return agg["total"] or 0
    total_itens_ponderado.short_description = "Qtd. total (unidades)"


# =========================
# DOAÇÃO RECEBIDA + ITENS (Entradas)
# =========================

class ItemDoacaoRecebidaInline(admin.TabularInline):
    model = ItemDoacaoRecebida
    extra = 0
    autocomplete_fields = ("item",)
    fields = ("item", "quantidade")
    # A movimentação de ENTRADA é criada no save() do modelo ItemDoacaoRecebida

@admin.register(DoacaoRecebida)
class DoacaoRecebidaAdmin(admin.ModelAdmin):
    list_display = ("data_doacao", "doador_str", "qtd_itens", "data_registro")
    list_filter = (("data_doacao", admin.DateFieldListFilter),)
    search_fields = ("observacoes", )
    inlines = [ItemDoacaoRecebidaInline]
    actions = [export_as_csv_action()]

    readonly_fields = ("doador_str", "data_registro")
    fieldsets = (
        (None, {"fields": ("data_doacao", ("content_type", "object_id"), "doador_str", "observacoes")}),
        ("Sistema", {"fields": ("data_registro",), "classes": ("collapse",)}),
    )

    def doador_str(self, obj):
        # tenta mostrar algo legível do GenericForeignKey
        try:
            return str(obj.doador)
        except Exception:
            return "-"
    doador_str.short_description = "Doador"

    def qtd_itens(self, obj):
        agg = obj.itens_doados.aggregate(total=Sum("quantidade"))
        return agg["total"] or 0
    qtd_itens.short_description = "Qtd. Itens"


# =========================
# DOAÇÃO REALIZADA + ITENS/KITS (Saídas)
# =========================

class ItemSaidaInline(admin.TabularInline):
    model = ItemSaida
    extra = 0
    autocomplete_fields = ("item",)
    fields = ("item", "quantidade")


class KitSaidaInline(admin.TabularInline):
    model = KitSaida
    extra = 0
    autocomplete_fields = ("kit",)
    fields = ("kit", "quantidade")


@admin.register(DoacaoRealizada)
class DoacaoRealizadaAdmin(admin.ModelAdmin):
    list_display = ("data_saida", "entidade_gestora", "qtd_itens_total", "data_registro")
    list_filter = (("data_saida", admin.DateFieldListFilter), "entidade_gestora")
    search_fields = (
        "observacoes",
        "entidade_gestora__nome_fantasia", "entidade_gestora__documento",
        "entidade_gestora__razao_social",
    )
    autocomplete_fields = ("entidade_gestora",)
    inlines = [ItemSaidaInline, KitSaidaInline]
    actions = [export_as_csv_action()]
    list_select_related = ("entidade_gestora",)

    fieldsets = (
        (None, {"fields": ("data_saida", "entidade_gestora", "observacoes")}),
        ("Sistema", {"fields": ("data_registro",), "classes": ("collapse",)}),
    )
    readonly_fields = ("data_registro",)

    def qtd_itens_total(self, obj):
        # soma direta de itens avulsos + soma ponderada dos kits
        soma_itens = obj.itens_saida.aggregate(s=Sum("quantidade"))["s"] or 0
        # multiplicar cada kit pela soma de seus componentes
        total_kits = 0
        for ks in obj.kits_saida.select_related("kit").all():
            comp_total = ks.kit.itens_do_kit.aggregate(s=Sum("quantidade"))["s"] or 0
            total_kits += comp_total * (ks.quantidade or 0)
        return soma_itens + total_kits
    qtd_itens_total.short_description = "Qtd. Itens (total)"

    # --- Movimentação de SAÍDA automaticamente para novos registros de itens/kits ---
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        # Salva primeiro para garantir PKs
        for obj in instances:
            obj.save()

        formset.save_m2m()

        # Cria MovimentacaoEstoque de SAÍDA SOMENTE para objetos novos
        from .models import MovimentacaoEstoque, ItemKit

        if formset.model is ItemSaida:
            for obj in instances:
                if obj._state.adding:  # novo
                    MovimentacaoEstoque.objects.create(
                        item=obj.item,
                        tipo_movimento="S",
                        quantidade=obj.quantidade,
                        usuario_responsavel=request.user if request.user.is_authenticated else None,
                        observacao=f"Saída via doação (ItemSaida) ID {obj.pk} - Doação {obj.doacao_realizada_id}",
                    )

        elif formset.model is KitSaida:
            for obj in instances:
                if obj._state.adding:  # novo
                    # Expande o kit em itens e cria movimentações de saída
                    componentes = ItemKit.objects.filter(kit=obj.kit)
                    for comp in componentes:
                        qtd_total = (obj.quantidade or 0) * (comp.quantidade or 0)
                        if qtd_total and qtd_total > 0:
                            MovimentacaoEstoque.objects.create(
                                item=comp.item,
                                tipo_movimento="S",
                                quantidade=qtd_total,
                                usuario_responsavel=request.user if request.user.is_authenticated else None,
                                observacao=f"Saída via doação (KitSaida) ID {obj.pk} - Kit {obj.kit_id} expandido",
                            )

        # Importante: chamar o super para fluxo normal
        super().save_formset(request, form, formset, change)


# =========================
# ITENS RELACIONADOS (cadastros diretos)
# =========================

@admin.register(ItemKit)
class ItemKitAdmin(admin.ModelAdmin):
    list_display = ("kit", "item", "quantidade")
    search_fields = ("kit__nome", "item__nome")
    autocomplete_fields = ("kit", "item")
    list_select_related = ("kit", "item")
    actions = [export_as_csv_action()]


@admin.register(ItemDoacaoRecebida)
class ItemDoacaoRecebidaAdmin(admin.ModelAdmin):
    list_display = ("doacao", "item", "quantidade")
    search_fields = ("doacao__observacoes", "item__nome")
    list_filter = ("doacao__data_doacao",)
    autocomplete_fields = ("doacao", "item")
    list_select_related = ("doacao", "item")
    actions = [export_as_csv_action()]


@admin.register(ItemSaida)
class ItemSaidaAdmin(admin.ModelAdmin):
    list_display = ("doacao_realizada", "item", "quantidade")
    search_fields = ("doacao_realizada__observacoes", "item__nome")
    list_filter = ("doacao_realizada__data_saida",)
    autocomplete_fields = ("doacao_realizada", "item")
    list_select_related = ("doacao_realizada", "item")
    actions = [export_as_csv_action()]


@admin.register(KitSaida)
class KitSaidaAdmin(admin.ModelAdmin):
    list_display = ("doacao_realizada", "kit", "quantidade")
    search_fields = ("doacao_realizada__observacoes", "kit__nome")
    list_filter = ("doacao_realizada__data_saida",)
    autocomplete_fields = ("doacao_realizada", "kit")
    list_select_related = ("doacao_realizada", "kit")
    actions = [export_as_csv_action()]


# =========================
# MOVIMENTAÇÃO
# =========================

@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ("data_movimento", "item", "tipo_movimento", "quantidade", "usuario_responsavel", "observacao")
    list_filter = ("tipo_movimento", ("data_movimento", admin.DateFieldListFilter))
    search_fields = ("item__nome", "observacao", "usuario_responsavel__username")
    autocomplete_fields = ("item", "usuario_responsavel")
    list_select_related = ("item", "usuario_responsavel")
    date_hierarchy = "data_movimento"
    actions = [export_as_csv_action()]

# Branding opcional do Admin (se quiser unificar com o CRM)
admin.site.site_header = "SGFS — Administração"
admin.site.site_title  = "SGFS Admin"
admin.site.index_title = "Gestão Administrativa (CRM + Estoque)"
