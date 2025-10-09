<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
// 1. IMPORTAMOS A NOSSA INSTÂNCIA 'api'
import api from '@/services/api';
import ReportLayout from '@/views/reports/ReportLayout.vue';
import Divider from 'primevue/divider';

const route = useRoute();
// 2. REMOVEMOS A URL FIXA
// const API = 'http://127.0.0.1:8005/api/';

const ent = ref(null);
const entradas = ref([]);
const saidas = ref([]);
const loading = ref(true);

const fmt = (dmy) => {
    if (!dmy) return '';
    const [y, m, d] = dmy.split('-');
    return `${d}/${m}/${y}`;
};

const fetchAll = async () => {
    loading.value = true;
    const id = route.params.id;

    try {
        // 3. USAMOS 'api.get' COM CAMINHOS RELATIVOS
        // entidade
        const e = await api.get(`/entidades/${id}/`);
        ent.value = e.data;

        // doações realizadas para essa entidade (saídas)
        const sr = await api.get(`/doacoes-realizadas/?entidade_gestora=${id}`);
        saidas.value = sr.data?.results ?? sr.data ?? [];

    } catch (error) {
        console.error("Erro ao buscar dados do relatório:", error);
    } finally {
        loading.value = false;
    }
};

const printNow = () => window.print();

onMounted(fetchAll);
</script>

<template>
  <ReportLayout
    :title="`Relatório — Entidade`"
    :subtitle="entidade ? (entidade.nome_fantasia || entidade.razao_social || entidade.nome) : ''"
  >

    <div v-if="loading">Carregando…</div>
    <div v-else>
      <h4 class="mt-0">{{ ent?.nome_fantasia || ent?.razao_social || ent?.nome }}</h4>
      <p class="m-0 text-500">Documento: {{ ent?.documento || '-' }}</p>
      <p class="m-0 text-500">Endereço: {{ ent?.logradouro }} {{ ent?.numero }}, {{ ent?.bairro }} — CEP {{ ent?.cep }}</p>

      <Divider />
      <h5 class="mt-0">Saídas para esta entidade</h5>
      <table class="w-full">
        <thead>
          <tr>
            <th class="text-left p-2 border">Data</th>
            <th class="text-left p-2 border">Observações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in saidas" :key="s.id">
            <td class="p-2 border">{{ s.data_saida }}</td>
            <td class="p-2 border">{{ s.observacoes || '-' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </ReportLayout>
</template>

<style>
@media print{
  .no-print{ display:none !important; }
  .card{ box-shadow:none !important; }
}
</style>
