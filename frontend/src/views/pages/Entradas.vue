<script setup>
import api from '@/services/api';
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import { FilterMatchMode } from '@primevue/core/api';
import DatePicker from 'primevue/datepicker';

const router = useRouter();
const toast = useToast();
const dt = ref();
const entradas = ref([]);
const loading = ref(true);
const deleteEntradaDialog = ref(false);
const entradaSelecionada = ref(null);
const filters = ref({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS }
});

const dataInicioFiltro = ref(null);
const dataFimFiltro = ref(null);

const formatDateToAPI = (date) => {
    if (!date) return null;
    const d = date instanceof Date ? date : new Date(date);
    if (isNaN(d.getTime())) return null;
    return d.toISOString().split('T')[0];
};

const entradasFiltradas = computed(() => {
    console.log("[DEBUG] Recalculando entradasFiltradas...");
    let dadosFiltrados = [...entradas.value];
    console.log(`[DEBUG] Total inicial: ${dadosFiltrados.length}`);

    // Filtro global (mantido)
    const termoBusca = filters.value.global.value?.trim().toLowerCase();
    if (termoBusca) {
        dadosFiltrados = dadosFiltrados.filter(entrada => {
            const doador = entrada?.doador_nome || `#${entrada?.object_id}` || '';
            const obs = entrada.observacoes || '';
            const data = entrada.data_doacao || ''; // A busca global pode continuar com a string original
            return doador.toLowerCase().includes(termoBusca) ||
                   obs.toLowerCase().includes(termoBusca) ||
                   data.toLowerCase().includes(termoBusca);
        });
        console.log(`[DEBUG] Após filtro global ('${termoBusca}'): ${dadosFiltrados.length}`);
    }

    // Função auxiliar interna para parsear DD/MM/YYYY ou YYYY-MM-DD
    const parseDataEntrada = (dataString) => {
        if (!dataString || typeof dataString !== 'string') return null;
        const dataOnlyString = dataString.split('T')[0]; // Remove hora se houver
        let parts, year, monthIndex, day;

        if (dataOnlyString.includes('/')) { // Formato DD/MM/YYYY
            parts = dataOnlyString.split('/');
            if (parts.length === 3) {
                day = parseInt(parts[0], 10);
                monthIndex = parseInt(parts[1], 10) - 1;
                year = parseInt(parts[2], 10);
            }
        } else if (dataOnlyString.includes('-')) { // Formato YYYY-MM-DD
             parts = dataOnlyString.split('-');
            if (parts.length === 3) {
                year = parseInt(parts[0], 10);
                monthIndex = parseInt(parts[1], 10) - 1;
                day = parseInt(parts[2], 10);
            }
        } else {
             console.warn(`[DEBUG] Formato data_doacao não reconhecido: ${dataString}`);
             return null; // Não reconhece o formato
        }

        if (!isNaN(year) && !isNaN(monthIndex) && !isNaN(day)) {
             if (year < 100) year += 2000; // Ajusta ano curto
             const dataObj = new Date(year, monthIndex, day);
             if (!isNaN(dataObj.getTime())) { // Verifica se a data criada é válida
                 dataObj.setHours(0, 0, 0, 0); // Zera hora para comparação
                 return dataObj;
             }
        }
        console.warn(`[DEBUG] Parsing de data_doacao resultou em inválido: ${dataString}`);
        return null; // Falha no parsing ou data inválida
    };

    // Filtro de Data Início
    const dataInicioObj = dataInicioFiltro.value instanceof Date ? dataInicioFiltro.value : null;
    if (dataInicioObj && !isNaN(dataInicioObj.getTime())) {
        const dataInicioComparacao = new Date(dataInicioObj);
        dataInicioComparacao.setHours(0, 0, 0, 0);
        console.log("[DEBUG] Data Início para Comparação:", dataInicioComparacao);

        dadosFiltrados = dadosFiltrados.filter(entrada => {
            const dataEntrada = parseDataEntrada(entrada.data_doacao); // Usa a nova função de parse
            return dataEntrada && dataEntrada >= dataInicioComparacao; // Compara se dataEntrada é válida
        });
        console.log(`[DEBUG] Após filtro Data Início: ${dadosFiltrados.length} registros`);
    }

    // Filtro de Data Fim
    const dataFimObj = dataFimFiltro.value instanceof Date ? dataFimFiltro.value : null;
     if (dataFimObj && !isNaN(dataFimObj.getTime())) {
        const dataFimComparacao = new Date(dataFimObj);
        dataFimComparacao.setHours(23, 59, 59, 999);
         console.log("[DEBUG] Data Fim para Comparação:", dataFimComparacao);

        dadosFiltrados = dadosFiltrados.filter(entrada => {
             const dataEntrada = parseDataEntrada(entrada.data_doacao); // Usa a nova função de parse
            return dataEntrada && dataEntrada <= dataFimComparacao; // Compara se dataEntrada é válida
        });
        console.log(`[DEBUG] Após filtro Data Fim: ${dadosFiltrados.length} registros`);
    }

    console.log(`[DEBUG] Retornando ${dadosFiltrados.length} registros filtrados.`);
    return dadosFiltrados;
});

const exportCSV = () => dt.value.exportCSV();

const fetchData = async () => {
    loading.value = true;
    let all = [];
    let nextUrl = '/doacoes-recebidas/';
    try {
        while (nextUrl) {
            const r = await api.get(nextUrl);
            const page = Array.isArray(r.data?.results) ? r.data.results : r.data;
            all = all.concat(page);
            nextUrl = r.data?.next || null;
        }
        entradas.value = all;
    } catch (e) {
        console.error(e);
        toast.add({ severity: 'error', summary: 'Erro', detail: 'Falha ao carregar entradas.', life: 3000 });
    } finally {
        loading.value = false;
    }
};

const confirmDeleteEntrada = (entrada) => {
    entradaSelecionada.value = entrada;
    deleteEntradaDialog.value = true;
};

// --- FUNÇÕES AUXILIARES (sem alteração) ---
const getDoadorLabel = (e) =>
    e?.doador_nome || e?.doador?.nome || e?.object_name || 'doador';

const getPrimeiroItemLabel = (e) => {
    const arr = Array.isArray(e?.itens_doados) ? e.itens_doados : [];
    const it = arr[0] || null;
    const nome = it?.item?.nome || it?.item_nome || null;
    const qtd = it?.quantidade;
    return nome ? `${qtd} x ${nome}` : '';
};

const deleteEntrada = async () => {
    if (!entradaSelecionada.value) return;

    try {
        // 4. USAMOS 'api.delete' COM CAMINHO RELATIVO
        await api.delete(`/doacoes-recebidas/${entradaSelecionada.value.id}/`);
        toast.add({
            severity: 'success',
            summary: 'Excluído',
            detail: 'Entrada removida e estoque revertido.',
            life: 3000
        });
        deleteEntradaDialog.value = false;
        await fetchData();
    } catch (err) {
        console.error('Erro ao excluir:', err?.response?.data || err);
        toast.add({
            severity: 'error',
            summary: 'Erro',
            detail: 'Não foi possível excluir a entrada.',
            life: 4000
        });
    }
};

onMounted(fetchData);

const editar = (row) => {
    // Esta navegação pode ser melhorada para usar o router do Vue
    router.push({ name: 'EditarEntradaDoacao', params: { id: row.id } });
};

const abrirRelatorioEntradas = () => {
    const queryParams = {};
    const dataInicioFormatada = formatDateToAPI(dataInicioFiltro.value);
    const dataFimFormatada = formatDateToAPI(dataFimFiltro.value);

    if (dataInicioFormatada) queryParams.data_inicio = dataInicioFormatada;
    if (dataFimFormatada) queryParams.data_fim = dataFimFormatada;

    const nomeDaRotaRelatorio = 'RelatorioEntradas';

    // Log para depurar o botão relatório
    console.log("[DEBUG] Tentando abrir relatório. Rota:", nomeDaRotaRelatorio, "Query:", queryParams); // Log 13: Antes de resolver

    try {
        const routeData = router.resolve({
            name: nomeDaRotaRelatorio,
            query: queryParams
        });
        console.log("[DEBUG] Rota resolvida com sucesso:", routeData); // Log 14: Sucesso ao resolver
        window.open(routeData.href, '_blank');
    } catch (error) {
        console.error(`[DEBUG] Erro ao resolver a rota '${nomeDaRotaRelatorio}':`, error); // Log 15: Erro ao resolver
        toast.add({ severity: 'error', summary: 'Erro de Rota', detail: `A rota '${nomeDaRotaRelatorio}' não foi encontrada. Verifique o console (F12) e o arquivo src/router/index.js.`, life: 6000 });
    }
};

const abrirEmNovaAba = (name, params) => {
    const { href } = router.resolve({ name, params });
    window.open(href, '_blank');
};
</script>

<template>
  <div class="card">
    <Toast />
    <Toolbar class="mb-4">
      <template #start>
        <Button label="Nova Entrada" icon="pi pi-plus" class="p-button-success" @click="$router.push({ name: 'EntradaDoacao' })" />
      </template>
      <template #end>
        <Button
            label="Relatório"
            icon="pi pi-print"
            class="p-button-secondary mr-2"
            @click="abrirRelatorioEntradas"
        />
        <Button label="Exportar CSV" icon="pi pi-upload" class="p-button-help" @click="exportCSV" />
      </template>
    </Toolbar>

    <DataTable
      ref="dt"
      :value="entradasFiltradas"
      dataKey="id"
      :paginator="true"
      :rows="10"
      v-model:filters="filters"
      :globalFilterFields="['doador_nome','observacoes','data_doacao']"
      paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
      :rowsPerPageOptions="[5,10,25]"
      currentPageReportTemplate="Mostrando {first} a {last} de {totalRecords} entradas"
      :loading="loading"
    >
      <template #header>
        <div class="flex flex-col gap-4">
            <div class="flex flex-wrap gap-2 items-center justify-between">
              <h4 class="m-0">Entradas de Doações</h4>
              <IconField>
                <InputIcon>
                  <i class="pi pi-search" />
                </InputIcon>
                <InputText v-model="filters['global'].value" placeholder="Buscar (doador, obs, data)..." />
              </IconField>
            </div>

            <div class="flex flex-wrap gap-3 items-end">
               <div>
                  <label for="dataInicio" class="block text-sm font-medium mb-1">Data Início</label>
                  <DatePicker inputId="dataInicio" v-model="dataInicioFiltro" dateFormat="dd/mm/yy" placeholder="DD/MM/AAAA" showIcon fluid />
               </div>
               <div>
                  <label for="dataFim" class="block text-sm font-medium mb-1">Data Fim</label>
                  <DatePicker inputId="dataFim" v-model="dataFimFiltro" dateFormat="dd/mm/yy" placeholder="DD/MM/AAAA" showIcon fluid />
               </div>
               <Button icon="pi pi-filter-slash" outlined severity="secondary" @click="() => { dataInicioFiltro = null; dataFimFiltro = null; filters.global.value = null; }" />
            </div>
        </div>
     </template>

      <template #empty>Nenhuma entrada encontrada.</template>

      <Column field="data_doacao" header="Data" sortable></Column>

      <Column header="Doador" sortable>
        <template #body="{ data }">
          {{ data?.doador_nome || `#${data?.object_id}` }}
        </template>
      </Column>

      <Column field="observacoes" header="Observações"></Column>

      <Column :exportable="false" header="Ações" style="width: 15rem">
        <template #body="{ data }">
          <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editar(data)" />
          <Button
            icon="pi pi-print"
            outlined
            rounded
            class="mr-2"
            :disabled="!data?.id"
            @click="abrirEmNovaAba('RelatorioEntrada', { id: data.id })"
          />
          <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmDeleteEntrada(data)" />
        </template>
      </Column>
    </DataTable>

    <Dialog
      v-model:visible="deleteEntradaDialog"
      :style="{ width: '450px' }"
      header="Confirmar Exclusão"
      :modal="true"
    >
      <div class="flex align-items-center">
        <i class="pi pi-exclamation-triangle mr-3" style="font-size: 2rem" />
        <span v-if="entradaSelecionada">
          Tem certeza que deseja excluir a entrada
          <b>#{{ entradaSelecionada.id }}</b>
          do doador
          <b>{{ getDoadorLabel(entradaSelecionada) }}</b>?
        </span>
      </div>
      <template #footer>
        <Button label="Não" icon="pi pi-times" text @click="deleteEntradaDialog = false" />
        <Button label="Sim, Excluir" icon="pi pi-check" class="p-button-danger" @click="deleteEntrada" />
      </template>
    </Dialog>
  </div>
</template>
