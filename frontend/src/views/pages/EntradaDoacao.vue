<script setup>
// 1. IMPORTAMOS A NOSSA INSTÂNCIA 'api'
import api from '@/services/api';
import { ref, computed, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import { useRoute, useRouter } from 'vue-router';

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

// 2. REMOVEMOS A URL FIXA
// const API_BASE_URL = 'http://127.0.0.1:8005/api/';

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
    doador: null,
    observacoes: '',
    itens_doados: [{ item: null, quantidade: 1 }]
});

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
        const q = encodeURIComponent(event?.query || '');
        // 3. USAMOS 'api.get' COM CAMINHO RELATIVO
        const resp = await api.get(`/entidades/?eh_doador=true&search=${q}`);
        const results = Array.isArray(resp.data?.results) ? resp.data.results : [];
        doadoresEncontrados.value = results.map(r => ({
            ...r,
            nome: r.nome_fantasia || r.razao_social || r.nome_completo || r.nome || 'Sem nome'
        }));
    } catch {
        doadoresEncontrados.value = [];
    }
};

const searchItem = async (event) => {
    try {
        // 4. USAMOS 'api.get' COM CAMINHO RELATIVO
        const resp = await api.get(`/itens/?search=${encodeURIComponent(event.query || '')}`);
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
    if (novaDoacao.value.itens_doados.length === 1) return;
    novaDoacao.value.itens_doados.splice(index, 1);
};

const fetchEntidadeById = async (id) => {
    if (!id) return null;
    try {
        // 5. USAMOS 'api.get' COM CAMINHO RELATIVO
        const { data } = await api.get(`/entidades/${id}/`);
        return { ...data, nome: data.nome_fantasia || data.razao_social || 'Sem nome' };
    } catch {
        return null;
    }
};

const parseAPIDate = (dateString) => {
    if (!dateString) return null;

    // Pega apenas a parte da data (ignora hora, se houver)
    const dateOnlyString = dateString.split('T')[0];
    
    const parts = dateOnlyString.split('-');
    
    if (parts.length === 3) {
        const year = parseInt(parts[0], 10);
        const monthIndex = parseInt(parts[1], 10) - 1; // Mês é 0-indexado
        const day = parseInt(parts[2], 10);
        
        if (!isNaN(year) && !isNaN(monthIndex) && !isNaN(day)) {
            // Cria a data na hora local
            return new Date(year, monthIndex, day);
        }
    }
    
    // Fallback para o caso de um formato que o JS já entenda (ex: ISO completa)
    const dt = new Date(dateString);
    if (!isNaN(dt.getTime())) return dt;

    console.warn('Falha ao fazer parse da data:', dateString);
    return null; // Retorna null se tudo falhar
};

// ---- carregar (prefill/edição) ----
onMounted(async () => {
    const q = route.query;

    if (!editing.value && (q?.doador_id || q?.doador_nome)) {
        novaDoacao.value.doador = {
            id: q.doador_id ? Number(q.doador_id) : null,
            nome: q.doador_nome || ''
        };
    } else {
        novaDoacao.value.doador = null;
    }

    if (editing.value) {
        try {
            const { id } = route.params;
            // 6. USAMOS 'api.get' COM CAMINHO RELATIVO
            const resp = await api.get(`/doacoes-recebidas/${id}/`);
            const d = resp.data;

            const doadorEntidade = await fetchEntidadeById(d.object_id);

            novaDoacao.value.data_doacao = d.data_doacao ? (parseAPIDate(d.data_doacao) || new Date()) : new Date();
            novaDoacao.value.observacoes = d.observacoes || '';
            novaDoacao.value.doador = doadorEntidade ? doadorEntidade : { id: d.object_id, nome: '' };
            
            novaDoacao.value.itens_doados = Array.isArray(d.itens_doados) && d.itens_doados.length
                ? d.itens_doados.map(it => ({
                    item: it.item,
                    quantidade: Number(it.quantidade) || 0
                }))
                : [{ item: null, quantidade: 1 }];
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
        object_id: d.doador?.id,
        itens_doados: d.itens_doados
            .filter(i => i.item?.id && Number(i.quantidade) > 0)
            .map(i => ({ item_id: i.item.id, quantidade: i.quantidade }))
    };

    try {
        if (editing.value) {
            // 7. USAMOS 'api.put' COM CAMINHO RELATIVO
            await api.put(`/doacoes-recebidas/${route.params.id}/`, payload);
            toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Doação atualizada!', life: 3500 });
            router.push({ name: 'ListaEntradas' });
        } else {
            // 8. USAMOS 'api.post' COM CAMINHO RELATIVO
            await api.post('/doacoes-recebidas/', payload);
            toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Doação registrada! Estoque atualizado.', life: 4000 });
            novaDoacao.value = {
                data_doacao: new Date(),
                doador: null,
                observacoes: '',
                itens_doados: [{ item: null, quantidade: 1 }]
            };
            router.push({ name: 'ListaEntradas' });
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