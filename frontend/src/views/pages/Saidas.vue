<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useToast } from 'primevue/usetoast';
import { FilterMatchMode } from '@primevue/core/api';

const toast = useToast();
const API_BASE_URL = 'http://127.0.0.1:8005/api/';

const dt = ref();
const saidas = ref([]);
const loading = ref(true);

// Dialog de exclusão
const deleteSaidaDialog = ref(false);
const saidaSelecionada = ref(null);

const filters = ref({
  global: { value: null, matchMode: FilterMatchMode.CONTAINS }
});

const exportCSV = () => dt.value.exportCSV();

const fetchData = async () => {
  loading.value = true;
  let all = [];
  let nextUrl = `${API_BASE_URL}doacoes-realizadas/`;
  try {
    while (nextUrl) {
      const r = await axios.get(nextUrl);
      const page = Array.isArray(r.data?.results) ? r.data.results : r.data;
      all = all.concat(page);
      nextUrl = r.data?.next || null;
    }
    saidas.value = all;
  } catch (e) {
    console.error(e);
    toast.add({ severity: 'error', summary: 'Erro', detail: 'Falha ao carregar saídas.', life: 3000 });
  } finally {
    loading.value = false;
  }
};

onMounted(fetchData);

// Label amigável da entidade gestora
const getEntidadeGestoraLabel = (row) =>
  row?.entidade_gestora_nome ||
  row?.entidade_gestora_obj?.nome_fantasia ||
  row?.entidade_gestora_obj?.razao_social ||
  (row?.entidade_gestora ? `#${row.entidade_gestora}` : '—');

// Abrir/fechar dialog
const confirmarExclusao = (row) => {
  saidaSelecionada.value = row;
  deleteSaidaDialog.value = true;
};

const cancelarExclusao = () => {
  deleteSaidaDialog.value = false;
  saidaSelecionada.value = null;
};

// Excluir (endpoint corrigido)
const excluirSaida = async () => {
  if (!saidaSelecionada.value?.id) return;
  try {
    await axios.delete(`${API_BASE_URL}doacoes-realizadas/${saidaSelecionada.value.id}/`);
    toast.add({
      severity: 'success',
      summary: 'Excluído',
      detail: 'Saída removida e estoque revertido.',
      life: 3000
    });
    deleteSaidaDialog.value = false;
    saidaSelecionada.value = null;
    await fetchData();
  } catch (err) {
    console.error('Erro ao excluir:', err?.response?.data || err);
    toast.add({
      severity: 'error',
      summary: 'Erro',
      detail: 'Não foi possível excluir a saída.',
      life: 4000
    });
  }
};

const editar = (row) => {
  window.location.href = `/doacoes/saida/${row.id}`;
};

const abrirRelatorioSaida = (row) => {
  if (!row?.id) return;
  window.open(`/relatorios/saida/${row.id}`, '_blank');
};
</script>

<template>
  <div class="card">
    <Toast />
    <Toolbar class="mb-4">
      <template #start>
        <Button
          label="Nova Saída"
          icon="pi pi-plus"
          class="p-button-success"
          @click="$router.push({ name: 'SaidaDoacao' })"
        />
      </template>
      <template #end>
        <Button label="Exportar CSV" icon="pi pi-upload" class="p-button-help" @click="exportCSV" />
      </template>
    </Toolbar>

    <DataTable
      ref="dt"
      :value="saidas"
      dataKey="id"
      :paginator="true"
      :rows="10"
      v-model:filters="filters"
      :globalFilterFields="['entidade_gestora_nome','observacoes','data_saida']"
      paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
      :rowsPerPageOptions="[5,10,25]"
      currentPageReportTemplate="Mostrando {first} a {last} de {totalRecords} saídas"
      :loading="loading"
    >
      <template #header>
        <div class="flex flex-wrap gap-2 items-center justify-between">
          <h4 class="m-0">Saídas de Doações</h4>
          <IconField>
            <InputIcon>
              <i class="pi pi-search" />
            </InputIcon>
            <InputText v-model="filters['global'].value" placeholder="Buscar..." />
          </IconField>
        </div>
      </template>

      <template #empty>Nenhuma saída encontrada.</template>

      <Column field="data_saida" header="Data" sortable></Column>

      <Column header="Entidade Gestora" sortable>
        <template #body="slotProps">
          {{ getEntidadeGestoraLabel(slotProps.data) }}
        </template>
      </Column>

      <Column field="observacoes" header="Observações"></Column>

      <Column :exportable="false" header="Ações" style="width: 15rem">
        <template #body="slotProps">
          <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editar(slotProps.data)" />
          <Button icon="pi pi-print" outlined rounded class="mr-2" @click="abrirRelatorioSaida(slotProps.data)" />
          <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmarExclusao(slotProps.data)" />
        </template>
      </Column>
    </DataTable>
  </div>

  <!-- Dialog de confirmação -->
  <Dialog v-model:visible="deleteSaidaDialog" :style="{ width: '450px' }" header="Confirmar Exclusão" :modal="true">
    <div class="flex align-items-center">
      <i class="pi pi-exclamation-triangle mr-3" style="font-size: 2rem" />
      <span v-if="saidaSelecionada">
        Tem certeza que deseja excluir a saída
        <b>#{{ saidaSelecionada.id }}</b>
        para
        <b>{{ getEntidadeGestoraLabel(saidaSelecionada) }}</b>?
      </span>
    </div>
    <template #footer>
      <Button label="Não" icon="pi pi-times" text @click="cancelarExclusao" />
      <Button label="Sim, Excluir" icon="pi pi-check" class="p-button-danger" @click="excluirSaida" />
    </template>
  </Dialog>
</template>
