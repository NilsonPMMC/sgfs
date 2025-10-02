<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { useToast } from 'primevue/usetoast';
import { useRoute, useRouter } from 'vue-router';

// (Se seus componentes PrimeVue são registrados globalmente, estes imports são opcionais.
// Mantive para manter consistência com seu projeto.)
import Card from 'primevue/card';
import AutoComplete from 'primevue/autocomplete';
import Calendar from 'primevue/calendar';
import InputNumber from 'primevue/inputnumber';
import InputText from 'primevue/inputtext';
import Button from 'primevue/button';
import Divider from 'primevue/divider';
import Tag from 'primevue/tag';
import Toast from 'primevue/toast';

const toast = useToast();
const route = useRoute();
const router = useRouter();

// Base da API (troque por env se preferir)
const API_BASE_URL = 'http://127.0.0.1:8005/api/';

// ---- helpers ----
const getApiErrorMessage = (error) => {
  const data = error?.response?.data;
  if (data?.detail) return data.detail;
  if (Array.isArray(data) && data[0]) return data[0];
  if (data && typeof data === 'object') {
    const first = Object.values(data)[0];
    if (Array.isArray(first) && first[0]) return first[0];
  }
  return 'Não foi possível registrar/atualizar a doação.';
};
const voltar = () => router.back();

// ---- estado ----
const salvando = ref(false);
const doadoresEncontrados = ref([]);
const itensEncontrados = ref([]);

const novaDoacao = ref({
  data_doacao: new Date(),
  doador: null,           // { id, nome, content_type_id, tipo? }
  observacoes: '',
  itens_doados: [{ item: null, quantidade: 1 }] // item: {id, nome, unidade_medida}
});

// create vs edit
const editing = computed(() => Boolean(route.params.id));

// ---- computeds ----
const podeSalvar = computed(() => {
  const d = novaDoacao.value;
  const temItensValidos = d.itens_doados.length > 0 && d.itens_doados.every(i => i.item && Number(i.quantidade) > 0);
  return !!d.doador && temItensValidos && !salvando.value;
});
const totalLinhas = computed(() => novaDoacao.value.itens_doados.length);

// ---- buscas ----
const searchDoador = async (event) => {
  try {
    const resp = await axios.get(`${API_BASE_URL}doador-search/?query=${encodeURIComponent(event.query || '')}`);
    doadoresEncontrados.value = resp.data;
  } catch {
    doadoresEncontrados.value = [];
  }
};

const searchItem = async (event) => {
  try {
    const resp = await axios.get(`${API_BASE_URL}itens/?search=${encodeURIComponent(event.query || '')}`);
    itensEncontrados.value = Array.isArray(resp.data?.results) ? resp.data.results : [];
  } catch {
    itensEncontrados.value = [];
  }
};

// ---- linhas de itens ----
const adicionarItem = () => {
  novaDoacao.value.itens_doados.push({ item: null, quantidade: 1 });
};
const removerItem = (index) => {
  if (novaDoacao.value.itens_doados.length === 1) return; // evita ficar sem nenhuma linha
  novaDoacao.value.itens_doados.splice(index, 1);
};

// ---- carregar (prefill/edição) ----
onMounted(async () => {
  const q = route.query;

  // Prefill (vindo da página de detalhes da entidade/pessoa)
  if (!editing.value && (q?.doador_id || q?.doador_nome)) {
    novaDoacao.value.doador = {
      id: q.doador_id ? Number(q.doador_id) : null,
      nome: q.doador_nome || 'Doador selecionado',
      content_type_id: q.content_type_id ? Number(q.content_type_id) : null,
      tipo: q.tipo || undefined
    };
  }

  // Edição: carrega a doação existente
  if (editing.value) {
    try {
      const { id } = route.params;
      const resp = await axios.get(`${API_BASE_URL}doacoes-recebidas/${id}/`);
      const d = resp.data;

      // mapeamento defensivo (ajuste conforme seu serializer)
      novaDoacao.value = {
        data_doacao: d.data_doacao ? new Date(d.data_doacao) : new Date(),
        doador: {
          id: d.object_id ?? d.doador_id ?? d.doador?.id ?? null,
          content_type_id: d.content_type ?? d.doador?.content_type_id ?? null,
          nome: d.doador_nome ?? d.doador?.nome ?? 'Doador'
        },
        observacoes: d.observacoes || '',
        itens_doados: Array.isArray(d.itens_doados)
          ? d.itens_doados.map(it => ({
              item: {
                id: it.item ?? it.item_id,
                nome: it.item_nome ?? it.nome ?? 'Item',
                unidade_medida: it.unidade_medida
              },
              quantidade: it.quantidade
            }))
          : [{ item: null, quantidade: 1 }]
      };
    } catch (err) {
      console.error('Falha ao carregar doação para edição:', err?.response?.data || err);
      toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível carregar a doação.', life: 5000 });
    }
  }
});

// ---- submit ----
const saveDoacao = async () => {
  if (!podeSalvar.value) {
    toast.add({ severity: 'warn', summary: 'Atenção', detail: 'Preencha o doador e ao menos um item com quantidade.', life: 3000 });
    return;
  }

  salvando.value = true;

  const d = novaDoacao.value;
  const payload = {
    data_doacao: d.data_doacao instanceof Date ? d.data_doacao.toISOString().split('T')[0] : d.data_doacao,
    observacoes: d.observacoes || '',
    content_type: d.doador.content_type ?? d.doador.content_type_id ?? d.doador.ct,
    object_id: d.doador.id,
    itens_doados: d.itens_doados
      .filter(i => i.item && Number(i.quantidade) > 0)
      .map(i => ({ item_id: i.item.id, quantidade: i.quantidade }))
  };

  try {
    if (editing.value) {
      await axios.put(`${API_BASE_URL}doacoes-recebidas/${route.params.id}/`, payload);
      toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Doação atualizada!', life: 3500 });
      // opcional: voltar para a tela anterior
      // router.back();
    } else {
      console.log('payload doacao recebida ->', payload);
      await axios.post(`${API_BASE_URL}doacoes-recebidas/`, payload);
      toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Doação registrada! Estoque atualizado.', life: 4000 });
      // reset básico mantendo a data de hoje
      novaDoacao.value = {
        data_doacao: new Date(),
        doador: null,
        observacoes: '',
        itens_doados: [{ item: null, quantidade: 1 }]
      };
    }
  } catch (err) {
    const msg = getApiErrorMessage(err);
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
            <h3 class="m-0">Registrar Nova Doação (Entrada)</h3>
            <small>Informe o doador, a data e os itens doados. Ao salvar, o estoque é atualizado.</small>
          </div>
        </div>
      </div>
      <Divider />
      <div class="grid grid-cols-12 gap-4">
        <div class="col-span-12 md:col-span-8">
          <label class="block font-semibold mb-2">Doador (Pessoa ou Entidade)</label>
          <AutoComplete
            v-model="novaDoacao.doador"
            :suggestions="doadoresEncontrados"
            @complete="searchDoador"
            optionLabel="nome"
            dropdown
            fluid
            placeholder="Buscar doador..."
          >
            <template #option="slotProps">
              <div class="flex items-center justify-between w-full">
                <span>{{ slotProps.option.nome }}</span>
                <small class="opacity-70">{{ slotProps.option.tipo }}</small>
              </div>
            </template>
          </AutoComplete>
        </div>

        <div class="col-span-12 md:col-span-4">
          <label class="block font-semibold mb-2">Data da Doação</label>
          <Calendar v-model="novaDoacao.data_doacao" dateFormat="dd/mm/yy" fluid />
        </div>

        <div class="col-span-12">
          <label class="block font-semibold mb-2">Observações (opcional)</label>
          <InputText v-model="novaDoacao.observacoes" placeholder="Observações..." fluid />
        </div>
      </div>

      <Divider class="my-5" />

      <div class="flex items-center justify-between mb-2">
        <h5 class="m-0 font-semibold">Itens Doados</h5>
        <Tag :value="`${totalLinhas} linha(s)`" />
      </div>

      <div
        v-for="(itemDoado, index) in novaDoacao.itens_doados"
        :key="index"
        class="grid grid-cols-12 gap-4 mb-3"
      >
        <div class="col-span-12 md:col-span-8">
          <label class="block font-semibold mb-2">Item</label>
          <AutoComplete
            v-model="itemDoado.item"
            :suggestions="itensEncontrados"
            @complete="searchItem"
            optionLabel="nome"
            placeholder="Busque um item..."
            dropdown
            fluid
          >
            <template #option="slotProps">
              <div class="flex items-center justify-between w-full">
                <span class="mr-2">{{ slotProps.option.nome }}</span>
                <Tag>{{ slotProps.option.unidade_medida }}</Tag>
              </div>
            </template>
          </AutoComplete>
        </div>

        <div class="col-span-8 md:col-span-3">
          <label class="block font-semibold mb-2">Quantidade</label>
          <InputNumber v-model="itemDoado.quantidade" mode="decimal" :min="1" fluid />
        </div>

        <div class="col-span-4 md:col-span-1 flex items-end">
          <Button
            icon="pi pi-trash"
            severity="danger"
            class="w-full md:w-auto"
            @click="removerItem(index)"
            :disabled="novaDoacao.itens_doados.length === 1"
            aria-label="Remover linha"
          />
        </div>
      </div>

      <Button label="Adicionar outro item" icon="pi pi-plus" text @click="adicionarItem" />


      <div class="flex justify-end gap-2">
        <Button
          label="Salvar Doação"
          icon="pi pi-check"
          :loading="salvando"
          :disabled="!podeSalvar"
          @click="saveDoacao"
        />
      </div>
    </div>
  </div>
</template>