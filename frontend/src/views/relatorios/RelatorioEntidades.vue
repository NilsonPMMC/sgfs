<script setup>
import { ref, onMounted, computed } from 'vue';
// 1. IMPORTAMOS A NOSSA INSTÂNCIA 'api'
import api from '@/services/api';
import ReportLayout from '@/views/reports/ReportLayout.vue';

// 2. REMOVEMOS A URL FIXA
// const API = 'http://127.0.0.1:8005/api/';
const rows = ref([]);
const loading = ref(true);

// --- FUNÇÕES DE FILTRO E UI ---
const paramsFromRoute = () => {
    const q = new URLSearchParams(location.search);
    return {
        classificacao: q.get('classificacao') || '',
        categoria: q.get('categoria') || '',
        bairro: q.get('bairro') || '',
        search: q.get('search') || ''
    };
};

const filtrosAtivos = computed(() => {
    const p = paramsFromRoute();
    const parts = [];
    if (p.classificacao) parts.push(`Classificação: ${p.classificacao}`);
    if (p.categoria) parts.push(`Categoria: ${p.categoria}`);
    if (p.bairro) parts.push(`Bairro: ${p.bairro}`);
    if (p.search) parts.push(`Busca: "${p.search}"`);
    return parts.join(' • ') || 'Sem filtros';
});

// --- BUSCA DE DADOS ---
const fetchAll = async () => {
    loading.value = true;
    rows.value = [];

    // 3. CONSTRUÍMOS A URL INICIAL COM CAMINHO RELATIVO E PARÂMETROS
    const p = paramsFromRoute();
    const params = new URLSearchParams({ page_size: 100 });
    if (p.classificacao) params.set('classificacao', p.classificacao);
    if (p.categoria) params.set('categoria', p.categoria);
    if (p.bairro) params.set('bairro', p.bairro);
    if (p.search) params.set('search', p.search);
    
    let nextUrl = `/entidades/?${params.toString()}`;

    while (nextUrl) {
        try {
            // 4. USAMOS 'api.get'
            const r = await api.get(nextUrl);
            rows.value.push(...(r.data?.results ?? r.data ?? []));
            // 5. USAMOS A URL COMPLETA RETORNADA PELA API PARA PAGINAÇÃO
            nextUrl = r.data?.next || null; 
        } catch (error) {
            console.error("Erro ao buscar relatório de entidades:", error);
            nextUrl = null; // Encerra o loop em caso de erro
        }
    }
    loading.value = false;
};

const printNow = () => window.print();

onMounted(fetchAll);
</script>

<template>
  <ReportLayout title="Relatório — Entidades" :subtitle="filtrosAtivos">

    <div v-if="loading">Carregando…</div>
    <div v-else>
      <table class="w-full">
        <thead>
          <tr>
            <th class="text-left p-2 border">Nome</th>
            <th class="text-left p-2 border">Classificação</th>
            <th class="text-left p-2 border">Categoria</th>
            <th class="text-left p-2 border">Bairro</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in rows" :key="e.id">
            <td class="p-2 border">{{ e.nome_fantasia || e.razao_social || e.nome }}</td>
            <td class="p-2 border">
              <span v-if="e.eh_gestor && e.eh_doador">Gestor & Doador</span>
              <span v-else-if="e.eh_gestor">Gestor</span>
              <span v-else-if="e.eh_doador">Doador</span>
              <span v-else>-</span>
            </td>
            <td class="p-2 border">{{ e.categoria?.nome || '-' }}</td>
            <td class="p-2 border">{{ e.bairro || '-' }}</td>
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
