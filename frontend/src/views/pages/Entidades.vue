<script setup>
import { useAuthStore } from '@/store/auth';
import { ref, onMounted, watch } from 'vue';
import { FilterMatchMode } from '@primevue/core/api';
import { useToast } from 'primevue/usetoast';
import axios from 'axios';
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

// NOVA VARIÁVEL PARA ARMAZENAR AS CATEGORIAS
const categorias = ref([]); 
const entidade = ref({
    contatos: [] // Inicializa a entidade com uma lista de contatos
});
const API_BASE_URL = 'http://127.0.0.1:8005/api/';
const API_URL = 'http://127.0.0.1:8005/api/entidades/';

// --- FUNÇÕES AUXILIARES ---
const formatDateToAPI = (date) => {
    if (!date) return null;
    const d = new Date(date);
    // Formata para AAAA-MM-DD
    return d.toISOString().split('T')[0];
}

// --- BUSCA INICIAL DE DADOS ---
const fetchData = async () => {
    let allEntidades = [];
    // Substitua pela sua URL correta se for diferente
    let nextUrl = 'http://127.0.0.1:8005/api/entidades/'; 

    // Opcional: ativar o loading se tiver a variável
    // loading.value = true; 

    while (nextUrl) {
        try {
            const response = await axios.get(nextUrl);
            allEntidades = allEntidades.concat(response.data.results);
            nextUrl = response.data.next;
        } catch (error) {
            console.error("Erro ao buscar uma página de entidades:", error);
            toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível carregar todas as entidades.', life: 3000 });
            nextUrl = null;
        }
    }

    entidades.value = allEntidades;
    // Opcional: desativar o loading
    // loading.value = false; 
};

onMounted(() => {
    // 1. Continua buscando a lista principal de entidades
    fetchData(); 

    // 2. ADICIONAMOS DE VOLTA a busca pela lista de categorias
    axios.get(`${API_BASE_URL}categorias/`)
        .then(response => {
            // A API de categorias também pode ser paginada, então usamos .results
            categorias.value = response.data.results || response.data;
        })
        .catch(error => {
            console.error("Erro ao buscar categorias:", error);
        });
});

watch(() => entidade.value.cep, (novoCep) => {
    // Remove qualquer caractere que não seja número
    const cepLimpo = (novoCep || '').replace(/\D/g, '');
    
    // Se o CEP tiver 8 dígitos, faz a busca
    if (cepLimpo.length === 8) {
        axios.get(`https://viacep.com.br/ws/${cepLimpo}/json/`)
            .then(response => {
                if (response.data.erro) {
                    toast.add({ severity: 'warn', summary: 'Aviso', detail: 'CEP não encontrado.', life: 3000 });
                } else {
                    // Preenche os campos com os dados retornados
                    entidade.value.logradouro = response.data.logradouro;
                    entidade.value.bairro = response.data.bairro;
                    // Futuramente, podemos adicionar cidade e estado também
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
    // Adiciona um novo objeto de contato em branco à lista
    entidade.value.contatos.push({
        tipo_contato: tipo, // 'T' para Telefone, 'E' para Email
        valor: '',
        descricao: ''
    });
};

const removeContato = (contatoParaRemover) => {
    // Filtra a lista, removendo o contato especificado
    entidade.value.contatos = entidade.value.contatos.filter(c => c !== contatoParaRemover);
    
    // Se o contato já existia no banco (tem um ID), precisamos deletá-lo via API
    if (contatoParaRemover.id) {
        axios.delete(`${API_BASE_URL}contatos/${contatoParaRemover.id}/`)
            .then(() => {
                toast.add({ severity: 'info', summary: 'Aviso', detail: 'Contato removido.', life: 2000 });
            })
            .catch(err => console.error("Erro ao deletar contato:", err));
    }
};

// --- FUNÇÕES DO CRUD ---
watch(entidade, (novoValor) => {
    // Se o interruptor "Doador" for ligado E o "Gestor" estiver desligado
    if (novoValor.eh_doador && !novoValor.eh_gestor) {
        // Procura pela categoria "Doador" na nossa lista de categorias
        const categoriaDoador = categorias.value.find(c => c.nome.toLowerCase() === 'doador');
        if (categoriaDoador) {
            // Define a categoria automaticamente
            novoValor.categoria = categoriaDoador;
        }
    }
}, { deep: true });

const openNew = () => {
    entidade.value = {
        data_cadastro: new Date(),
        eh_doador: false,
        eh_gestor: false,
        contatos: []
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
    if (!entidade.value.razao_social) return;

    // 1. Prepara o payload da Entidade, formatando datas
    let entidadePayload = { ...entidade.value };
    entidadePayload.data_cadastro = formatDateToAPI(entidadePayload.data_cadastro);
    entidadePayload.vigencia_de = formatDateToAPI(entidadePayload.vigencia_de);
    entidadePayload.vigencia_ate = formatDateToAPI(entidadePayload.vigencia_ate);
    
    // A API de entidade não lida com contatos, então removemos a lista do payload principal
    delete entidadePayload.contatos; 
    
    try {
        let savedEntidade;
        // 2. Salva a Entidade (Cria ou Atualiza)
        if (entidade.value.id) {
            const response = await axios.put(`${API_BASE_URL}entidades/${entidade.value.id}/`, entidadePayload);
            savedEntidade = response.data;
        } else {
            const response = await axios.post(`${API_BASE_URL}entidades/`, entidadePayload);
            savedEntidade = response.data;
        }

        // 3. Salva os Contatos
        const contatosPromises = entidade.value.contatos.map(contato => {
            const contatoPayload = { ...contato, entidade: savedEntidade.id };
            if (contato.id) {
                // Atualiza contato existente
                return axios.put(`${API_BASE_URL}contatos/${contato.id}/`, contatoPayload);
            } else {
                // Cria novo contato
                return axios.post(`${API_BASE_URL}contatos/`, contatoPayload);
            }
        });

        await Promise.all(contatosPromises);

        toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Entidade salva com sucesso!', life: 3000 });
        entidadeDialog.value = false;
        fetchData(); // Recarrega a lista da tabela

    } catch (err) {
        console.error("Erro ao salvar entidade:", err.response?.data || err);
        toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível salvar a entidade.', life: 3000 });
    }
};

const editEntidade = (prod) => {
    // Busca a versão mais recente da entidade, incluindo os contatos aninhados
    axios.get(`${API_BASE_URL}entidades/${prod.id}/`).then(response => {
        entidade.value = response.data;
        // Converte as strings de data para objetos Date que o Calendar entende
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
    axios.delete(`${API_BASE_URL}entidades/${entidade.value.id}/`)
        .then(() => {
            toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Entidade deletada!', life: 3000 });
            deleteEntidadeDialog.value = false;
            fetchData(); // Atualiza a lista
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
    const promises = selectedEntidades.value.map(ent => axios.delete(`${API_BASE_URL}entidades/${ent.id}/`));
    
    Promise.all(promises)
        .then(() => {
            toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Entidades deletadas!', life: 3000 });
            deleteEntidadesDialog.value = false;
            selectedEntidades.value = [];
            fetchData(); // Atualiza a lista
        })
        .catch(err => {
            console.error("Erro ao deletar selecionados:", err);
            toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível deletar as entidades selecionadas.', life: 3000 });
        });
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
                    <Button label="Exportar CSV" icon="pi pi-upload" class="p-button-help" @click="exportCSV($event)" />
                </template>
            </Toolbar>

            <DataTable
                ref="dt"
                v-model:selection="selectedEntidades"
                :value="entidades"
                dataKey="id"
                :paginator="true"
                :rows="10"
                :filters="filters"
                paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
                :rowsPerPageOptions="[5, 10, 25]"
                currentPageReportTemplate="Mostrando {first} a {last} de {totalRecords} entidades"
            >

                <template #header>
                    <div class="flex flex-wrap gap-2 items-center justify-between">
                        <h4 class="m-0">Gerenciar Entidades</h4>
                        <IconField>
                            <InputIcon>
                                <i class="pi pi-search" />
                            </InputIcon>
                            <InputText v-model="filters['global'].value" placeholder="Buscar..." />
                        </IconField>
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
                <Column field="cnpj" header="CNPJ" sortable style="min-width: 12rem"></Column>
                <Column header="Classificação" style="min-width: 12rem">
                    <template #body="slotProps">
                        <Tag v-if="slotProps.data.eh_doador" value="Doador" severity="success" class="mr-2"></Tag>
                        <Tag v-if="slotProps.data.eh_gestor" value="Gestor" severity="info"></Tag>
                    </template>
                </Column>
                <Column field="bairro" header="Bairro" sortable style="min-width: 16rem"></Column>
                <Column :exportable="false" style="min-width: 8rem">
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
                <Divider class="my-4" />
                <div class="grid grid-cols-12 gap-4">
                    <div class="col-span-8">
                        <label for="razao_social" class="block font-bold mb-3">Razão Social</label>
                        <InputText id="razao_social" v-model.trim="entidade.razao_social" required="true" autofocus :class="{'p-invalid': submitted && !entidade.razao_social}" fluid />
                        <small class="p-error" v-if="submitted && !entidade.razao_social">Razão Social é obrigatório.</small>
                    </div>
                    <div class="col-span-4">
                        <label for="cnpj" class="block font-bold mb-3">CNPJ</label>
                        <InputText id="cnpj" v-model.trim="entidade.cnpj" required="true" :class="{'p-invalid': submitted && !entidade.cnpj}" fluid />
                        <small class="p-error" v-if="submitted && !entidade.cnpj">CNPJ é obrigatório.</small>
                    </div>
                </div>
                <div class="grid grid-cols-12 gap-4">
                    <div class="col-span-8">
                        <label for="nome_fantasia" class="block font-bold mb-3">Nome Fantasia</label>
                        <InputText id="nome_fantasia" v-model.trim="entidade.nome_fantasia" fluid />
                    </div>
                    <div v-if="!entidade.eh_doador || entidade.eh_gestor" class="col-span-4">
                        <label for="categoria" class="block font-bold mb-3">Categoria</label>
                        <Dropdown id="categoria" v-model="entidade.categoria" :options="categorias" optionLabel="nome" placeholder="Selecione" fluid></Dropdown>
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
                <div v-for="(contato, index) in entidade.contatos" :key="index">
                    <div class="grid grid-cols-12 gap-4">
                        <div class="col-span-2">
                            <label for="tipo" class="block font-bold mb-3">Tipo</label>
                            <InputText id="tipo" :value="contato.tipo_contato === 'T' ? 'Telefone' : 'Email'" disabled fluid />
                        </div>
                        <div class="col-span-5">
                            <label for="contato-valor" class="block font-bold mb-3">Contato</label>
                            <InputText id="contato-valor" :value="contato.valor" fluid />
                        </div>
                        <div class="col-span-4">
                            <label for="contato-desc" class="block font-bold mb-3">Contato</label>
                            <InputText id="contato-desc" :value="contato.descricao" placeholder="Ex: Celular, Whatsapp" fluid />
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
                        <InputMask id="cep" v-model="entidade.cep" mask="99999-999" fluid />
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