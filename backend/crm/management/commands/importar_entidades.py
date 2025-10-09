# crm/management/commands/importar_entidades.py
import pandas as pd
import re
from datetime import datetime
from django.core.management.base import BaseCommand
from crm.models import Entidade, Contato, CategoriaEntidade

def limpar_documento(doc):
    if not doc or pd.isna(doc) or str(doc).lower() in ['sem cnpj', 'sem cpf', '']:
        return None
    return re.sub(r'\D', '', str(doc))

def formatar_data_vigencia(data_str):
    if not data_str or pd.isna(data_str):
        return None
    data_str = str(data_str).strip().lower()
    match = re.match(r'(\d{1,2})\s*/\s*(\d{4})', data_str)
    if match:
        mes, ano = match.groups()
        return f"{ano}-{int(mes):02d}-01"
    return None

class Command(BaseCommand):
    help = 'Importa entidades (Associações, Lideranças, etc.) de um arquivo CSV.'

    def add_arguments(self, parser):
        parser.add_argument('caminho_csv', type=str, help='O caminho para o arquivo .csv')
        parser.add_argument('nome_categoria', type=str, help='O nome da categoria para atribuir')

    def handle(self, *args, **options):
        caminho_csv = options['caminho_csv']
        nome_categoria = options['nome_categoria']
        self.stdout.write(self.style.SUCCESS(f'Iniciando a importação do arquivo "{caminho_csv}" para a categoria "{nome_categoria}"...'))

        categoria_obj, cat_created = CategoriaEntidade.objects.get_or_create(nome=nome_categoria)
        if cat_created:
            self.stdout.write(self.style.SUCCESS(f'Categoria "{nome_categoria}" criada.'))

        try:
            df = pd.read_csv(caminho_csv, sep=';')
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Arquivo não encontrado em: {caminho_csv}'))
            return
        
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

        coluna_documento = 'cnpj' if 'cnpj' in df.columns else 'cpf'
        
        # CORREÇÃO: Define uma lista de possíveis nomes para a coluna da entidade
        colunas_nome_entidade = ['associação', 'entidade_religiosa']

        for index, row in df.iterrows():
            documento_limpo = limpar_documento(row.get(coluna_documento))
            
            # CORREÇÃO: Tenta encontrar o nome da entidade em qualquer uma das colunas da lista
            nome_entidade = None
            for nome_coluna in colunas_nome_entidade:
                if nome_coluna in row and pd.notna(row[nome_coluna]):
                    nome_entidade = row[nome_coluna]
                    break
            
            if not nome_entidade:
                self.stdout.write(self.style.WARNING(f'Linha {index+2} ignorada: Nome da entidade não encontrado.'))
                continue

            if not documento_limpo:
                self.stdout.write(self.style.WARNING(f'Linha {index+2} ignorada: "{nome_entidade}" não possui documento válido.'))
                continue

            data_cadastro_obj = None
            if 'data_de_cadastro' in df.columns and pd.notna(row.get('data_de_cadastro')):
                try:
                    data_cadastro_obj = pd.to_datetime(row.get('data_de_cadastro'), dayfirst=True).date()
                except (ValueError, TypeError):
                    self.stdout.write(self.style.WARNING(f"Formato de data de cadastro inválido para o documento {documento_limpo}."))

            entidade_obj, created = Entidade.objects.update_or_create(
                documento=documento_limpo,
                defaults={
                    'razao_social': nome_entidade,
                    'nome_fantasia': nome_entidade,
                    'logradouro': row.get('logradouro'),
                    'numero': row.get('número'),
                    'bairro': row.get('bairro'),
                    'data_cadastro': data_cadastro_obj,
                    'vigencia_de': formatar_data_vigencia(row.get('vigência_de')),
                    'vigencia_ate': formatar_data_vigencia(row.get('vigência_até')),
                    'observacoes': row.get('obs'),
                    'categoria': categoria_obj,
                    'eh_gestor': True,
                }
            )
            
            acao = "Criada" if created else "Atualizada"
            self.stdout.write(f'Entidade: "{entidade_obj.nome_fantasia}" - {acao}')

            if 'telefone' in df.columns and pd.notna(row.get('telefone')):
                telefones_lista = str(row.get('telefone')).split(',')
                for tel in telefones_lista:
                    tel_limpo = tel.strip()
                    if tel_limpo:
                        Contato.objects.get_or_create(entidade=entidade_obj, tipo_contato='T', valor=tel_limpo)
                        self.stdout.write(f'  -> Telefone adicionado: {tel_limpo}')

            if 'emails' in df.columns and pd.notna(row.get('emails')):
                emails_lista = str(row.get('emails')).split(',')
                for email in emails_lista:
                    email_limpo = email.strip()
                    if email_limpo and '@' in email_limpo:
                        Contato.objects.get_or_create(entidade=entidade_obj, tipo_contato='E', valor=email_limpo)
                        self.stdout.write(f'  -> Email adicionado: {email_limpo}')

        self.stdout.write(self.style.SUCCESS('Importação concluída com sucesso!'))