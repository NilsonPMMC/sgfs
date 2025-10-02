<script setup>
import { useAuthStore } from '@/store/auth';
import { ref, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import axios from 'axios';
import { FilterMatchMode } from '@primevue/core/api';

const authStore = useAuthStore();
const toast = useToast();
const kits = ref([]);
const kitDialog = ref(false);
const kit = ref({ itens_do_kit: [] });
const submitted = ref(false);
const itensEncontrados = ref([]); // Para a busca de itens
const API_URL = 'http://127.0.0.1:8005/api/kits/';

const deleteKitDialog = ref(false);
const kitParaDeletar = ref({});

const dt = ref();
const filters = ref({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS }
});
const exportCSV = () => dt.value.exportCSV();

const getStockClass = (item) => {
    const estoque = item.estoque_atual || 0;
    if (estoque === 0) return 'text-red-500'; // Vermelho para "sem estoque"
    if (estoque > 0 && estoque <= 10) return 'text-orange-500'; // Laranja para "estoque baixo"
    return 'text-green-500'; // Verde para "em estoque"
};

const fetchData = async () => {
    let allKits = [];
    let nextUrl = API_URL;

    while (nextUrl) {
        try {
            const response = await axios.get(nextUrl);
            allKits = allKits.concat(response.data.results); // Pega os dados de dentro de 'results'
            nextUrl = response.data.next;
        } catch (error) {
            console.error("Erro ao buscar kits:", error);
            nextUrl = null;
        }
    }
    kits.value = allKits;
};
onMounted(fetchData);

const openNew = () => {
    kit.value = { itens_do_kit: [{ item: null, quantidade: 1 }] };
    submitted.value = false;
    kitDialog.value = true;
};

const editKit = (kitParaEditar) => {
    // A API retorna o item completo, mas para salvar precisamos só do item_id.
    // O backend espera { "item_id": X, "quantidade": Y }
    // Vamos garantir que nosso objeto de edição esteja nesse formato.
    kit.value = {
        ...kitParaEditar,
        itens_do_kit: kitParaEditar.itens_do_kit.map(ik => ({
            item: ik.item, // Mantemos o objeto completo para exibição no AutoComplete
            quantidade: ik.quantidade,
        }))
    };
    kitDialog.value = true;
};

const saveKit = () => {
    submitted.value = true;
    if (!kit.value.nome) return;

    const payload = {
        ...kit.value,
        itens_do_kit: kit.value.itens_do_kit.map(ik => ({
            item_id: ik.item.id, // Enviamos apenas o ID do item
            quantidade: ik.quantidade,
        }))
    };

    const request = kit.value.id
        ? axios.put(`${API_URL}${kit.value.id}/`, payload)
        : axios.post(API_URL, payload);

    request.then(() => {
        toast.add({ severity: 'success', summary: 'Sucesso', detail: `Kit salvo com sucesso!`, life: 3000 });
        kitDialog.value = false;
        fetchData();
    }).catch(err => {
        console.error("Erro ao salvar kit:", err.response?.data);
        toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível salvar o kit.', life: 3000 });
    });
};

const confirmDeleteKit = (kitParaDeletar) => {
    kit.value = kitParaDeletar; // Reutilizando a variável 'kit' para a mensagem
    deleteKitDialog.value = true;
};

const deleteKit = () => {
    axios.delete(`${API_URL}${kit.value.id}/`)
        .then(() => {
            toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Kit deletado com sucesso!', life: 3000 });
            deleteKitDialog.value = false;
            fetchData(); // Atualiza a lista de kits
        })
        .catch(err => {
            console.error("Erro ao deletar kit:", err.response?.data);
            toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível deletar o kit.', life: 3000 });
        });
};

const searchItem = (event) => {
    axios.get(`http://127.0.0.1:8005/api/itens/?search=${event.query}`)
        .then(response => (itensEncontrados.value = response.data.results));
};

const adicionarItemAoKit = () => {
    kit.value.itens_do_kit.push({ item: null, quantidade: 1 });
};

const removerItemDoKit = (index) => {
    kit.value.itens_do_kit.splice(index, 1);
};
</script>

<template>
    <div class="card">
        <Toast />
        <Toolbar class="mb-4">
            <template #start>
                <Button label="Novo Kit" icon="pi pi-plus" class="p-button-success" @click="openNew" />
            </template>
            <template #end>
                <Button label="Exportar CSV" icon="pi pi-upload" class="p-button-help" @click="exportCSV($event)" />
            </template>
        </Toolbar>
        <DataTable
            ref="dt"
            :value="kits"
            dataKey="id"
            :paginator="true"
            :rows="10"
            v-model:filters="filters"
            :globalFilterFields="['nome', 'descricao']"
            paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
            :rowsPerPageOptions="[5, 10, 25]"
            currentPageReportTemplate="Mostrando {first} a {last} de {totalRecords} kits"
        >
            <template #header>
                <div class="flex flex-wrap gap-2 items-center justify-between">
                    <h4 class="m-0">Gerenciar Kits</h4>
                    <IconField>
                        <InputIcon>
                            <i class="pi pi-search" />
                        </InputIcon>
                        <InputText v-model="filters['global'].value" placeholder="Buscar..." />
                    </IconField>
                </div>
            </template>
            <template #empty> Nenhum kit encontrado. </template>
            <Column field="nome" header="Nome do Kit" sortable></Column>
            <Column field="descricao" header="Descrição"></Column>
            <Column header="Nº de Itens">
                <template #body="slotProps">
                    {{ slotProps.data.itens_do_kit.length }}
                </template>
            </Column>
            <Column :exportable="false" style="min-width: 8rem">
                <template #body="slotProps">
                    <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editKit(slotProps.data)" />
                    <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmDeleteKit(slotProps.data)" />
                </template>
            </Column>
        </DataTable>
    </div>

    <Dialog v-model:visible="kitDialog" :style="{ width: '50rem' }" header="Detalhes do Kit" :modal="true" class="p-fluid">
        <div class="flex flex-col">
            <div class="mb-3">
                <label for="nome" class="block font-bold mb-3">Nome do Kit</label>
                <InputText id="nome" v-model.trim="kit.nome" required="true" autofocus fluid />
            </div>
            <div>
                <label for="descricao" class="block font-bold mb-3">Descrição</label>
                <Textarea id="descricao" v-model="kit.descricao" rows="3" fluid />
            </div>

            <Divider class="my-4" />

            <h5>Itens do Kit</h5>
            <div v-for="(itemDoKit, index) in kit.itens_do_kit" :key="index" class="grid grid-cols-12 gap-4 mb-3">
                <div class="col-span-8">
                    <AutoComplete v-model="itemDoKit.item" :suggestions="itensEncontrados" @complete="searchItem" optionLabel="nome" placeholder="Busque um item..." dropdown fluid>
                        <template #option="slotProps">
                            <div>
                                <span class="mr-3">{{ slotProps.option.nome }}</span>
                                <span class="font-bold text-lg" :class="getStockClass(slotProps.option)">
                                    {{ slotProps.option.estoque_atual || 0 }} {{ slotProps.option.unidade_medida }}
                                </span>
                            </div>
                        </template>
                    </AutoComplete>
                </div>
                <div class="col-span-3">
                    <InputNumber v-model="itemDoKit.quantidade" mode="decimal" :min="1" fluid />
                </div>
                <div class="col-span-1">
                    <Button icon="pi pi-trash" class="p-button-danger" @click="removerItemDoKit(index)" />
                </div>
            </div>
            <Button label="Adicionar Item ao Kit" icon="pi pi-plus" class="p-button-text" @click="adicionarItemAoKit" />
        </div>
        <template #footer>
            <Button label="Cancelar" icon="pi pi-times" text @click="kitDialog = false" />
            <Button label="Salvar" icon="pi pi-check" @click="saveKit" />
        </template>
    </Dialog>

    <Dialog v-model:visible="deleteKitDialog" :style="{ width: '450px' }" header="Confirmar Exclusão" :modal="true">
        <div class="flex align-items-center">
            <i class="pi pi-exclamation-triangle mr-3" style="font-size: 2rem" />
            <span v-if="kit">Tem certeza que deseja deletar o kit <b>{{ kit.nome }}</b>?</span>
        </div>
        <template #footer>
            <Button label="Não" icon="pi pi-times" text @click="deleteKitDialog = false" />
            <Button label="Sim, Excluir" icon="pi pi-check" class="p-button-danger" @click="deleteKit" />
        </template>
    </Dialog>
</template>