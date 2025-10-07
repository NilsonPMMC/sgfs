# estoque/serializers.py
from rest_framework import serializers
from django.db.models import Sum, DecimalField
from django.db.models.functions import Coalesce
from .models import Item, CategoriaDeItens, DoacaoRecebida, ItemDoacaoRecebida, Kit, ItemKit, DoacaoRealizada, ItemSaida, KitSaida, MovimentacaoEstoque
from crm.models import Entidade

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
    data_doacao = serializers.DateField(
        format='%d/%m/%Y',
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        required=True
    )
    itens_doados = ItemDoacaoRecebidaSerializer(many=True)
    doador_nome = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DoacaoRecebida
        fields = [
            'id', 'data_doacao', 'observacoes', 'itens_doados',
            'content_type', 'object_id',
            'doador_nome',
        ]

    def get_doador_nome(self, obj):
        try:
            return str(obj.doador) if obj.doador else None
        except Exception:
            return None

    def create(self, validated_data):
        itens_data = validated_data.pop('itens_doados')
        doacao = DoacaoRecebida.objects.create(**validated_data)
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
    data_saida = serializers.DateField(
        format='%d/%m/%Y',
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        required=True
    )
    itens_saida = ItemSaidaSerializer(many=True, read_only=True)
    kits_saida = KitSaidaSerializer(many=True, read_only=True)
    entidade_gestora_nome = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DoacaoRealizada
        fields = [
            'id', 'data_saida', 'observacoes', 'entidade_gestora',
            'entidade_gestora_nome',  # <= novo
            'itens_saida', 'kits_saida'
        ]

    def get_entidade_gestora_nome(self, obj):
        try:
            eg = obj.entidade_gestora
            if not eg:
                return None
            return eg.nome_fantasia or getattr(eg, 'razao_social', None) or str(eg)
        except Exception:
            return None


class MovimentacaoEstoqueSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.all(), source='item', write_only=True
    )

    class Meta:
        model = MovimentacaoEstoque
        fields = [
            'id', 'item', 'item_id', 'tipo_movimento', 'quantidade',
            'data_movimento', 'usuario_responsavel', 'observacao'
        ]
        read_only_fields = ['data_movimento', 'usuario_responsavel']

    def validate(self, attrs):
        tipo = attrs.get('tipo_movimento') or getattr(self.instance, 'tipo_movimento', None)
        qtd = attrs.get('quantidade') or getattr(self.instance, 'quantidade', None)
        item = attrs.get('item') or getattr(self.instance, 'item', None)

        if qtd is None or item is None or tipo is None:
            return attrs
        if tipo == 'E' and float(qtd) < 0:
            raise serializers.ValidationError("Quantidade deve ser positiva para entradas.")
        if tipo == 'S' and float(qtd) > 0:
            attrs['quantidade'] = -abs(float(qtd))
        if tipo == 'S':
            estoque_atual = Item.objects.filter(pk=item.pk).annotate(
                estoque_atual=Coalesce(Sum('movimentacoes__quantidade'), 0.0, output_field=DecimalField())
            ).values_list('estoque_atual', flat=True).first() or 0
            if float(estoque_atual) + float(attrs['quantidade']) < 0:
                raise serializers.ValidationError(
                    f"Estoque insuficiente: saldo {estoque_atual}, saída solicitada {abs(float(qtd))}."
                )

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['usuario_responsavel'] = request.user
        return super().create(validated_data)