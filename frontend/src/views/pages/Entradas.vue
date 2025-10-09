<script setup>
// 1. IMPORTAMOS A NOSSA INSTÂNCIA 'api'
import api from '@/services/api';
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import { FilterMatchMode } from '@primevue/core/api';

const router = useRouter();
const toast = useToast();

// 2. REMOVEMOS A URL FIXA
// const API_BASE_URL = 'http://127.0.0.1:8005/api/';

const dt = ref();
const entradas = ref([]);
const loading = ref(true);
const deleteEntradaDialog = ref(false);
const entradaSelecionada = ref(null);
const filters = ref({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS }
});

const exportCSV = () => dt.value.exportCSV();

const fetchData = async () => {
    loading.value = true;
    let all = [];
    // 3. A PRIMEIRA CHAMADA É RELATIVA
    let nextUrl = '/doacoes-recebidas/';
    try {
        while (nextUrl) {
            // USAMOS 'api.get'
            const r = await api.get(nextUrl);
            const page = Array.isArray(r.data?.results) ? r.data.results : r.data;
            all = all.concat(page);
            // CORREÇÃO: Usamos a URL completa que a API nos dá para as próximas páginas
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
        <Button label="Exportar CSV" icon="pi pi-upload" class="p-button-help" @click="exportCSV" />
      </template>
    </Toolbar>

    <DataTable
      ref="dt"
      :value="entradas"
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
        <div class="flex flex-wrap gap-2 items-center justify-between">
          <h4 class="m-0">Entradas de Doações</h4>
          <IconField>
            <InputIcon>
              <i class="pi pi-search" />
            </InputIcon>
            <InputText v-model="filters['global'].value" placeholder="Buscar..." />
          </IconField>
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
