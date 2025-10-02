<script setup>
import { ref, computed } from 'vue';
import axios from 'axios';
import { useToast } from 'primevue/usetoast';

// PrimeVue (se não usar Tag no template, pode remover a import)
import Card from 'primevue/card';
import AutoComplete from 'primevue/autocomplete';
import Calendar from 'primevue/calendar'; // (v4 deprecado; trocar por DatePicker depois)
import InputNumber from 'primevue/inputnumber';
import InputText from 'primevue/inputtext';
import Button from 'primevue/button';
import Divider from 'primevue/divider';
import Tag from 'primevue/tag';
import Toast from 'primevue/toast';

const toast = useToast();

// Base da API
const API_BASE_URL = 'http://127.0.0.1:8005/api/';

// ---- ESTADO ----
const salvando = ref(false);

const entidadesGestorasEncontradas = ref([]);
const itensEncontrados = ref([]);
const kitsEncontrados = ref([]);

const novaSaida = ref({
  data_saida: new Date(),
  entidade_gestora: null,
  itens_saida: [],     // [{ item, quantidade }]
  kits_saida: [],      // [{ kit, quantidade }]
  observacoes: ''
});

// ---- HELPERS ----
const hasItensValidos = computed(() =>
  Array.isArray(novaSaida.value.itens_saida) &&
  novaSaida.value.itens_saida.some(i => i?.item && Number(i?.quantidade) > 0)
);

const hasKitsValidos = computed(() =>
  Array.isArray(novaSaida.value.kits_saida) &&
  novaSaida.value.kits_saida.some(k => k?.kit && Number(k?.quantidade) > 0)
);

const podeSalvar = computed(() =>
  !!novaSaida.value.entidade_gestora &&
  (hasItensValidos.value || hasKitsValidos.value) &&
  !salvando.value
);

const totalLinhas = computed(() =>
  (novaSaida.value.itens_saida?.length || 0) + (novaSaida.value.kits_saida?.length || 0)
);

// **FUNÇÕES QUE ESTAVAM FALTANDO/INACESSÍVEIS NO TEMPLATE**
const getStockClass = (option) => {
  const estoque = option?.estoque_atual ?? 0;
  if (estoque === 0) return 'text-red-500';
  if (estoque > 0 && estoque <= 10) return 'text-orange-500';
  return 'text-green-500';
};

const getKitClass = (option) => {
  const montavel = option?.quantidade_montavel ?? 0;
  if (montavel === 0) return 'text-red-500';
  if (montavel > 0 && montavel <= 5) return 'text-orange-500';
  return 'text-green-500';
};

// ---- BUSCAS ----
const searchEntidadeGestora = async (event) => {
  try {
    const q = encodeURIComponent(event?.query || '');
    const resp = await axios.get(`${API_BASE_URL}entidades/?eh_gestor=true&search=${q}`);
    // Pode vir paginado (results) ou plano (array)
    entidadesGestorasEncontradas.value = Array.isArray(resp.data?.results) ? resp.data.results : (Array.isArray(resp.data) ? resp.data : []);
  } catch {
    entidadesGestorasEncontradas.value = [];
  }
};

const searchItem = async (event) => {
  try {
    const q = encodeURIComponent(event?.query || '');
    const resp = await axios.get(`${API_BASE_URL}itens/?search=${q}`);
    itensEncontrados.value = Array.isArray(resp.data?.results) ? resp.data.results : (Array.isArray(resp.data) ? resp.data : []);
  } catch {
    itensEncontrados.value = [];
  }
};

const searchKit = async (event) => {
  try {
    const q = encodeURIComponent(event?.query || '');
    const resp = await axios.get(`${API_BASE_URL}kits/?search=${q}`);
    kitsEncontrados.value = Array.isArray(resp.data?.results) ? resp.data.results : (Array.isArray(resp.data) ? resp.data : []);
  } catch {
    kitsEncontrados.value = [];
  }
};

// ---- LINHAS (add/remover) ----
const adicionarItemNaSaida = () => {
  if (!Array.isArray(novaSaida.value.itens_saida)) novaSaida.value.itens_saida = [];
  novaSaida.value.itens_saida.push({ item: null, quantidade: 1 });
};
const removerItemNaSaida = (index) => {
  if (!Array.isArray(novaSaida.value.itens_saida)) return;
  novaSaida.value.itens_saida.splice(index, 1);
};
const adicionarKitNaSaida = () => {
  if (!Array.isArray(novaSaida.value.kits_saida)) novaSaida.value.kits_saida = [];
  novaSaida.value.kits_saida.push({ kit: null, quantidade: 1 });
};
const removerKitNaSaida = (index) => {
  if (!Array.isArray(novaSaida.value.kits_saida)) return;
  novaSaida.value.kits_saida.splice(index, 1);
};

// ---- SUBMIT ----
const getApiErrorMessage = (error) => {
  const data = error?.response?.data;
  if (data?.detail) return data.detail;
  if (Array.isArray(data) && data[0]) return data[0];
  if (data && typeof data === 'object') {
    const first = Object.values(data)[0];
    if (Array.isArray(first) && first[0]) return first[0];
  }
  return 'Não foi possível registrar a saída.';
};

const saveSaida = async () => {
  if (!podeSalvar.value) {
    toast.add({ severity: 'warn', summary: 'Atenção', detail: 'Selecione a entidade gestora e adicione ao menos um item ou kit com quantidade.', life: 3500 });
    return;
  }

  salvando.value = true;

  const s = novaSaida.value;
  const payload = {
    data_saida: s.data_saida instanceof Date ? s.data_saida.toISOString().split('T')[0] : s.data_saida,
    observacoes: s.observacoes || '',
    entidade_gestora: s.entidade_gestora.id,
    itens_saida: s.itens_saida
      .filter(i => i.item && Number(i.quantidade) > 0)
      .map(i => ({ item: i.item.id, quantidade: i.quantidade })),
    kits_saida: s.kits_saida
      .filter(k => k.kit && Number(k.quantidade) > 0)
      .map(k => ({ kit: k.kit.id, quantidade: k.quantidade })),
  };

  try {
    await axios.post(`${API_BASE_URL}doacoes-realizadas/`, payload);
    toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Saída registrada! Estoque atualizado.', life: 4000 });

    // reset mantendo a data
    novaSaida.value = {
      data_saida: new Date(),
      entidade_gestora: null,
      itens_saida: [],
      kits_saida: [],
      observacoes: ''
    };
  } catch (err) {
    const msg = getApiErrorMessage(err);
    console.error('Erro ao registrar saída:', err?.response?.data || err);
    toast.add({ severity: 'error', summary: 'Erro', detail: msg, life: 6000 });
  } finally {
    salvando.value = false;
  }
};
</script>


<template>
  <div>
    <Toast />
    <div class="card">
        <div class="flex flex-wrap gap-2 items-center justify-between mb-6">
            <div class="flex gap-2">
              <Button icon="pi pi-arrow-left" severity="secondary" text rounded @click="voltar" />
              <div>
                <h3 class="m-0">Registrar Saída para Entidade Gestora</h3>
                <small>Selecione a entidade, data e os itens/kits a entregar.</small>
              </div>
            </div>
        </div>
      <Divider /> 
        <div class="grid grid-cols-12 gap-4">
            <div class="col-span-12 md:col-span-8">
            <label class="block font-semibold mb-2">Entidade Gestora</label>
            <AutoComplete
                v-model="novaSaida.entidade_gestora"
                :suggestions="entidadesGestorasEncontradas"
                @complete="searchEntidadeGestora"
                optionLabel="nome_fantasia"
                dropdown
                fluid
                placeholder="Buscar entidade..."
            >
                <template #option="slotProps">
                <div class="flex items-center justify-between w-full">
                    <span>{{ slotProps.option.nome_fantasia }}</span>
                </div>
                </template>
            </AutoComplete>
            </div>

            <div class="col-span-12 md:col-span-4">
            <label class="block font-semibold mb-2">Data da Entrega</label>
            <Calendar v-model="novaSaida.data_saida" dateFormat="dd/mm/yy" fluid />
            </div>

            <div class="col-span-12">
            <label class="block font-semibold mb-2">Observações (opcional)</label>
            <InputText v-model="novaSaida.observacoes" placeholder="Observações..." fluid />
            </div>
        </div>

        <Divider class="my-5" />

        <div class="flex items-center justify-between mb-2">
            <h5 class="m-0 font-semibold">Itens Avulsos</h5>
            <Tag :value="`${totalLinhas} linha(s)`" />
        </div>

        <div
            v-for="(itemSaida, index) in novaSaida.itens_saida"
            :key="`item-${index}`"
            class="grid grid-cols-12 gap-4 mb-3"
        >
            <div class="col-span-12 md:col-span-7">
            <label class="block font-semibold mb-2">Item</label>
            <AutoComplete
              v-model="itemSaida.item"
              :suggestions="itensEncontrados"
              @complete="searchItem"
              optionLabel="nome"
              placeholder="Busque um item..."
              dropdown
              fluid
            >
              <template #option="{ option }">
                <div class="flex items-center justify-between w-full">
                  <span class="mr-3">{{ option?.nome }}</span>
                  <span class="font-bold text-lg" :class="getStockClass(option)">
                    {{ (option?.estoque_atual ?? 0) }} {{ option?.unidade_medida || '' }}
                  </span>
                </div>
              </template>
            </AutoComplete>
            </div>

            <div class="col-span-8 md:col-span-3">
            <label class="block font-semibold mb-2">Quantidade</label>
            <InputNumber v-model="itemSaida.quantidade" mode="decimal" :min="1" fluid />
            </div>

            <div class="col-span-4 md:col-span-2 flex items-end">
            <Button
                icon="pi pi-trash"
                severity="danger"
                class="w-full md:w-auto"
                @click="removerItemNaSaida(index)"
                aria-label="Remover item"
            />
            </div>
        </div>

        <Button label="Adicionar Item Avulso" icon="pi pi-plus" text @click="adicionarItemNaSaida" />

        <Divider class="my-5" />

        <h5 class="m-0 font-semibold mb-2">Kits Prontos</h5>

        <div
            v-for="(kitSaida, index) in novaSaida.kits_saida"
            :key="`kit-${index}`"
            class="grid grid-cols-12 gap-4 mb-3"
        >
            <div class="col-span-12 md:col-span-7">
            <label class="block font-semibold mb-2">Kit</label>
            <AutoComplete
              v-model="kitSaida.kit"
              :suggestions="kitsEncontrados"
              @complete="searchKit"
              optionLabel="nome"
              placeholder="Busque um kit..."
              dropdown
              fluid
            >
              <template #option="{ option }">
                <div class="flex items-center justify-between w-full">
                  <span class="mr-3">{{ option?.nome }}</span>
                  <span class="font-bold text-lg" :class="getKitClass(option)">
                    {{ (option?.quantidade_montavel ?? 0) }} montáveis
                  </span>
                </div>
              </template>
            </AutoComplete>
            </div>

            <div class="col-span-8 md:col-span-3">
            <label class="block font-semibold mb-2">Quantidade</label>
            <InputNumber v-model="kitSaida.quantidade" :min="1" fluid />
            </div>

            <div class="col-span-4 md:col-span-2 flex items-end">
            <Button
                icon="pi pi-trash"
                severity="danger"
                class="w-full md:w-auto"
                @click="removerKitNaSaida(index)"
                aria-label="Remover kit"
            />
            </div>
        </div>

        <Button label="Adicionar Kit" icon="pi pi-plus" text @click="adicionarKitNaSaida" />
        
        <div class="flex justify-end gap-2">
            <Button
            label="Registrar Saída"
            icon="pi pi-check"
            :loading="salvando"
            :disabled="!podeSalvar"
            @click="saveSaida"
            />
        </div>
    </div>
  </div>
</template>
