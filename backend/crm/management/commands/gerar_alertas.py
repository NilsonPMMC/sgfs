# backend/crm/management/commands/gerar_alertas.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from crm.models import Entidade, Alerta
from estoque.models import DoacaoRealizada

class Command(BaseCommand):
    help = 'Executa as rotinas para gerar alertas de pendências e vigências.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando a geração de alertas...'))
        
        criados_pendentes = self.gerar_alertas_pendentes()
        criados_vigencia = self.gerar_alertas_vigencia()
        
        self.stdout.write(self.style.SUCCESS(
            f'Processo finalizado. Alertas gerados: {criados_pendentes + criados_vigencia}'
        ))

    def gerar_alertas_pendentes(self):
        """ Lógica da action 'gerar_pendentes' com a correção """
        self.stdout.write('Verificando entidades sem atendimento...')
        hoje = timezone.now().date()
        limite = hoje - timedelta(days=60)
        gestoras = Entidade.objects.filter(eh_gestor=True)
        criados = 0

        for g in gestoras:
            # --- LINHA CORRIGIDA ---
            # Adicionado .order_by('-data_saida') para garantir que pegamos a data mais recente.
            ultima_saida = (DoacaoRealizada.objects
                            .filter(entidade_gestora=g)
                            .order_by('-data_saida')
                            .values_list('data_saida', flat=True)
                            .first())

            if (not ultima_saida) or (ultima_saida <= limite):
                titulo = 'Entidade sem atendimento há 60+ dias'
                if not Alerta.objects.filter(entidade=g, titulo=titulo, lido=False).exists():
                    Alerta.objects.create(
                        titulo=titulo,
                        mensagem=f'A entidade {g.nome_fantasia or g.razao_social} está sem atendimento desde {ultima_saida.strftime("%d/%m/%Y") if ultima_saida else "sempre"}.',
                        entidade=g,
                        severity='warn'
                    )
                    criados += 1
        
        self.stdout.write(f' -> {criados} alertas de pendência gerados.')
        return criados

    def gerar_alertas_vigencia(self):
        """ Lógica da action 'gerar_alertas_vigencia' """
        self.stdout.write('Verificando vigências de entidades...')
        hoje = timezone.now().date()
        limite_vencimento = hoje + timedelta(days=30)
        criados = 0

        # Vigências vencidas
        entidades_vencidas = Entidade.objects.filter(vigencia_ate__lt=hoje)
        for entidade in entidades_vencidas:
            titulo = 'Vigência de atendimento vencida'
            if not Alerta.objects.filter(entidade=entidade, titulo=titulo, lido=False).exists():
                Alerta.objects.create(
                    titulo=titulo,
                    mensagem=f'A vigência da entidade {entidade.nome_fantasia or entidade.razao_social} venceu em {entidade.vigencia_ate.strftime("%d/%m/%Y")}.',
                    entidade=entidade,
                    severity='danger'
                )
                criados += 1

        # Vigências próximas do vencimento
        entidades_proximas = Entidade.objects.filter(vigencia_ate__gte=hoje, vigencia_ate__lte=limite_vencimento)
        for entidade in entidades_proximas:
            titulo = 'Vigência próxima do vencimento'
            if not Alerta.objects.filter(entidade=entidade, titulo=titulo, lido=False).exists():
                dias_restantes = (entidade.vigencia_ate - hoje).days
                Alerta.objects.create(
                    titulo=titulo,
                    mensagem=f'A vigência da entidade {entidade.nome_fantasia or entidade.razao_social} vencerá em {dias_restantes} dias ({entidade.vigencia_ate.strftime("%d/%m/%Y")}).',
                    entidade=entidade,
                    severity='warn'
                )
                criados += 1
        
        self.stdout.write(f' -> {criados} alertas de vigência gerados.')
        return criados