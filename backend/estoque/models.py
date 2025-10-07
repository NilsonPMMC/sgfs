# estoque/models.py
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from crm.models import Entidade

class CategoriaDeItens(models.Model):
    nome = models.CharField(max_length=150, unique=True)
    
    class Meta:
        verbose_name = "Categoria de Item"
        verbose_name_plural = "Categorias de Itens"

    def __str__(self):
        return self.nome

# Modelo que define um item do inventário (ex: "Arroz", "Cesta Básica", "Sabonete")
class Item(models.Model):
    # O campo 'item' da sua planilha será nosso campo 'nome'
    nome = models.CharField(max_length=150, unique=True)
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    unidade_medida = models.CharField(max_length=50, verbose_name="Unidade de Medida")
    
    # Relacionamento com a Categoria
    categoria = models.ForeignKey(
        CategoriaDeItens, 
        on_delete=models.SET_NULL, # Se uma categoria for deletada, o item não será.
        null=True, 
        blank=True
    )
    
    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Itens"

    def __str__(self):
        return self.nome

# Modelo para definir um "Kit" (um agrupamento de itens)
class Kit(models.Model):
    nome = models.CharField(max_length=150, unique=True)
    descricao = models.TextField(blank=True, verbose_name="Descrição")

    class Meta:
        verbose_name = "Kit"
        verbose_name_plural = "Kits"
    
    def __str__(self):
        return self.nome

# Tabela de ligação que define a composição de um Kit (quais itens e em que quantidade)
class ItemKit(models.Model):
    kit = models.ForeignKey(Kit, on_delete=models.CASCADE, related_name='itens_do_kit')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="Item")
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Item do Kit"
        verbose_name_plural = "Itens do Kit"
        unique_together = ('kit', 'item')
    
    def __str__(self):
        return f'{self.quantidade} x {self.item.nome} no {self.kit.nome}'

class DoacaoRecebida(models.Model):
    """
    Registra um evento de doação, incluindo quem doou e quando.
    Usa um GenericForeignKey para que o doador possa ser qualquer modelo (PessoaFisica, Entidade).
    """
    data_doacao = models.DateField(verbose_name="Data da Doação")
    
    # Campos para o GenericForeignKey
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    doador = GenericForeignKey('content_type', 'object_id')

    observacoes = models.TextField(blank=True, verbose_name="Observações")
    data_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Doação Recebida"
        verbose_name_plural = "Doações Recebidas"

    def __str__(self):
        return f"Doação de {self.doador} em {self.data_doacao.strftime('%d/%m/%Y')}"


class ItemDoacaoRecebida(models.Model):
    """
    Registra um item específico dentro de uma Doação Recebida.
    Este é o modelo que efetivamente adiciona ao estoque.
    """
    doacao = models.ForeignKey(DoacaoRecebida, on_delete=models.CASCADE, related_name='itens_doados')
    item = models.ForeignKey(Item, on_delete=models.PROTECT, verbose_name="Item")
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        # ANTES de salvar o item da doação...
        # Cria a movimentação de estoque correspondente!
        MovimentacaoEstoque.objects.create(
            item=self.item,
            tipo_movimento='E', # 'E' para Entrada
            quantidade=self.quantidade, # Quantidade positiva
            observacao=f"Entrada via doação ID {self.doacao_id if self.doacao_id else 'Nova'}"
        )
        super().save(*args, **kwargs) # ... AGORA salva o item da doação.
    
    class Meta:
        verbose_name = "Item de Doação Recebida"
        verbose_name_plural = "Itens de Doações Recebidas"
        
class MovimentacaoEstoque(models.Model):
    class Tipo(models.TextChoices):
        ENTRADA = 'E', 'Entrada'
        SAIDA = 'S', 'Saída'

    item = models.ForeignKey(
        Item, 
        on_delete=models.PROTECT, 
        verbose_name="Item",
        related_name='movimentacoes'
        )
    tipo_movimento = models.CharField(max_length=1, choices=Tipo.choices, verbose_name="Tipo de Movimento")
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    data_movimento = models.DateTimeField(auto_now_add=True, verbose_name="Data do Movimento")
    usuario_responsavel = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, # Não deletar a movimentação se o usuário for removido
        null=True, 
        blank=True,
        verbose_name="Usuário Responsável"
    )
    observacao = models.TextField(blank=True, verbose_name="Observação")
    
    class Meta:
        verbose_name = "Movimentação de Estoque"
        verbose_name_plural = "Movimentações de Estoque"
        ordering = ['-data_movimento'] # Ordena as movimentações da mais recente para a mais antiga

    def __str__(self):
        return f'{self.get_tipo_movimento_display()} de {self.quantidade} {self.item.unidade_medida}(s) de {self.item.nome}'

class DoacaoRealizada(models.Model):
    """ Registra um evento de saída de doação para um beneficiário. """
    data_saida = models.DateField(verbose_name="Data da Saída")
    
    entidade_gestora = models.ForeignKey(
        Entidade,
        on_delete=models.PROTECT,
        related_name='doacoes_distribuidas',
        limit_choices_to={'eh_gestor': True},
        null=True
    )

    observacoes = models.TextField(blank=True, verbose_name="Observações")
    data_registro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        nome = (
            getattr(self.entidade_gestora, "nome_fantasia", None)
            or getattr(self.entidade_gestora, "razao_social", None)
            or "Entidade gestora"
        )
        return f"Saída para {nome} em {self.data_saida.strftime('%d/%m/%Y')}"

class ItemSaida(models.Model):
    """ Item avulso que saiu em uma doação. """
    doacao_realizada = models.ForeignKey(DoacaoRealizada, related_name="itens_saida", on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)

class KitSaida(models.Model):
    """ Kit que saiu em uma doação. """
    doacao_realizada = models.ForeignKey(DoacaoRealizada, related_name="kits_saida", on_delete=models.CASCADE)
    kit = models.ForeignKey(Kit, on_delete=models.PROTECT)
    quantidade = models.PositiveIntegerField()