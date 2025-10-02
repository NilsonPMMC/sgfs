# crm/serializers.py
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from .models import Entidade, Contato, CategoriaEntidade, PessoaFisica, Responsavel, Beneficiario

class ContatoWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contato
        fields = ['id', 'entidade', 'tipo_contato', 'valor', 'descricao']

class PessoaFisicaSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo PessoaFisica.
    """
    class Meta:
        model = PessoaFisica
        fields = ['id', 'nome_completo', 'cpf', 'data_nascimento', 'email', 'telefone']


class ResponsavelSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Responsavel.
    Ele aninha os dados completos da PessoaFisica relacionada.
    """
    pessoa_fisica = PessoaFisicaSerializer(read_only=True)
    
    class Meta:
        model = Responsavel
        fields = ['id', 'cargo', 'pessoa_fisica']


class BeneficiarioSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Beneficiario.
    Também aninha os dados completos da PessoaFisica.
    """
    pessoa_fisica = PessoaFisicaSerializer(read_only=True)

    class Meta:
        model = Beneficiario
        fields = ['id', 'data_vinculo', 'ativo', 'pessoa_fisica']

class ResponsavelWriteSerializer(serializers.ModelSerializer):
    """ Serializer para criar/atualizar um vínculo de Responsável. """
    class Meta:
        model = Responsavel
        fields = ['id', 'entidade', 'pessoa_fisica', 'cargo']

class BeneficiarioWriteSerializer(serializers.ModelSerializer):
    """ Serializer para criar/atualizar um vínculo de Beneficiário. """
    class Meta:
        model = Beneficiario
        fields = ['id', 'entidade_intermediaria', 'pessoa_fisica', 'ativo']

class CategoriaEntidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaEntidade
        fields = ['id', 'nome']


class ContatoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contato
        fields = ['id', 'tipo_contato', 'valor', 'descricao']


class EntidadeSerializer(serializers.ModelSerializer):
    categoria = CategoriaEntidadeSerializer(read_only=True)
    contatos = ContatoSerializer(many=True, read_only=True)
    responsaveis = ResponsavelSerializer(many=True, read_only=True)
    beneficiarios = BeneficiarioSerializer(many=True, read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(
        queryset=CategoriaEntidade.objects.all(), source='categoria', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Entidade
        fields = [
            'id', 
            'razao_social', 
            'nome_fantasia', 
            'cnpj', 
            'logradouro',
            'numero',
            'bairro',
            'cep',
            'data_cadastro', 
            'vigencia_de',
            'vigencia_ate', 
            'observacoes',
            'categoria',
            'categoria_id',
            'contatos',
            'responsaveis',
            'beneficiarios',
            'eh_doador',
            'eh_gestor'
        ]

class UserSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'permissions']

    def get_permissions(self, obj):
        return obj.get_all_permissions()