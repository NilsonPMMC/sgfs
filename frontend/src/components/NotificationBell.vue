<script setup>
import { ref, onMounted, computed } from 'vue';
// 1. IMPORTAMOS A NOSSA INSTÂNCIA 'api'
import api from '@/services/api';
import OverlayPanel from 'primevue/overlaypanel';
import OverlayBadge from 'primevue/overlaybadge';

const op = ref();
const loading = ref(false);
const alertas = ref([]);
const unreadCount = ref(0);

// 2. REMOVEMOS A URL FIXA
// const API = 'http://127.0.0.1:8005/api/';

const fetchAlertas = async () => {
    loading.value = true;
    try {
        await Promise.all([
            api.post('/alertas/gerar_pendentes/').catch(() => {}),
            // --- NOVA LINHA ADICIONADA ---
            api.post('/alertas/gerar-alertas-vigencia/').catch(() => {})
        ]);
        
        // 4. USAMOS 'api.get' COM CAMINHO RELATIVO
        const r = await api.get('/alertas/');
        const lista = Array.isArray(r.data?.results) ? r.data.results : (Array.isArray(r.data) ? r.data : []);
        const naoLidos = lista.filter(a => !a.lido);
        alertas.value = naoLidos;
        unreadCount.value = naoLidos.length;
    } finally {
        loading.value = false;
    }
};

const badgeValue = computed(() =>
    unreadCount.value > 0 ? String(unreadCount.value) : undefined
);

const toggle = (e) => op.value?.toggle(e);

const marcarComoLido = async (a) => {
    try {
        // 5. USAMOS 'api.patch' COM CAMINHO RELATIVO
        await api.patch(`/alertas/${a.id}/`, { lido: true });
    } catch {}
    alertas.value = alertas.value.filter(x => x.id !== a.id);
    unreadCount.value = alertas.value.length;
};

const marcarTodos = async () => {
    try {
        // 6. USAMOS 'api.post' COM CAMINHO RELATIVO
        await api.post('/alertas/marcar_todos_lidos/');
    } catch {}
    alertas.value = [];
    unreadCount.value = 0;
};

onMounted(fetchAlertas);
</script>

<template>
  <div class="relative">
    <button type="button" class="layout-topbar-action" @click="toggle">
      <OverlayBadge :value="badgeValue" severity="danger">
        <i class="pi pi-bell" />
      </OverlayBadge>
      <span>Notificações</span>
    </button>

    <OverlayPanel ref="op" style="width: 420px">
      <div class="p-4">
        <div class="flex items-center justify-between mb-3">
          <h5 class="m-0">Notificações</h5>
          <Button link size="small" @click="marcarTodos">Marcar todas</Button>
        </div>

        <div v-if="loading" class="py-4 text-center">
          <ProgressSpinner style="width:24px; height:24px" />
        </div>

        <template v-else>
          <div v-if="alertas.length === 0" class="text-500">Nenhuma notificação pendente.</div>
          <div v-for="a in alertas" :key="a.id" class="p-3 border rounded-lg mb-2">
            <div class="flex items-center justify-between">
              <div class="font-medium">{{ a.titulo }}</div>
              <i class="pi pi-exclamation-triangle text-orange-400"></i>
            </div>
            <div class="mt-2 text-600 text-sm">{{ a.mensagem }}</div>
            <div class="mt-2 text-right">
              <Button link size="small" @click="marcarComoLido(a)">Marcar como lido</Button>
            </div>
          </div>
        </template>
      </div>
    </OverlayPanel>
  </div>
</template>

<style>
.p-overlaybadge span{
    display: inline-flex !important;
    font-size: .75rem !important;
    min-width: 1.25rem !important;
    height: 1.25rem !important;
    align-items: center;
    justify-content: center;
}
</style>