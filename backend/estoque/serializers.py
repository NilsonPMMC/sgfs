# estoque/serializers.py
from rest_framework import serializers
from .models import Item, CategoriaDeItens, DoacaoRecebida, ItemDoacaoRecebida, Kit, ItemKit, DoacaoRealizada, ItemSaida, KitSaida

class CategoriaDeItensSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaDeItens
        fields = ['id', 'nome']

class ItemSerializer(serializers.ModelSerializer):
    categoria = CategoriaDeItensSerializer(read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(
        queryset=CategoriaDeItens.objects.all(), source='categoria', write_only=True, required=False, allow_null=True
    )
    # NOVO CAMPO CALCULADO
    estoque_atual = serializers.FloatField(read_only=True)

    class Meta:
        model = Item
        # Adicione 'estoque_atual' à lista de campos
        fields = ['id', 'nome', 'descricao', 'unidade_medida', 'categoria', 'categoria_id', 'estoque_atual']

class ItemKitSerializer(serializers.ModelSerializer):
    # Para LEITURA, aninha os dados do item para sabermos o nome
    item = ItemSerializer(read_only=True)
    # Para ESCRITA, espera receber apenas o ID do item
    item_id = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all(), source='item', write_only=True)

    class Meta:
        model = ItemKit
        fields = ['id', 'item', 'item_id', 'quantidade']


class KitSerializer(serializers.ModelSerializer):
    # Aninha a lista de ItemKitSerializer
    itens_do_kit = ItemKitSerializer(many=True)
    quantidade_montavel = serializers.IntegerField(read_only=True)

    class Meta:
        model = Kit
        fields = ['id', 'nome', 'descricao', 'itens_do_kit', 'quantidade_montavel']

    def create(self, validated_data):
        itens_data = validated_data.pop('itens_do_kit')
        kit = Kit.objects.create(**validated_data)
        for item_data in itens_data:
            ItemKit.objects.create(kit=kit, **item_data)
        return kit

    def update(self, instance, validated_data):
        itens_data = validated_data.pop('itens_do_kit')
        instance.nome = validated_data.get('nome', instance.nome)
        instance.descricao = validated_data.get('descricao', instance.descricao)
        instance.save()

        # Lógica para atualizar os itens: deleta os antigos e cria os novos.
        # É a abordagem mais simples e robusta.
        ItemKit.objects.filter(kit=instance).delete()
        for item_data in itens_data:
            ItemKit.objects.create(kit=instance, **item_data)

        return instance

class ItemDoacaoRecebidaSerializer(serializers.ModelSerializer):
    # Aninha os detalhes do item
    item = ItemSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all(), source='item', write_only=True)

    class Meta:
        model = ItemDoacaoRecebida
        # Ajusta os campos para leitura e escrita
        fields = ['id', 'item', 'item_id', 'quantidade']

class DoacaoRecebidaSerializer(serializers.ModelSerializer):
    # Campo para receber a lista de itens aninhada
    itens_doados = ItemDoacaoRecebidaSerializer(many=True)

    class Meta:
        model = DoacaoRecebida
        fields = ['id', 'data_doacao', 'observacoes', 'itens_doados', 'content_type', 'object_id']

    def create(self, validated_data):
        # Remove os itens do dicionário principal
        itens_data = validated_data.pop('itens_doados')
        # Cria o objeto DoacaoRecebida
        doacao = DoacaoRecebida.objects.create(**validated_data)
        # Cria cada ItemDoacaoRecebida, vinculando-o à Doacao recém-criada
        for item_data in itens_data:
            ItemDoacaoRecebida.objects.create(doacao=doacao, **item_data)
        return doacao

class ItemSaidaSerializer(serializers.ModelSerializer):
    # Aninha os detalhes do item para sabermos o nome
    item = ItemSerializer(read_only=True)
    class Meta:
        model = ItemSaida
        fields = ['id', 'item', 'quantidade']

class KitSaidaSerializer(serializers.ModelSerializer):
    # Aninha os detalhes do kit
    kit = KitSerializer(read_only=True)
    class Meta:
        model = KitSaida
        fields = ['id', 'kit', 'quantidade']

class DoacaoRealizadaSerializer(serializers.ModelSerializer):
    itens_saida = ItemSaidaSerializer(many=True, required=False)
    kits_saida = KitSaidaSerializer(many=True, required=False)

    class Meta:
        model = DoacaoRealizada
        # CAMPOS SIMPLIFICADOS
        fields = ['id', 'data_saida', 'observacoes', 'entidade_gestora', 'itens_saida', 'kits_saida']