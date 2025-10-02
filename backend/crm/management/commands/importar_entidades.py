# crm/management/commands/importar_entidades.py
import pandas as pd
from datetime import datetime
from django.core.management.base import BaseCommand
from crm.models import Entidade, Contato

class Command(BaseCommand):
    help = 'Importa entidades de um arquivo CSV fornecido pelo Fundo Social.'

    def add_arguments(self, parser):
        parser.add_argument('caminho_csv', type=str, help='O caminho para o arquivo .csv')

    def handle(self, *args, **options):
        caminho_csv = options['caminho_csv']
        self.stdout.write(self.style.SUCCESS(f'Iniciando a importação do arquivo "{caminho_csv}"...'))

        # Usamos sep=';' para indicar que o separador é ponto-e-vírgula
        df = pd.read_csv(caminho_csv, sep=',')

        for index, row in df.iterrows():
            cnpj_limpo = row['cnpj/cpf'] # Usaremos o CNPJ como identificador único
            if not cnpj_limpo or pd.isna(cnpj_limpo):
                self.stdout.write(self.style.WARNING(f'Linha {index+2} ignorada: CNPJ/CPF não preenchido.'))
                continue

            # --- Processando Datas ---
            data_cadastro_obj = None
            if pd.notna(row['data de cadastro']):
                try:
                    data_cadastro_obj = datetime.strptime(str(row['data de cadastro']), '%d/%m/%Y').date()
                except ValueError:
                    self.stdout.write(self.style.WARNING(f"Formato de data inválido para CNPJ {cnpj_limpo}. Use DD/MM/YYYY."))

            # --- Criando ou Atualizando a Entidade ---
            entidade_obj, created = Entidade.objects.update_or_create(
                cnpj=cnpj_limpo,
                defaults={
                    'razao_social': row['entidade'],
                    'nome_fantasia': row['entidade'], # Usando o mesmo por padrão
                    'endereco': row['endereço'],
                    'data_cadastro': data_cadastro_obj,
                    'vigencia_documento': row['vigência do documento'],
                    'observacoes': row['obs']
                }
            )
            
            acao = "Criada" if created else "Atualizada"
            self.stdout.write(f'Entidade: "{entidade_obj.nome_fantasia}" - {acao}')

            # --- Processando Telefones (múltiplos valores) ---
            if pd.notna(row['telefones']):
                telefones_lista = str(row['telefones']).split(',')
                for tel in telefones_lista:
                    tel_limpo = tel.strip()
                    if tel_limpo:
                        Contato.objects.get_or_create(
                            entidade=entidade_obj,
                            tipo_contato='T',
                            valor=tel_limpo
                        )
                        self.stdout.write(f'  -> Telefone adicionado: {tel_limpo}')

            # --- Processando Emails (múltiplos valores) ---
            if pd.notna(row['emails']):
                emails_lista = str(row['emails']).split(',')
                for email in emails_lista:
                    email_limpo = email.strip()
                    if email_limpo:
                        Contato.objects.get_or_create(
                            entidade=entidade_obj,
                            tipo_contato='E',
                            valor=email_limpo
                        )
                        self.stdout.write(f'  -> Email adicionado: {email_limpo}')

        self.stdout.write(self.style.SUCCESS('Importação concluída com sucesso!'))