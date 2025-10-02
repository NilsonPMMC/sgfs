# Dentro do novo arquivo crm/migrations/000X_migrar_enderecos.py

from django.db import migrations
import re

def desmembrar_enderecos(apps, schema_editor):
    Entidade = apps.get_model('crm', 'Entidade')
    for entidade in Entidade.objects.all():
        if not entidade.endereco_antigo:
            continue

        endereco_str = entidade.endereco_antigo
        
        # Tenta extrair o CEP primeiro
        cep_match = re.search(r'CEP\s*([\d-]+)', endereco_str, re.IGNORECASE)
        if cep_match:
            entidade.cep = cep_match.group(1).strip()
            # Remove a parte do CEP do resto do endereço para facilitar
            endereco_str = endereco_str[:cep_match.start()].strip()

        partes = [p.strip() for p in endereco_str.split(',')]
        
        if len(partes) > 0:
            entidade.logradouro = partes[0]
        
        if len(partes) > 1:
            # Tenta separar número e bairro
            resto = partes[1]
            num_match = re.search(r'([\d\w]+)\s*-\s*(.*)', resto)
            if num_match:
                entidade.numero = num_match.group(1)
                entidade.bairro = num_match.group(2)
            else:
                # Se não encontrar o padrão "numero - bairro", assume que é só o bairro
                entidade.bairro = resto

        entidade.save(update_fields=['logradouro', 'numero', 'bairro', 'cep'])


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0005_remove_entidade_endereco_entidade_bairro_and_more'),  # Troque pelo nome da migração anterior
    ]

    operations = [
        migrations.RunPython(desmembrar_enderecos),
    ]