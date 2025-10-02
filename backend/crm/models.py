# crm/models.py
from django.db import models

# Modelo para classificar as entidades (Associações, Igrejas, etc.)
class CategoriaEntidade(models.Model):
    nome = models.CharField(max_length=150, unique=True, verbose_name="Nome da Categoria")

    class Meta:
        verbose_name = "Categoria de Entidade"
        verbose_name_plural = "Categorias de Entidades"

    def __str__(self):
        return self.nome

# Modelo principal para as entidades (organizações)
class Entidade(models.Model):
    razao_social = models.CharField(max_length=255)
    nome_fantasia = models.CharField(max_length=255, blank=True)
    cnpj = models.CharField(max_length=18, unique=True)
    categoria = models.ForeignKey(
        CategoriaEntidade, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Categoria"
    )
    logradouro = models.CharField(max_length=255, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cep = models.CharField(max_length=9, blank=True)
    data_cadastro = models.DateField(null=True, blank=True, verbose_name="Data de Cadastro Original")
    vigencia_de = models.DateField(null=True, blank=True, verbose_name="Vigência De")
    vigencia_ate = models.DateField(null=True, blank=True, verbose_name="Vigência Até")
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    eh_doador = models.BooleanField(default=False, verbose_name="É Doador?")
    eh_gestor = models.BooleanField(default=False, verbose_name="É Gestor/Recebedor?")
    
    class Meta:
        verbose_name = "Entidade"
        verbose_name_plural = "Entidades"

    def __str__(self):
        return self.nome_fantasia or self.razao_social

# Modelo para armazenar múltiplos contatos (telefone/email) para cada entidade
class Contato(models.Model):
    class Tipo(models.TextChoices):
        TELEFONE = 'T', 'Telefone'
        EMAIL = 'E', 'Email'
    
    entidade = models.ForeignKey(Entidade, on_delete=models.CASCADE, related_name='contatos')
    tipo_contato = models.CharField(max_length=1, choices=Tipo.choices, verbose_name="Tipo de Contato")
    valor = models.CharField(max_length=255, verbose_name="Contato")
    descricao = models.CharField(max_length=100, blank=True, verbose_name="Descrição")

    class Meta:
        verbose_name = "Contato"
        verbose_name_plural = "Contatos"

    def __str__(self):
        return f'{self.get_tipo_contato_display()}: {self.valor} ({self.entidade.nome_fantasia})'

# Modelo central para qualquer pessoa física (responsáveis, beneficiários, etc.)
class PessoaFisica(models.Model):
    nome_completo = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    # Adicione aqui campos de endereço da pessoa se desejar
    
    class Meta:
        verbose_name = "Pessoa Física"
        verbose_name_plural = "Pessoas Físicas"

    def __str__(self):
        return self.nome_completo

# Tabela de ligação para definir quem é responsável pelo quê em uma entidade
class Responsavel(models.Model):
    entidade = models.ForeignKey(Entidade, on_delete=models.CASCADE, related_name='responsaveis')
    pessoa_fisica = models.ForeignKey(PessoaFisica, on_delete=models.CASCADE, verbose_name="Pessoa")
    cargo = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Responsável"
        verbose_name_plural = "Responsáveis"
        unique_together = ('entidade', 'pessoa_fisica', 'cargo') # Evita duplicatas

    def __str__(self):
        return f'{self.pessoa_fisica.nome_completo} - {self.cargo} de {self.entidade.nome_fantasia}'

# Tabela de ligação para registrar os beneficiários de cada entidade
class Beneficiario(models.Model):
    entidade_intermediaria = models.ForeignKey(
        Entidade, 
        on_delete=models.PROTECT, # Impede deletar uma entidade que ainda tem beneficiários
        related_name='beneficiarios',
        verbose_name="Entidade Intermediária"
    )
    pessoa_fisica = models.ForeignKey(PessoaFisica, on_delete=models.CASCADE, verbose_name="Pessoa")
    data_vinculo = models.DateField(auto_now_add=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Beneficiário"
        verbose_name_plural = "Beneficiários"
        unique_together = ('entidade_intermediaria', 'pessoa_fisica')

    def __str__(self):
        return f'Beneficiário: {self.pessoa_fisica.nome_completo}'