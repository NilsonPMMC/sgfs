<script setup>
// 1. IMPORTAMOS O 'api' PARA NOSSA API E MANTEMOS O 'axios' PARA APIs EXTERNAS (VIACEP)
import api from '@/services/api';
import axios from 'axios'; // Necessário para o ViaCEP
import { useAuthStore } from '@/store/auth';
import { ref, onMounted, watch, computed, reactive } from 'vue';
import { FilterMatchMode } from '@primevue/core/api';
import { useToast } from 'primevue/usetoast';
import Divider from 'primevue/divider';

// --- CONFIGURAÇÕES E ESTADO ---
const authStore = useAuthStore();
const toast = useToast();
const dt = ref();
const entidades = ref([]);
const entidadeDialog = ref(false);
const deleteEntidadeDialog = ref(false);
const deleteEntidadesDialog = ref(false);
const selectedEntidades = ref([]);
const filters = ref({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS }
});
const submitted = ref(false);

const filtros = reactive({
  classificacao: null,
  categoria: null,
  bairro: null,
});

const categorias = ref([]);
const entidade = ref({
    contatos: []
});

// 2. REMOVEMOS AS CONSTANTES DE URL FIXAS
// const API_BASE_URL = 'http://127.0.0.1:8005/api/';
// const API_URL = 'http://127.0.0.1:8005/api/entidades/';

// --- FUNÇÕES AUXILIARES --- (Nenhuma alteração aqui)
const formatDateToAPI = (date) => {
    if (!date) return null;
    const d = new Date(date);
    return d.toISOString().split('T')[0];
}
const onlyDigits = (s) => (s || '').replace(/\D/g, '');
const isValidEmail = (s) => {
  if (!s) return false;
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(s);
};
const maskDoc = (s) => {
  const d = onlyDigits(s);
  if (!d) return '';
  if (d.length > 11) {
    return d.replace(/^(\d{0,2})(\d{0,3})(\d{0,3})(\d{0,4})(\d{0,2}).*$/, (_, a,b,c,e,f) =>
      [a, b && '.'+b, c && '.'+c, e && '/'+e, f && '-'+f].filter(Boolean).join('')
    );
  }
  return d.replace(/^(\d{0,3})(\d{0,3})(\d{0,3})(\d{0,2}).*$/, (_, a,b,c,dig) =>
    [a, b && '.'+b, c && '.'+c, dig && '-'+dig].filter(Boolean).join('')
  );
};
const maskPhone = (s) => {
  const d = onlyDigits(s).slice(0, 11);
  if (!d) return '';
  if (d.length <= 10) {
    return d.replace(/^(\d{0,2})(\d{0,4})(\d{0,4}).*$/, (_, a,b,c) =>
      [a && `(${a})`, b && ' '+b, c && '-'+c].filter(Boolean).join('')
    );
  }
  return d.replace(/^(\d{0,2})(\d{0,5})(\d{0,4}).*$/, (_, a,b,c) =>
    [a && `(${a})`, b && ' '+b, c && '-'+c].filter(Boolean).join('')
  );
};
const onDocInput = (e) => { entidade.value.documento = onlyDigits(e.target.value).slice(0, 14); };
const onPhoneInput = (contato, e) => { contato.valor = onlyDigits(e.target.value).slice(0, 11); };
const formatDocumento = (v) => maskDoc(v);
const contatoStats = computed(() => {
  const t = entidade.value?.contatos?.filter(c => c.tipo_contato === 'T').length || 0;
  const e = entidade.value?.contatos?.filter(c => c.tipo_contato === 'E').length || 0;
  return { telefones: t, emails: e };
});
const toggleError = ref(false);

// --- BUSCA INICIAL DE DADOS ---
const fetchData = async () => {
    let allEntidades = [];
    let nextUrl = '/entidades/'; // A primeira chamada é relativa

    while (nextUrl) {
        try {
            const response = await api.get(nextUrl);
            allEntidades = allEntidades.concat(response.data.results);
            // CORREÇÃO: Usamos a URL completa que a API nos dá para as próximas páginas
            nextUrl = response.data.next;
        } catch (error) {
            console.error("Erro ao buscar uma página de entidades:", error);
            toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível carregar todas as entidades.', life: 3000 });
            nextUrl = null;
        }
    }
    entidades.value = allEntidades;
};

onMounted(() => {
    fetchData();

    // 4. USAMOS 'api' PARA BUSCAR CATEGORIAS
    api.get('/categorias/')
        .then(response => {
            categorias.value = response.data.results || response.data;
        })
        .catch(error => {
            console.error("Erro ao buscar categorias:", error);
        });
});

// A CHAMADA PARA O VIACEP CONTINUA USANDO 'axios' POR SER EXTERNA
watch(() => entidade.value.cep, (novoCep) => {
    const cepLimpo = (novoCep || '').replace(/\D/g, '');
    if (cepLimpo.length === 8) {
        axios.get(`https://viacep.com.br/ws/${cepLimpo}/json/`)
            .then(response => {
                if (response.data.erro) {
                    toast.add({ severity: 'warn', summary: 'Aviso', detail: 'CEP não encontrado.', life: 3000 });
                } else {
                    entidade.value.logradouro = response.data.logradouro;
                    entidade.value.bairro = response.data.bairro;
                }
            })
            .catch(error => {
                console.error("Erro ao buscar CEP:", error);
                toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível consultar o CEP.', life: 3000 });
            });
    }
});

// --- FUNÇÕES DE CONTATO ---
const addContato = (tipo) => {
    entidade.value.contatos.push({
        tipo_contato: tipo,
        valor: '',
        descricao: ''
    });
};

const removeContato = (contatoParaRemover) => {
    entidade.value.contatos = entidade.value.contatos.filter(c => c !== contatoParaRemover);
    if (contatoParaRemover.id) {
        // 5. USAMOS 'api' PARA DELETAR CONTATO
        api.delete(`/contatos/${contatoParaRemover.id}/`)
            .then(() => {
                toast.add({ severity: 'info', summary: 'Aviso', detail: 'Contato removido.', life: 2000 });
            })
            .catch(err => console.error("Erro ao deletar contato:", err));
    }
};

// --- FUNÇÕES DO CRUD --- (O restante das funções do CRUD e lógicas continuam iguais)
watch(entidade, (novoValor) => {
    if (novoValor.eh_doador && !novoValor.eh_gestor) {
        const categoriaDoador = categorias.value.find(c => c.nome.toLowerCase() === 'doador');
        if (categoriaDoador) {
            novoValor.categoria = categoriaDoador.id;
        }
    }
}, { deep: true });

const openNew = () => {
    entidade.value = {
        data_cadastro: new Date(),
        eh_doador: false,
        eh_gestor: false,
        contatos: [],
        documento: '',
        cep: ''
    };
    submitted.value = false;
    entidadeDialog.value = true;
};

const hideDialog = () => {
    entidadeDialog.value = false;
    submitted.value = false;
};

const saveEntidade = async () => {
    submitted.value = true;
    toggleError.value = !(entidade.value.eh_doador || entidade.value.eh_gestor);
    if (!entidade.value.razao_social || toggleError.value) return;

    const emailsInvalidos = entidade.value.contatos
        .filter(c => c.tipo_contato === 'E')
        .some(c => !isValidEmail(c.valor));
    if (emailsInvalidos) {
        toast.add({ severity: 'error', summary: 'E-mail inválido', detail: 'Verifique os endereços de e-mail nos contatos.', life: 3000 });
        return;
    }

    let entidadePayload = { ...entidade.value };
    entidadePayload.data_cadastro = formatDateToAPI(entidadePayload.data_cadastro);
    entidadePayload.vigencia_de = formatDateToAPI(entidadePayload.vigencia_de);
    entidadePayload.vigencia_ate = formatDateToAPI(entidadePayload.vigencia_ate);
    entidadePayload.documento = onlyDigits(entidadePayload.documento);
    entidadePayload.cep = onlyDigits(entidadePayload.cep);
    entidadePayload.categoria = entidadePayload.categoria ?? null;
    
    delete entidadePayload.contatos; 
    
    try {
        let savedEntidade;
        // 6. USAMOS 'api' PARA SALVAR A ENTIDADE (PUT ou POST)
        if (entidade.value.id) {
            const response = await api.put(`/entidades/${entidade.value.id}/`, entidadePayload);
            savedEntidade = response.data;
        } else {
            const response = await api.post('/entidades/', entidadePayload);
            savedEntidade = response.data;
        }

        // 7. USAMOS 'api' PARA SALVAR OS CONTATOS (PUT ou POST)
        const contatosPromises = entidade.value.contatos.map(contato => {
            const contatoPayload = { ...contato, entidade: savedEntidade.id };
            if (contatoPayload.tipo_contato === 'T') {
                contatoPayload.valor = onlyDigits(contatoPayload.valor);
            }
            if (contato.id) {
                return api.put(`/contatos/${contato.id}/`, contatoPayload);
            } else {
                return api.post('/contatos/', contatoPayload);
            }
        });

        await Promise.all(contatosPromises);

        toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Entidade salva com sucesso!', life: 3000 });
        entidadeDialog.value = false;
        fetchData();

    } catch (err) {
        console.error("Erro ao salvar entidade:", err.response?.data || err);
        toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível salvar a entidade.', life: 3000 });
    }
};

const editEntidade = (prod) => {
    // 8. USAMOS 'api' PARA BUSCAR A ENTIDADE PARA EDIÇÃO
    api.get(`/entidades/${prod.id}/`).then(response => {
        entidade.value = response.data;
        const cat = entidade.value.categoria;
        entidade.value.categoria = (cat && typeof cat === 'object') ? cat.id : (cat ?? null);
        
        if (entidade.value.data_cadastro) entidade.value.data_cadastro = new Date(entidade.value.data_cadastro);
        if (entidade.value.vigencia_de) entidade.value.vigencia_de = new Date(entidade.value.vigencia_de);
        if (entidade.value.vigencia_ate) entidade.value.vigencia_ate = new Date(entidade.value.vigencia_ate);

        entidadeDialog.value = true;
    });
};

const confirmDeleteEntidade = (prod) => {
    entidade.value = prod;
    deleteEntidadeDialog.value = true;
};

const deleteEntidade = () => {
    // 9. USAMOS 'api' PARA DELETAR A ENTIDADE
    api.delete(`/entidades/${entidade.value.id}/`)
        .then(() => {
            toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Entidade deletada!', life: 3000 });
            deleteEntidadeDialog.value = false;
            fetchData();
        })
        .catch(err => {
            console.error("Erro ao deletar:", err);
            toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível deletar a entidade.', life: 3000 });
        });
};

const confirmDeleteSelected = () => {
    deleteEntidadesDialog.value = true;
};

const deleteSelectedEntidades = () => {
    // 10. USAMOS 'api' PARA DELETAR MÚLTIPLAS ENTIDADES
    const promises = selectedEntidades.value.map(ent => api.delete(`/entidades/${ent.id}/`));
    
    Promise.all(promises)
        .then(() => {
            toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Entidades deletadas!', life: 3000 });
            deleteEntidadesDialog.value = false;
            selectedEntidades.value = [];
            fetchData();
        })
        .catch(err => {
            console.error("Erro ao deletar selecionados:", err);
            toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível deletar as entidades selecionadas.', life: 3000 });
        });
};

// --- FILTROS E RELATÓRIOS --- (Nenhuma alteração aqui)
const classificacoesOptions = [
  { label: 'Todos', value: null },
  { label: 'Gestor/Recebedor', value: 'gestor' },
  { label: 'Doador', value: 'doador' },
  { label: 'Ambos (Gestor e Doador)', value: 'ambos' }
];
const categoriaSelecionadaId = computed(() =>
  typeof filtros.categoria === 'object' ? filtros.categoria?.id : filtros.categoria
);
const entidadesFiltradas = computed(() => {
  const termo = (filters.value?.global?.value || '').toString().toLowerCase().trim();
  const catId = categoriaSelecionadaId.value;
  const cls = filtros.classificacao;
  const bairro = (filtros.bairro || '').toString().toLowerCase().trim();

  return (entidades.value || []).filter(e => {
    const passaBusca =
      !termo ||
      (e.nome_fantasia || '').toLowerCase().includes(termo) ||
      (e.razao_social || '').toLowerCase().includes(termo) ||
      (e.documento || '').toString().includes(termo) ||
      (e.bairro || '').toLowerCase().includes(termo);
    let passaClassificacao = true;
    if (cls === 'gestor') passaClassificacao = !!e.eh_gestor;
    else if (cls === 'doador') passaClassificacao = !!e.eh_doador;
    else if (cls === 'ambos') passaClassificacao = !!e.eh_gestor && !!e.eh_doador;
    const idDoRegistro = typeof e.categoria === 'object' ? e.categoria?.id : e.categoria;
    const passaCategoria = !catId || idDoRegistro === catId;
    const passaBairro = !bairro || (e.bairro || '').toLowerCase().includes(bairro);
    return passaBusca && passaClassificacao && passaCategoria && passaBairro;
  });
});
const limparFiltros = () => {
  filtros.classificacao = null;
  filtros.categoria = null;
  filtros.bairro = null;
  filters.value.global.value = null;
};
const buildRelatorioQuery = () => {
  const qs = new URLSearchParams();
  if (filtros.classificacao) qs.set('classificacao', filtros.classificacao);
  const categoriaId = typeof filtros.categoria === 'object' ? filtros.categoria?.id : filtros.categoria;
  if (categoriaId) qs.set('categoria', categoriaId);
  if (filtros.bairro) qs.set('bairro', filtros.bairro);
  const q = filters.value?.global?.value;
  if (q) qs.set('search', q);
  return qs.toString();
};
const abrirRelatorioEntidades = () => {
  const query = buildRelatorioQuery();
  window.open(`/relatorios/entidades?${query}`, '_blank');
};
const exportCSV = () => {
    dt.value.exportCSV();
};

</script>

<template>
    <div>
        <Toast />
        <div class="card">
            <Toolbar class="mb-4">
                <template #start>
                    <Button label="Nova Entidade" icon="pi pi-plus" class="p-button-success mr-2" @click="openNew" />
                    <Button label="Deletar" icon="pi pi-trash" class="p-button-danger" @click="confirmDeleteSelected" :disabled="!selectedEntidades || !selectedEntidades.length" />
                </template>

                <template #end>
                    <Button
                        label="Relatório"
                        icon="pi pi-print"
                        class="p-button-help mr-2"
                        @click="abrirRelatorioEntidades"
                    />
                    <Button label="Exportar CSV" icon="pi pi-upload" class="p-button-help" @click="exportCSV($event)" />
                </template>
            </Toolbar>

            <DataTable
                ref="dt"
                v-model:selection="selectedEntidades"
                :value="entidadesFiltradas"
                dataKey="id"
                :paginator="true"
                :rows="10"
                :filters="filters"
                paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
                :rowsPerPageOptions="[5, 10, 25]"
                currentPageReportTemplate="Mostrando {first} a {last} de {totalRecords} entidades"
            >

                <template #header>
                    <div class="flex flex-col gap-3 w-full">
                        <div class="flex flex-wrap gap-2 items-center justify-between">
                        <h4 class="m-0">Gerenciar Entidades</h4>

                        <div class="flex items-center gap-3">
                            <!-- Busca global -->
                            <IconField>
                            <InputIcon>
                                <i class="pi pi-search" />
                            </InputIcon>
                            <InputText v-model="filters['global'].value" placeholder="Buscar (nome, doc, bairro)..." />
                            </IconField>

                            <!-- Botão limpar -->
                            <Button icon="pi pi-filter-slash" label="Limpar" text @click="limparFiltros" />
                        </div>
                        </div>

                        <!-- Linha de filtros -->
                        <div class="grid grid-cols-12 gap-3">
                        <div class="col-span-12 md:col-span-4">
                            <label class="block text-sm font-semibold mb-1">Classificação</label>
                            <Dropdown
                            v-model="filtros.classificacao"
                            :options="classificacoesOptions"
                            optionLabel="label"
                            optionValue="value"
                            placeholder="Todos"
                            showClear
                            fluid
                            />
                        </div>

                        <div class="col-span-12 md:col-span-4">
                            <label class="block text-sm font-semibold mb-1">Categoria</label>
                            <Dropdown
                            v-model="filtros.categoria"
                            :options="categorias"
                            optionLabel="nome"
                            optionValue="id"
                            placeholder="Todas"
                            showClear
                            filter
                            fluid
                            />
                        </div>

                        <div class="col-span-12 md:col-span-4">
                            <label class="block text-sm font-semibold mb-1">Bairro</label>
                            <InputText v-model="filtros.bairro" placeholder="Ex.: Centro" fluid />
                        </div>
                        </div>
                    </div>
                </template>

                <Column selectionMode="multiple" style="width: 3rem" :exportable="false"></Column>
                <Column field="nome_fantasia" header="Nome Fantasia" sortable style="min-width: 16rem">
                    <template #body="slotProps">
                        <router-link class="font-bold" :to="{ name: 'detalhes-entidade', params: { id: slotProps.data.id } }">
                            {{ slotProps.data.nome_fantasia }}
                        </router-link>
                    </template>
                </Column>
                <Column header="CNPJ ou CPF" sortable style="min-width: 12rem">
                    <template #body="{ data }">
                        {{ formatDocumento(data.documento) }}
                    </template>
                </Column>
                <Column header="Classificação" style="min-width: 12rem">
                    <template #body="slotProps">
                        <Tag v-if="slotProps.data.eh_doador" value="Doador" severity="success" class="mr-2"></Tag>
                        <Tag v-if="slotProps.data.eh_gestor" value="Gestor" severity="info"></Tag>
                    </template>
                </Column>
                <Column header="Contatos" style="min-width: 10rem">
                    <template #body="{ data }">
                        <Tag v-if="data.contatos" :value="`${data.contatos.filter(c=>c.tipo_contato==='T').length} Tel`" class="mr-2" />
                        <Tag v-if="data.contatos" :value="`${data.contatos.filter(c=>c.tipo_contato==='E').length} Email`" />
                    </template>
                </Column>
                <Column field="bairro" header="Bairro" sortable style="min-width: 16rem"></Column>
                <Column :exportable="false" header="Ações" style="min-width: 8rem">
                    <template #body="slotProps">
                        <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editEntidade(slotProps.data)" />
                        <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmDeleteEntidade(slotProps.data)" />
                    </template>
                </Column>
            </DataTable>
        </div>

        <Dialog v-model:visible="entidadeDialog" :style="{ width: '50rem' }" header="Detalhes da Entidade" :modal="true">
            <div class="flex flex-col gap-6">
                <div class="grid grid-cols-12 gap-4">
                    <div class="flex col-span-6">
                        <InputSwitch v-model="entidade.eh_gestor" inputId="gestor-switch" />
                        <label for="gestor-switch" class="font-bold ml-3"> Marcar como Gestor/Recebedor</label>
                    </div>
                    <div class="flex col-span-6">
                        <InputSwitch v-model="entidade.eh_doador" inputId="doador-switch" />
                        <label for="doador-switch" class="font-bold ml-3"> Marcar como Doador</label>
                    </div>
                </div>
                <small class="p-error" v-if="submitted && toggleError">
                    Marque pelo menos uma opção: Gestor/Recebedor ou Doador.
                </small>
                <Divider class="my-4" />
                <div class="grid grid-cols-12 gap-4">
                    <div class="col-span-8">
                        <label for="razao_social" class="block font-bold mb-3">Razão Social</label>
                        <InputText id="razao_social" v-model.trim="entidade.razao_social" required="true" autofocus :class="{'p-invalid': submitted && !entidade.razao_social}" fluid />
                        <small class="p-error" v-if="submitted && !entidade.razao_social">Razão Social é obrigatório.</small>
                    </div>
                    <div class="col-span-4">
                        <label for="documento" class="block font-bold mb-3">CNPJ ou CPF</label>
                        <InputText
                            id="documento"
                            :value="maskDoc(entidade.documento)"
                            @input="onDocInput"
                            inputmode="numeric"
                            required
                            :class="{'p-invalid': submitted && !entidade.documento}"
                            fluid
                            />
                        <small class="p-error" v-if="submitted && !entidade.documento">CNPJ ou CPF é obrigatório.</small>
                    </div>
                </div>
                <div class="grid grid-cols-12 gap-4">
                    <div class="col-span-8">
                        <label for="nome_fantasia" class="block font-bold mb-3">Nome Fantasia</label>
                        <InputText id="nome_fantasia" v-model.trim="entidade.nome_fantasia" fluid />
                    </div>
                    <div v-if="!entidade.eh_doador || entidade.eh_gestor" class="col-span-4">
                        <label for="categoria" class="block font-bold mb-3">Categoria</label>
                        <Dropdown id="categoria"
                            v-model="entidade.categoria"
                            :options="categorias"
                            optionLabel="nome"
                            optionValue="id"
                            placeholder="Selecione"
                            fluid />
                    </div>
                </div>
                <div v-if="!entidade.eh_doador || entidade.eh_gestor" class="grid grid-cols-12 gap-4">
                    <div class="col-span-4">
                        <label for="data_cadastro" class="block font-bold mb-3">Data de Cadastro</label>
                        <Calendar id="data_cadastro" v-model="entidade.data_cadastro" dateFormat="dd/mm/yy" fluid />
                    </div>
                    <div class="col-span-4">
                        <label for="vigencia_de" class="block font-bold mb-3">Vigência De (MM/AAAA)</label>
                        <Calendar id="vigencia_de" v-model="entidade.vigencia_de" view="month" dateFormat="mm/yy" fluid />
                    </div>
                    <div class="col-span-4">
                        <label for="vigencia_ate" class="block font-bold mb-3">Vigência Até (MM/AAAA)</label>
                        <Calendar id="vigencia_ate" v-model="entidade.vigencia_ate" view="month" dateFormat="mm/yy" fluid />
                    </div>
                </div>
                <Divider class="m-0" align="left" type="solid">
                    <b>Contatos</b>
                </Divider>
                <div class="mb-2 text-sm text-gray-600">
                    {{ contatoStats.telefones }} telefone(s) · {{ contatoStats.emails }} e-mail(s)
                </div>
                <div v-for="(contato, index) in entidade.contatos" :key="index">
                    <div class="grid grid-cols-12 gap-4">
                        <div class="col-span-2">
                            <label for="tipo" class="block font-bold mb-3">Tipo</label>
                            <InputText id="tipo" :value="contato.tipo_contato === 'T' ? 'Telefone' : 'Email'" disabled fluid />
                        </div>
                        <div class="col-span-5">
                            <label for="contato-valor" class="block font-bold mb-3">Contato</label>
                            <template v-if="contato.tipo_contato === 'T'">
                                <InputText
                                    :value="maskPhone(contato.valor)"
                                    @input="(e) => onPhoneInput(contato, e)"
                                    inputmode="tel"
                                    fluid
                                    />
                            </template>
                            <template v-else>
                                <InputText v-model.trim="contato.valor"
                                    type="email"
                                    :class="{'p-invalid': contato.valor && !isValidEmail(contato.valor)}"
                                    placeholder="email@exemplo.com"
                                    fluid />
                                <small class="p-error" v-if="contato.valor && !isValidEmail(contato.valor)">
                                    E-mail inválido.
                                </small>
                            </template>
                        </div>
                        <div class="col-span-4">
                            <label for="contato-desc" class="block font-bold mb-3">Contato</label>
                            <InputText v-model.trim="contato.descricao" placeholder="Ex: Celular, Whatsapp" fluid />
                        </div>
                        <div class="col-span-1">
                            <label class="block font-bold mb-3">&nbsp;</label>
                            <Button icon="pi pi-trash" class="p-button-danger" @click="removeContato(contato)" />
                        </div>
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <Button label="Adicionar Telefone" icon="pi pi-phone" class="p-button-outlined mr-2" @click="addContato('T')" />
                    <Button label="Adicionar Email" icon="pi pi-envelope" class="p-button-outlined" @click="addContato('E')" />
                </div>
                <div class="grid grid-cols-12 gap-4">
                    <div class="col-span-3">
                        <label for="cep" class="block font-bold mb-3">CEP</label>
                        <InputMask id="cep" v-model="entidade.cep" mask="99999-999" :unmask="true" fluid />
                    </div>
                    <div class="col-span-9">
                        <label for="logradouro" class="block font-bold mb-3">Logradouro (Rua, Av.)</label>
                        <InputText id="logradouro" v-model="entidade.logradouro" fluid />
                    </div>
                    <div class="col-span-3">
                        <label for="numero" class="block font-bold mb-3">Número</label>
                        <InputText id="numero" v-model="entidade.numero" fluid />
                    </div>
                    <div class="col-span-9">
                        <label for="bairro" class="block font-bold mb-3">Bairro</label>
                        <InputText id="bairro" v-model="entidade.bairro" fluid />
                    </div>
                </div>
                <div>
                    <label for="observacoes" class="block font-bold mb-3">Observações</label>
                    <Textarea id="observacoes" v-model="entidade.observacoes" rows="3" fluid />
                </div>
            </div>
            <template #footer>
                <Button label="Cancelar" icon="pi pi-times" text @click="hideDialog" />
                <Button label="Salvar" icon="pi pi-check" @click="saveEntidade" />
            </template>
        </Dialog>

        <Dialog v-model:visible="deleteEntidadeDialog" :style="{ width: '450px' }" header="Confirmar" :modal="true">
            <div class="flex align-items-center">
                <i class="pi pi-exclamation-triangle mr-3" style="font-size: 2rem" />
                <span v-if="entidade">Tem certeza que deseja deletar <b>{{ entidade.nome_fantasia }}</b>?</span>
            </div>
            <template #footer>
                <Button label="Não" icon="pi pi-times" text @click="deleteEntidadeDialog = false" />
                <Button label="Sim" icon="pi pi-check" @click="deleteEntidade" />
            </template>
        </Dialog>

        <Dialog v-model:visible="deleteEntidadesDialog" :style="{ width: '450px' }" header="Confirmar" :modal="true">
             <div class="flex align-items-center">
                <i class="pi pi-exclamation-triangle mr-3" style="font-size: 2rem" />
                <span>Tem certeza que deseja deletar as entidades selecionadas?</span>
            </div>
            <template #footer>
                <Button label="Não" icon="pi pi-times" text @click="deleteEntidadesDialog = false" />
                <Button label="Sim" icon="pi pi-check" @click="deleteSelectedEntidades" />
            </template>
        </Dialog>
    </div>
</template>