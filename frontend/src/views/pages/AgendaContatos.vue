<script setup>
// 1. IMPORTAMOS SOMENTE A NOSSA INSTÂNCIA 'api'
import api from '@/services/api';
import { useAuthStore } from '@/store/auth';
import { ref, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import { FilterMatchMode } from '@primevue/core/api';

// --- ESTADO DO COMPONENTE ---
const authStore = useAuthStore();
const toast = useToast();
const aniversariantes = ref([]);
const agendaContatos = ref([]);
const loading = ref(true);
const dt = ref();
const filters = ref({
    global: { value: null, matchMode: FilterMatchMode.CONTAINS }
});

// 2. REMOVEMOS A URL FIXA
// const API_BASE_URL = 'http://127.0.0.1:8005/api/';

const pessoaDialog = ref(false);
const pessoa = ref({});
const submitted = ref(false);
const deletePessoaDialog = ref(false);
const pessoaParaDeletar = ref({});

// --- BUSCA DE DADOS ---
const fetchData = () => {
    loading.value = true;
    // 3. USAMOS 'api.get' COM CAMINHOS RELATIVOS
    const aniversariantesReq = api.get('/aniversariantes/');
    const agendaReq = api.get('/agenda/');

    Promise.all([aniversariantesReq, agendaReq])
        .then(([aniversariantesRes, agendaRes]) => {
            aniversariantes.value = aniversariantesRes.data;
            agendaContatos.value = agendaRes.data;
        })
        .catch(err => console.error("Erro ao buscar dados da agenda:", err))
        .finally(() => loading.value = false);
};

onMounted(fetchData);

// --- LÓGICA DO CRUD DE PESSOAS ---
const openNovaPessoa = () => {
    pessoa.value = {};
    submitted.value = false;
    pessoaDialog.value = true;
};

const editPessoa = (contato) => {
    // 4. USAMOS 'api.get' PARA BUSCAR A PESSOA
    api.get(`/pessoas/${contato.pessoa_id}/`).then(res => {
        pessoa.value = res.data;
        pessoaDialog.value = true;
    });
};

const savePessoa = () => {
    submitted.value = true;
    if (!pessoa.value.nome_completo) return;

    if (pessoa.value.id) { // Edição
        // 5. USAMOS 'api.put' PARA ATUALIZAR
        api.put(`/pessoas/${pessoa.value.id}/`, pessoa.value)
            .then(() => {
                toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Contato atualizado!', life: 3000 });
                pessoaDialog.value = false;
                fetchData();
            })
            .catch(() => toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível atualizar.', life: 3000 }));
    } else { // Criação
        // 6. USAMOS 'api.post' PARA CRIAR
        api.post('/pessoas/', pessoa.value)
            .then(() => {
                toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Contato criado!', life: 3000 });
                pessoaDialog.value = false;
                fetchData();
            })
            .catch(() => toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível criar.', life: 3000 }));
    }
};

const confirmDeletePessoa = (contatoParaDeletar) => {
    pessoaParaDeletar.value = contatoParaDeletar;
    deletePessoaDialog.value = true;
};

const deletePessoaConfirmado = () => {
    // 7. USAMOS 'api.delete' PARA DELETAR
    api.delete(`/pessoas/${pessoaParaDeletar.value.pessoa_id}/`)
        .then(() => {
            toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Contato deletado!', life: 3000 });
            deletePessoaDialog.value = false;
            fetchData();
        })
        .catch(err => {
            console.error("Erro ao deletar:", err);
            toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível deletar. Verifique se a pessoa tem outros vínculos ativos.', life: 5000 });
            deletePessoaDialog.value = false;
        });
};

// --- FUNÇÃO DE EXPORTAR CSV ---
const exportCSV = () => {
    dt.value.exportCSV();
};
</script>

<template>
    <div>
        <Card class="mb-6">
            <template #title>
                <div>
                    <i class="pi pi-gift mr-2 text-2xl text-primary"></i>
                    <span>Aniversariantes do Dia</span>
                </div>
            </template>
            <template #content>
                <div v-if="aniversariantes.length > 0">
                    <div v-for="aniv in aniversariantes" :key="aniv.id" class="mb-3">
                        <Avatar icon="pi pi-user" class="mr-2" />
                        <span>{{ aniv.nome_completo }}</span>
                    </div>
                </div>
                <div v-else>
                    <p>Nenhum aniversariante hoje.</p>
                </div>
            </template>
        </Card>

        <div class="card">
            <DataTable
                ref="dt"
                :value="agendaContatos"
                :loading="loading"
                paginator
                :rows="10"
                responsiveLayout="scroll"
                dataKey="id_vinculo"  v-model:filters="filters"
                :globalFilterFields="['nome_completo', 'entidade_nome', 'cargo', 'telefone', 'email']"
            >
                <template #header>
                    <div class="flex flex-wrap gap-2 items-center justify-between">
                        <h4 class="m-0">Agenda de Contatos</h4>
                        <div class="flex gap-2">
                            <Button label="Exportar CSV" icon="pi pi-upload" class="p-button-help mr-2" @click="exportCSV" />
                            <IconField>
                                <InputIcon>
                                    <i class="pi pi-search" />
                                </InputIcon>
                                <InputText v-model="filters['global'].value" placeholder="Buscar..." />
                            </IconField>
                        </div>
                    </div>
                </template>
                    <template #empty> Nenhum contato encontrado. </template>

                <Column field="nome_completo" header="Nome" sortable></Column>
                <Column field="telefone" header="Telefone"></Column>
                <Column field="email" header="Email"></Column>
                <Column field="entidade_nome" header="Vínculo (Entidade)" sortable>
                    <template #body="slotProps">
                        <router-link :to="`/entidades/${slotProps.data.entidade_id}`">{{ slotProps.data.entidade_nome }}</router-link>
                    </template>
                </Column>
                <Column field="cargo" header="Cargo/Tipo" sortable>
                    <template #body="slotProps">
                        <Tag :value="slotProps.data.tipo_vinculo" :severity="slotProps.data.tipo_vinculo === 'Responsável' ? 'info' : 'success'" class="mr-2" />
                        <span v-if="slotProps.data.cargo">{{ slotProps.data.cargo }}</span>
                    </template>
                </Column>
                <Column header="Ações" style="width: 12rem">
                    <template #body="slotProps">
                        <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editPessoa(slotProps.data)" />
                        <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmDeletePessoa(slotProps.data)" />
                    </template>
                </Column>
            </DataTable>
        </div>
    </div>

    <Dialog v-model:visible="pessoaDialog" :style="{ width: '50rem' }" header="Dados do Contato" :modal="true" class="p-fluid">
        <div class="flex flex-col gap-6">
            <div>
                <label for="nome_completo" class="block font-bold mb-3">Nome Completo</label>
                <InputText id="nome_completo" v-model.trim="pessoa.nome_completo" required="true" autofocus :class="{'p-invalid': submitted && !pessoa.nome_completo}" fluid />
                <small class="p-error" v-if="submitted && !pessoa.nome_completo">Nome é obrigatório.</small>
            </div>
            <div class="grid grid-cols-12 gap-4">
                <div class="col-span-6">
                    <label for="cpf" class="block font-bold mb-3">CPF</label>
                    <InputText id="cpf" v-model.trim="pessoa.cpf" fluid />
                </div>
                <div class="col-span-6">
                    <label for="data_nascimento" class="block font-bold mb-3">Data de Nascimento</label>
                    <Calendar id="data_nascimento" v-model="pessoa.data_nascimento" dateFormat="dd/mm/yy" fluid />
                </div>
            </div>
            <div class="grid grid-cols-12 gap-4">
                <div class="col-span-4">
                    <label for="telefone" class="block font-bold mb-3">Telefone</label>
                    <InputText id="telefone" v-model.trim="pessoa.telefone" fluid />
                </div>
                <div class="col-span-8">
                    <label for="email" class="block font-bold mb-3">Email</label>
                    <InputText id="email" v-model.trim="pessoa.email" fluid />
                </div>
            </div>
        </div>
        <template #footer>
            <Button label="Cancelar" icon="pi pi-times" text @click="pessoaDialog = false" />
            <Button label="Salvar" icon="pi pi-check" @click="savePessoa" />
        </template>
    </Dialog>

    <Dialog v-model:visible="deletePessoaDialog" :style="{ width: '450px' }" header="Confirmar Exclusão" :modal="true">
        <div class="flex align-items-center">
            <i class="pi pi-exclamation-triangle mr-3" style="font-size: 2rem" />
            <div v-if="pessoaParaDeletar">
                <span>Tem certeza que deseja excluir <b>{{ pessoaParaDeletar.nome_completo }}</b>?</span>
                <p class="mt-2 text-sm text-500">Atenção: Esta ação removerá a pessoa de todo o sistema, incluindo de todos os seus vínculos.</p>
            </div>
        </div>
        <template #footer>
            <Button label="Não" icon="pi pi-times" text @click="deletePessoaDialog = false" />
            <Button label="Sim, Excluir" icon="pi pi-check" class="p-button-danger" @click="deletePessoaConfirmado" />
        </template>
    </Dialog>
</template>