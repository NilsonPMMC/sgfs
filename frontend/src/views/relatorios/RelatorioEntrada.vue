<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import ReportLayout from '@/views/reports/ReportLayout.vue';
import Divider from 'primevue/divider';

const route = useRoute();
const API = 'http://127.0.0.1:8005/api/';
const rec = ref(null);
const loading = ref(true);

const printNow = () => window.print();

onMounted(async () => {
  loading.value = true;
  const id = route.params.id;
  const r = await axios.get(`${API}doacoes-recebidas/${id}/`);
  rec.value = r.data;
  loading.value = false;
});
</script>

<template>
  <ReportLayout
    title="Relatório — Doação (Entrada)"
    :subtitle="registro ? `#${registro.id} • ${registro.data_doacao}` : ''"
  >
    <div v-if="loading">Carregando…</div>
    <div v-else>
      <div class="mb-2">
        <div><b>Data:</b> {{ rec?.data_doacao }}</div>
        <div><b>Doador:</b> {{ rec?.doador_nome || `#${rec?.object_id}` }}</div>
        <div v-if="rec?.observacoes"><b>Observações:</b> {{ rec.observacoes }}</div>
      </div>

      <Divider />
      <h5 class="mt-0">Itens</h5>
      <table class="w-full">
        <thead>
          <tr>
            <th class="text-left p-2 border">Item</th>
            <th class="text-left p-2 border" style="width: 120px">Quantidade</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="i in (rec?.itens_doados || [])" :key="i.id">
            <td class="p-2 border">{{ i?.item?.nome || i?.item_nome || '-' }}</td>
            <td class="p-2 border">{{ i?.quantidade }}</td>
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
