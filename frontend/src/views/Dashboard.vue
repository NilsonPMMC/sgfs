<script setup>
import api from '@/services/api';
import { useAuthStore } from '@/store/auth';
import { ref, onMounted, watch } from 'vue';
import { useLayout } from '@/layout/composables/layout';

const authStore = useAuthStore();
const { isDarkTheme } = useLayout();
const loading = ref(true);
const dashboardData = ref(null);
const alertas = ref([]);
const alertasLoading = ref(true);

// Estado para os dados dos gráficos
const estoquePieData = ref(null);
const rankingEntidadesBarData = ref(null);
const rankingDoadoresBarData = ref(null);
const movimentacoesLineData = ref(null);

// Estado para as opções dos gráficos
const pieOptions = ref(null);
const barOptions = ref(null);
const lineOptions = ref(null);

const formatarDia = (dataString) => {
    if (!dataString) return '';
    const partes = dataString.split('-');
    return partes[2];
};

const setChartData = (data) => {
    const documentStyle = getComputedStyle(document.documentElement);
    const textColor = documentStyle.getPropertyValue('--text-color');
    const textColorSecondary = documentStyle.getPropertyValue('--text-color-secondary');
    const surfaceBorder = documentStyle.getPropertyValue('--surface-border');

    if (data.movimentacoes_mensais) {
        const { labels, entradas, saidas } = data.movimentacoes_mensais;
        movimentacoesLineData.value = {
            labels: labels,
            datasets: [
                {
                    label: 'Entradas (Doações Recebidas)',
                    data: entradas,
                    fill: false,
                    backgroundColor: documentStyle.getPropertyValue('--p-teal-500'),
                    borderColor: documentStyle.getPropertyValue('--p-teal-500'),
                    tension: 0.4
                },
                {
                    label: 'Saídas (Doações Realizadas)',
                    data: saidas,
                    fill: false,
                    backgroundColor: documentStyle.getPropertyValue('--p-purple-500'),
                    borderColor: documentStyle.getPropertyValue('--p-purple-500'),
                    tension: 0.4
                }
            ]
        };
        
        lineOptions.value = {
            plugins: { legend: { labels: { color: textColor } } },
            scales: {
                x: { ticks: { color: textColorSecondary }, grid: { color: surfaceBorder } },
                y: { ticks: { color: textColorSecondary }, grid: { color: surfaceBorder } }
            }
        };
    }

    const { total_itens, itens_zerados, itens_estoque_baixo } = data.indicadores_estoque;
    const itens_ok = total_itens - itens_zerados - itens_estoque_baixo;

    estoquePieData.value = {
        labels: ['Em Estoque', 'Estoque Baixo', 'Zerado'],
        datasets: [{
            data: [itens_ok, itens_estoque_baixo, itens_zerados],
            backgroundColor: [
                documentStyle.getPropertyValue('--p-teal-500'),
                documentStyle.getPropertyValue('--p-purple-500'),
                documentStyle.getPropertyValue('--p-indigo-500')
            ]
        }]
    };

    rankingEntidadesBarData.value = {
        labels: data.ranking_entidades_gestoras.map(e => e.entidade_gestora__nome_fantasia),
        datasets: [{
            label: 'Nº de Recebimentos',
            backgroundColor: documentStyle.getPropertyValue('--p-teal-500'),
            borderColor: documentStyle.getPropertyValue('--p-teal-500'),
            data: data.ranking_entidades_gestoras.map(e => e.total)
        }]
    };
    
    rankingDoadoresBarData.value = {
        labels: data.ranking_doadores.map(d => d.nome_doador),
        datasets: [{
            label: 'Nº de Doações',
            backgroundColor: documentStyle.getPropertyValue('--p-purple-500'),
            borderColor: documentStyle.getPropertyValue('--p-purple-500'),
            data: data.ranking_doadores.map(d => d.total)
        }]
    };

    pieOptions.value = { plugins: { legend: { labels: { color: textColor, usePointStyle: true } } } };
    barOptions.value = {
        plugins: { legend: { display: false } },
        scales: {
            x: { ticks: { color: textColorSecondary }, grid: { display: false, drawBorder: false } },
            y: { ticks: { color: textColorSecondary }, grid: { color: surfaceBorder, drawBorder: false } }
        }
    };
};

const fetchAlertasDashboard = async () => {
  alertasLoading.value = true;
  try {
    // CORRIGIDO: usa 'api.get' com caminho relativo
    const r = await api.get('/alertas/');
    const lista = Array.isArray(r.data?.results) ? r.data.results : (Array.isArray(r.data) ? r.data : []);
    alertas.value = lista.filter(a => !a.lido).slice(0, 5);
  } catch (e) {
    console.error('Erro ao buscar alertas:', e);
    alertas.value = [];
  } finally {
    alertasLoading.value = false;
  }
};

onMounted(() => {
    // CORRIGIDO: usa 'api.get' com caminho relativo
    api.get('/dashboard/')
        .then(response => {
            dashboardData.value = response.data;
            setChartData(response.data); 
        })
        .catch(error => console.error("Erro ao buscar dados do dashboard:", error))
        .finally(() => loading.value = false);

    fetchAlertasDashboard();
});

const formatarDataBR = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    const dd = String(d.getDate()).padStart(2,'0');
    const mm = String(d.getMonth()+1).padStart(2,'0');
    const yyyy = d.getFullYear();
    return `${dd}/${mm}/${yyyy}`;
};


watch(isDarkTheme, () => {
    if (dashboardData.value) {
        setChartData(dashboardData.value);
    }
});
</script>

<template>
    <div v-if="loading" class="text-center">
        <ProgressSpinner />
    </div>
    <div v-else-if="dashboardData" class="grid grid-cols-12 gap-8">

        <div class="col-span-12 xl:col-span-6">
            <div class="card">
                <div class="flex justify-between mb-4">
                    <div>
                        <span class="block text-muted-color font-medium mb-4">Aniversariantes da Semana</span>
                        <div class="text-surface-900 dark:text-surface-0 font-medium text-xl">{{ dashboardData.aniversariantes_semana.length }} Pessoas</div>
                    </div>
                    <div class="flex items-center justify-center bg-purple-100 dark:bg-purple-400/10 rounded-border" style="width: 2.5rem; height: 2.5rem">
                        <i class="pi pi-gift text-purple-500 !text-xl"></i>
                    </div>
                </div>
                <ul v-if="dashboardData.aniversariantes_semana.length > 0" class="p-0 mx-0 mt-0 mb-6 list-none">
                    <li v-for="aniv in dashboardData.aniversariantes_semana" :key="aniv.id" class="flex items-center py-2 border-b border-surface">
                        <div class="w-12 h-12 flex items-center justify-center bg-purple-100 dark:bg-purple-400/10 rounded-full mr-4 shrink-0">
                            <i class="pi pi-user !text-xl text-purple-500"></i>
                        </div>
                        <span class="text-surface-900 dark:text-surface-0 leading-normal">
                            {{ aniv.nome_completo }}<span class="text-purple-500 font-bold ml-3">Dia: {{ formatarDia(aniv.data_nascimento) }}</span>
                        </span>
                    </li>
                </ul>
                <div v-else>
                    <p class="text-500">Nenhum aniversariante na semana.</p>
                </div>
            </div>

            <div class="card mb-0">
                <div class="flex justify-between mb-4">
                    <div>
                        <span class="block text-muted-color font-medium mb-4">Movimentações (Últimos 30 dias)</span>
                        <div class="text-surface-900 dark:text-surface-0 font-medium text-xl">{{ dashboardData.indicadores_doacoes.entradas_30d + dashboardData.indicadores_doacoes.saidas_30d }} Operações</div>
                    </div>
                    <div class="flex items-center justify-center bg-green-100 dark:bg-green-400/10 rounded-border" style="width: 2.5rem; height: 2.5rem">
                        <i class="pi pi-sync text-green-500 !text-xl"></i>
                    </div>
                </div>
                <span class="text-teal-500 font-medium">{{ dashboardData.indicadores_doacoes.entradas_30d }} Entradas </span>
                <span class="text-500">| </span>
                <span class="text-purple-500 font-medium">{{ dashboardData.indicadores_doacoes.saidas_30d }} Saídas</span>
            </div>

            <div class="card">
                <div class="font-semibold text-xl mb-4">Movimentações Mensais ({{ new Date().getFullYear() }})</div>
                <Chart type="line" :data="movimentacoesLineData" :options="lineOptions"></Chart>
            </div>

            <div class="card">
                <div class="font-semibold text-xl mb-4">Top 5 Entidades Gestoras</div>
                <Chart type="bar" :data="rankingEntidadesBarData" :options="barOptions" class="mb-4"></Chart>
                <DataTable :value="dashboardData.ranking_entidades_gestoras" :rows="5" responsiveLayout="scroll">
                    <Column field="entidade_gestora__nome_fantasia" header="Entidade"></Column>
                    <Column field="total" header="Nº de Recebimentos" sortable style="width: 30%"></Column>
                </DataTable>
            </div>
        </div>

        <div class="col-span-12 xl:col-span-6">
            <div class="card">
                <div class="flex justify-between mb-4">
                    <div>
                    <span class="block text-muted-color font-medium mb-4">Notificações</span>
                    <div class="text-surface-900 dark:text-surface-0 font-medium text-xl">
                        {{ alertas.length }} pendente(s)
                    </div>
                    </div>
                    <div class="flex items-center justify-center bg-orange-100 dark:bg-orange-400/10 rounded-border" style="width: 2.5rem; height: 2.5rem">
                    <i class="pi pi-bell text-orange-500 !text-xl"></i>
                    </div>
                </div>

                <div v-if="alertasLoading">
                    <p>Carregando...</p>
                </div>
                <ul v-else-if="alertas.length" class="p-0 mx-0 mt-0 mb-6 list-none">
                    <li v-for="a in alertas" :key="a.id" class="flex items-start py-3 border-b border-surface">
                    <div class="w-10 h-10 flex items-center justify-center bg-orange-100 dark:bg-orange-400/10 rounded-full mr-4 shrink-0">
                        <i class="pi pi-exclamation-triangle text-orange-500"></i>
                    </div>
                    <div class="flex-1">
                        <div class="font-semibold">{{ a.mensagem }}</div>
                        <small class="text-500">Criado em: {{ formatarDataBR(a.criado_em) }}</small>
                    </div>
                    </li>
                </ul>
                <div v-else>
                    <p class="text-500">Nenhuma notificação pendente.</p>
                </div>
            </div>

            <div class="card">
                <div class="flex justify-between mb-4">
                    <div>
                        <span class="block text-muted-color font-medium mb-4">Estoque</span>
                        <div class="text-surface-900 dark:text-surface-0 font-medium text-xl">{{ dashboardData.indicadores_estoque.total_itens }} Itens Cadastrados</div>
                    </div>
                    <div class="flex items-center justify-center bg-blue-100 dark:bg-blue-400/10 rounded-border" style="width: 2.5rem; height: 2.5rem">
                        <i class="pi pi-box text-blue-500 !text-xl"></i>
                    </div>
                </div>
                <span class="text-red-500 font-medium">{{ dashboardData.indicadores_estoque.itens_zerados }} itens zerados </span>
                <span class="text-500">| </span>
                <span class="text-orange-500 font-medium">{{ dashboardData.indicadores_estoque.itens_estoque_baixo }} com estoque baixo</span>
            </div>

            <div class="card flex flex-col items-center">
                <div class="font-semibold text-xl mb-4">Situação do Estoque</div>
                <Chart type="doughnut" :data="estoquePieData" :options="pieOptions"></Chart>
            </div>

            <div class="card">
                <div class="font-semibold text-xl mb-4">Top 5 Doadores</div>
                <Chart type="bar" :data="rankingDoadoresBarData" :options="barOptions" class="mb-4"></Chart>
                <DataTable :value="dashboardData.ranking_doadores" :rows="5" responsiveLayout="scroll">
                    <Column field="nome_doador" header="Doador"></Column>
                    <Column field="total" header="Nº de Doações" sortable style="width: 30%"></Column>
                </DataTable>
            </div>
        </div>

    </div>
</template>

<style module>
.myinput {
    border-radius: 2rem;
    padding: 1rem 2rem;
    border-width: 2px;
}
</style>