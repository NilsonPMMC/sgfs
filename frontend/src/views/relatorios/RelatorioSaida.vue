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
const rec = ref(null);
const loading = ref(true);

const printNow = () => window.print();

onMounted(async () => {
    loading.value = true;
    const id = route.params.id;
    try {
        // 3. USAMOS 'api.get' COM CAMINHO RELATIVO
        const r = await api.get(`/doacoes-realizadas/${id}/`);
        rec.value = r.data;
    } catch (error) {
        console.error("Erro ao buscar dados do relatório:", error);
    } finally {
        loading.value = false;
    }
});
</script>

<template>
  <ReportLayout
    title="Relatório — Doação (Saída)"
    :subtitle="registro ? `#${registro.id} • ${registro.data_saida}` : ''"
  >

    <div v-if="loading">Carregando…</div>
    <div v-else>
      <div class="mb-2">
        <div><b>Data:</b> {{ rec?.data_saida }}</div>
        <div><b>Entidade Gestora:</b> {{ rec?.entidade_gestora_nome || `#${rec?.entidade_gestora}` }}</div>
        <div v-if="rec?.observacoes"><b>Observações:</b> {{ rec.observacoes }}</div>
      </div>

      <Divider />
      <h5 class="mt-0">Itens Avulsos</h5>
      <table class="w-full mb-4">
        <thead>
          <tr>
            <th class="text-left p-2 border">Item</th>
            <th class="text-left p-2 border" style="width: 120px">Quantidade</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="i in (rec?.itens_saida || [])" :key="i.id">
            <td class="p-2 border">{{ i?.item?.nome || i?.item_nome || '-' }}</td>
            <td class="p-2 border">{{ i?.quantidade }}</td>
          </tr>
        </tbody>
      </table>

      <h5 class="mt-4">Kits</h5>
      <table class="w-full">
        <thead>
          <tr>
            <th class="text-left p-2 border">Kit</th>
            <th class="text-left p-2 border" style="width: 120px">Quantidade</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="k in (rec?.kits_saida || [])" :key="k.id">
            <td class="p-2 border">{{ k?.kit?.nome || k?.kit_nome || '-' }}</td>
            <td class="p-2 border">{{ k?.quantidade }}</td>
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
