<script setup>
// 1. IMPORTAMOS APENAS A NOSSA INSTÂNCIA 'api'
import api from '@/services/api';
import { useAuthStore } from '@/store/auth';
import { ref, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import { FilterMatchMode } from '@primevue/core/api';
import Tag from 'primevue/tag';

// --- ESTADO DO COMPONENTE ---
const authStore = useAuthStore();
const toast = useToast();
const dt = ref();
const itens = ref([]);
const itemDialog = ref(false);
const deleteItemDialog = ref(false);
const item = ref({});
const submitted = ref(false);
const categorias = ref([]);
const loading = ref(true);
const filters = ref({ global: { value: null, matchMode: FilterMatchMode.CONTAINS } });

// 2. REMOVEMOS A URL FIXA
// const API_BASE_URL = 'http://127.0.0.1:8005/api/';

const movimentacaoDialog = ref(false);
const tipoMovimentacao = ref('E');
const movimentacao = ref({ item: null, quantidade: 1, observacao: '' });

// --- BUSCA DE DADOS ---
const fetchData = async () => {
    loading.value = true;
    let allItens = [];
    let nextUrl = '/itens/'; // A primeira chamada é relativa e usará o baseURL

    while (nextUrl) {
        try {
            const response = await api.get(nextUrl);
            allItens = allItens.concat(response.data.results);
            // CORREÇÃO: Usamos a URL completa que a API nos dá para as próximas páginas
            nextUrl = response.data.next; 
        } catch (error) {
            console.error("Erro ao buscar uma página de itens:", error);
            toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível carregar todos os itens.', life: 3000 });
            nextUrl = null;
        }
    }

    itens.value = allItens;
    loading.value = false;

    // Esta parte continua igual e correta
    api.get('/categorias-itens/').then(response => {
        categorias.value = Array.isArray(response.data) ? response.data : response.data.results;
    });
};

onMounted(fetchData);

// --- MOVIMENTAÇÕES DE ESTOQUE ---
const openMovimentacaoDialog = (tipo) => {
    tipoMovimentacao.value = tipo;
    movimentacao.value = { item: null, quantidade: 1, observacao: '' };
    movimentacaoDialog.value = true;
};

const saveMovimentacao = async () => {
    if (!movimentacao.value.item || movimentacao.value.quantidade <= 0) {
        toast.add({ severity: 'warn', summary: 'Atenção', detail: 'Selecione um item e informe a quantidade.', life: 3000 });
        return;
    }

    const payload = {
        item: movimentacao.value.item.id,
        tipo_movimento: tipoMovimentacao.value,
        quantidade: movimentacao.value.quantidade,
        observacao: movimentacao.value.observacao || '',
    };

    try {
        // 5. USAMOS 'api.post' PARA SALVAR A MOVIMENTAÇÃO
        await api.post('/movimentacoes-estoque/', payload);
        toast.add({
            severity: 'success',
            summary: 'Movimentação registrada',
            detail: tipoMovimentacao.value === 'E' ? 'Entrada adicionada ao estoque.' : 'Saída registrada.',
            life: 3000
        });
        movimentacaoDialog.value = false;
        fetchData();
    } catch (error) {
        console.error('Erro ao registrar movimentação:', error);
        toast.add({ severity: 'error', summary: 'Erro', detail: 'Falha ao registrar movimentação.', life: 3000 });
    }
};

// --- CRUD DE ITENS ---
const openNew = () => {
    item.value = {};
    submitted.value = false;
    itemDialog.value = true;
};

const hideDialog = () => {
    itemDialog.value = false;
    submitted.value = false;
};

const saveItem = () => {
    submitted.value = true;
    if (!item.value.nome) return;

    let payload = { ...item.value };
    if (payload.categoria && typeof payload.categoria === 'object') {
        payload.categoria_id = payload.categoria.id;
    }
    delete payload.categoria;
    
    if (item.value.id) {
        // 6. USAMOS 'api.put' PARA ATUALIZAR O ITEM
        api.put(`/itens/${item.value.id}/`, payload)
            .then(() => {
                toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Item atualizado!', life: 3000 });
                itemDialog.value = false;
                fetchData();
            })
            .catch(() => toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível atualizar.', life: 3000 }));
    } else {
        // 7. USAMOS 'api.post' PARA CRIAR O ITEM
        api.post('/itens/', payload)
            .then(() => {
                toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Item criado!', life: 3000 });
                itemDialog.value = false;
                fetchData();
            })
            .catch(() => toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível criar.', life: 3000 }));
    }
};

const editItem = (prod) => {
    item.value = { ...prod };
    itemDialog.value = true;
};

const confirmDeleteItem = (prod) => {
    item.value = prod;
    deleteItemDialog.value = true;
};

const deleteItem = () => {
    // 8. USAMOS 'api.delete' PARA DELETAR O ITEM
    api.delete(`/itens/${item.value.id}/`)
        .then(() => {
            toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Item deletado!', life: 3000 });
            deleteItemDialog.value = false;
            fetchData();
        })
        .catch(() => toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível deletar o item.', life: 3000 }));
};

const exportCSV = () => dt.value.exportCSV();
</script>

<template>
    <div>
        <Toast />
        <div class="card">
            <Toolbar class="mb-4">
                <template #start>
                    <Button label="Novo Item" icon="pi pi-plus" class="p-button-success mr-3" @click="openNew" />
                    <Button label="Entrada Manual" icon="pi pi-arrow-down" class="p-button-secondary mr-3" @click="openMovimentacaoDialog('E')" />
                    <Button label="Saída Manual" icon="pi pi-arrow-up" class="p-button-help mr-3" @click="openMovimentacaoDialog('S')" />
                </template>
                <template #end>
                    <Button label="Exportar CSV" icon="pi pi-upload" class="p-button-help" @click="exportCSV($event)" />
                </template>
            </Toolbar>

            <DataTable
                ref="dt"
                :value="itens"
                dataKey="id"
                :paginator="true"
                :rows="10"
                v-model:filters="filters"
                :globalFilterFields="['nome', 'categoria.nome', 'unidade_medida']"
                paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
                :rowsPerPageOptions="[5, 10, 25]"
                currentPageReportTemplate="Mostrando {first} a {last} de {totalRecords} itens"
                :loading="loading"
            >
                <template #header>
                    <div class="flex flex-wrap gap-2 items-center justify-between">
                        <h4 class="m-0">Gerenciar Itens</h4>
                        <IconField>
                            <InputIcon>
                                <i class="pi pi-search" />
                            </InputIcon>
                            <InputText v-model="filters['global'].value" placeholder="Buscar..." />
                        </IconField>
                    </div>
                </template>
                <Column field="nome" header="Item" sortable></Column>
                <Column field="categoria.nome" header="Categoria" sortable></Column>
                <Column field="estoque_atual" header="Estoque Atual" sortable>
                    <template #body="slotProps">
                        <Tag :severity="slotProps.data.estoque_atual > 0 ? 'success' : 'danger'" class="text-lg font-bold">
                            {{ slotProps.data.estoque_atual || 0 }} {{ slotProps.data.unidade_medida }}
                        </Tag>
                    </template>
                </Column>
                <Column field="unidade_medida" header="Unidade" sortable></Column>
                <Column :exportable="false" header="Ações" style="min-width: 8rem">
                    <template #body="slotProps">
                        <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editItem(slotProps.data)" />
                        <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmDeleteItem(slotProps.data)" />
                    </template>
                </Column>
            </DataTable>
        </div>

        <Dialog v-model:visible="itemDialog" :style="{ width: '50rem' }" header="Detalhes do Item" :modal="true">
            <div class="flex flex-col gap-6">
                <div>
                    <label for="nome" class="block font-bold mb-3">Nome do Item</label>
                    <InputText id="nome" v-model.trim="item.nome" required="true" autofocus :class="{ 'p-invalid': submitted && !item.nome }" fluid />
                    <small class="p-error" v-if="submitted && !item.nome">Nome é obrigatório.</small>
                </div>
                <div class="grid grid-cols-12 gap-4">
                    <div class="col-span-8">
                        <label for="categoria" class="block font-bold mb-3">Categoria</label>
                        <Dropdown id="categoria" v-model="item.categoria" :options="categorias" optionLabel="nome" placeholder="Selecione uma categoria" fluid></Dropdown>
                    </div>
                    <div class="col-span-4">
                        <label for="unidade_medida" class="block font-bold mb-3">Unidade</label>
                        <InputText id="unidade_medida" v-model.trim="item.unidade_medida" placeholder="Ex: un, kg" fluid />
                    </div>
                </div>
                <div>
                    <label for="descricao" class="block font-bold mb-3">Descrição</label>
                    <Textarea id="descricao" v-model="item.descricao" rows="3" fluid />
                </div>
            </div>
            <template #footer>
                <Button label="Cancelar" icon="pi pi-times" text @click="hideDialog" />
                <Button label="Salvar" icon="pi pi-check" @click="saveItem" />
            </template>
        </Dialog>

        <Dialog v-model:visible="deleteItemDialog" :style="{ width: '450px' }" header="Confirmar" :modal="true">
            <div class="flex align-items-center">
                <i class="pi pi-exclamation-triangle mr-3" style="font-size: 2rem" />
                <span v-if="item">Tem certeza que deseja deletar <b>{{ item.nome }}</b>?</span>
            </div>
            <template #footer>
                <Button label="Não" icon="pi pi-times" text @click="deleteItemDialog = false" />
                <Button label="Sim" icon="pi pi-check" @click="deleteItem" />
            </template>
        </Dialog>

        <Dialog v-model:visible="movimentacaoDialog" :style="{ width: '40rem' }" modal>
            <template #header>
                <h4 class="m-0">
                    {{ tipoMovimentacao === 'E' ? 'Registrar Entrada Manual' : 'Registrar Saída Manual' }}
                </h4>
            </template>

            <div class="flex flex-col gap-5">
                <div>
                    <label class="block font-bold mb-3">Item</label>
                    <Dropdown v-model="movimentacao.item" :options="itens" optionLabel="nome" placeholder="Selecione o item" filter fluid />
                </div>

                <div>
                    <label class="block font-bold mb-3">Quantidade</label>
                    <InputNumber v-model="movimentacao.quantidade" mode="decimal" :min="1" fluid />
                </div>

                <div>
                    <label class="block font-bold mb-3">Observação (opcional)</label>
                    <Textarea v-model="movimentacao.observacao" rows="2" fluid />
                </div>
            </div>

            <template #footer>
                <Button label="Cancelar" icon="pi pi-times" text @click="movimentacaoDialog = false" />
                <Button
                    :label="tipoMovimentacao === 'E' ? 'Registrar Entrada' : 'Registrar Saída'"
                    icon="pi pi-check"
                    @click="saveMovimentacao"
                />
            </template>
        </Dialog>

    </div>
</template>