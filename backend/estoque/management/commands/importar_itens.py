# estoque/management/commands/importar_itens.py
import pandas as pd
from django.core.management.base import BaseCommand
from estoque.models import Item, CategoriaDeItens

class Command(BaseCommand):
    help = 'Importa itens de um arquivo CSV.'

    def add_arguments(self, parser):
        parser.add_argument('caminho_csv', type=str, help='O caminho para o arquivo .csv')

    def handle(self, *args, **options):
        caminho_csv = options['caminho_csv']
        self.stdout.write(self.style.SUCCESS(f'Iniciando importação do arquivo "{caminho_csv}"...'))

        df = pd.read_csv(caminho_csv)

        for index, row in df.iterrows():
            nome_categoria = row['categoria']
            categoria_obj = None

            # Encontra ou cria a categoria
            if pd.notna(nome_categoria):
                categoria_obj, created = CategoriaDeItens.objects.get_or_create(
                    nome=nome_categoria.strip()
                )
                if created:
                    self.stdout.write(f'  -> Categoria criada: "{categoria_obj.nome}"')
            
            # Cria ou atualiza o item
            item_obj, created = Item.objects.update_or_create(
                nome=row['item'].strip(),
                defaults={
                    'descricao': row['descrição'],
                    'unidade_medida': row['unidade de medida'],
                    'categoria': categoria_obj
                }
            )

            acao = "Criado" if created else "Atualizado"
            self.stdout.write(f'Item: "{item_obj.nome}" - {acao}')

        self.stdout.write(self.style.SUCCESS('Importação de itens concluída!'))