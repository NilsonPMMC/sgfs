<script setup>
import { useAuthStore } from '@/store/auth';
import { ref, onMounted } from 'vue';
import axios from 'axios';

const authStore = useAuthStore();
const itens = ref([]);
const loading = ref(true);
const API_URL = 'http://127.0.0.1:8005/api/itens/';

const fetchData = async () => {
    loading.value = true;
    let allItens = [];
    let nextUrl = API_URL;

    while (nextUrl) {
        try {
            const response = await axios.get(nextUrl);
            allItens = allItens.concat(response.data.results);
            nextUrl = response.data.next;
        } catch (error) {
            console.error("Erro ao buscar itens:", error);
            nextUrl = null;
        }
    }
    itens.value = allItens;
    loading.value = false;
};

onMounted(fetchData);

const getEstoqueSeverity = (item) => {
    const estoque = item.estoque_atual || 0;
    if (estoque === 0) return 'danger';
    if (estoque > 0 && estoque <= 10) return 'warning';
    return 'success';
};
</script>

<template>
    <div class="card">
        <DataTable :value="itens" :loading="loading" paginator :rows="10" responsiveLayout="scroll">
            <template #header>
                <div class="flex justify-content-between align-items-center">
                    <h5 class="m-0">Controle de Estoque</h5>
                    </div>
            </template>
            <template #empty> Nenhum item encontrado. </template>

            <Column field="nome" header="Item" sortable></Column>
            <Column field="categoria.nome" header="Categoria" sortable></Column>
            <Column field="unidade_medida" header="Unidade"></Column>
            <Column field="estoque_atual" header="Estoque Atual" sortable>
                <template #body="slotProps">
                    <Tag :severity="getEstoqueSeverity(slotProps.data)" class="text-lg">
                        {{ slotProps.data.estoque_atual || 0 }}
                    </Tag>
                </template>
            </Column>
        </DataTable>
    </div>
</template>