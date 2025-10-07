<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import ReportLayout from '@/views/reports/ReportLayout.vue';
import Divider from 'primevue/divider';

const route = useRoute();
const API = 'http://127.0.0.1:8005/api/';

const ent = ref(null);
const entradas = ref([]);
const saidas = ref([]);
const loading = ref(true);

const fmt = (dmy) => {
  if (!dmy) return '';
  const [y,m,d] = dmy.split('-');
  return `${d}/${m}/${y}`;
};

const fetchAll = async () => {
  loading.value = true;
  const id = route.params.id;

  // entidade
  const e = await axios.get(`${API}entidades/${id}/`);
  ent.value = e.data;

  // histórico (simples): doações recebidas pelo gestor = entradas? (opcional)
  // e doações realizadas para essa entidade (saídas)
  // Ajuste os filtros conforme seu backend expõe (ex.: ?entidade_gestora=id)
  const sr = await axios.get(`${API}doacoes-realizadas/?entidade_gestora=${id}`);
  saidas.value = sr.data?.results ?? sr.data ?? [];

  // Se quiser entradas relacionadas ao gestor (caso a própria entidade seja doadora, adapte)
  // const er = await axios.get(`${API}doacoes-recebidas/?object_id=${id}`);
  // entradas.value = er.data?.results ?? er.data ?? [];

  loading.value = false;
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
