<script setup>
// 1. IMPORTAMOS 'api' PARA NOSSA API E MANTEMOS 'axios' PARA O VIACEP
import api from '@/services/api';
import axios from 'axios'; // Necessário para o ViaCEP
import { useAuthStore } from '@/store/auth';
import { ref, onMounted, watch, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';

import Divider from 'primevue/divider';
import Tag from 'primevue/tag';
import Message from 'primevue/message';
import Fieldset from 'primevue/fieldset';
import Popover from 'primevue/popover';
import Tabs from 'primevue/tabs';
import TabList from 'primevue/tablist';
import Tab from 'primevue/tab';
import TabPanels from 'primevue/tabpanels';
import TabPanel from 'primevue/tabpanel';

// --- ESTADO DO COMPONENTE ---
const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();
const toast = useToast();
const entidade = ref(null);
const loading = ref(true);

// 2. REMOVEMOS A URL FIXA
// const API_BASE_URL = 'http://127.0.0.1:8005/api/';

const entidadeDialog = ref(false);
const entidadeParaEditar = ref({ contatos: [] });
const categorias = ref([]);
const submitted = ref(false);

const responsavelDialog = ref(false);
const responsavel = ref({});
const isEditMode = ref(false);

const deleteVinculoDialog = ref(false);
const vinculoParaDeletar = ref({});

const beneficiadoDialog = ref(false);
const beneficiado = ref({});
const isBeneficiadoEditMode = ref(false);

const historicoAtendimentos = ref([]);
const historicoDoacoes = ref([]);

const op = ref();
const overlayItems = ref([]);
const toggleError = ref(false);
const activeTabValue = ref();

// --- FUNÇÕES AUXILIARES ---

/**
 * Converte uma string de data (ex: "2023-10-27" OU "27/10/2023")
 * para um objeto Date local de forma segura, evitando erros de NaN e fuso horário.
 */
const parseAPIDate = (dateString) => {
    if (!dateString || typeof dateString !== 'string') return null;

    // Tira a parte da hora, se houver
    const dateOnlyString = dateString.split('T')[0];
    
    let parts;
    let year, monthIndex, day;

    if (dateOnlyString.includes('-')) {
        // Formato 1: "YYYY-MM-DD"
        parts = dateOnlyString.split('-');
        if (parts.length === 3) {
            year = parseInt(parts[0], 10);
            monthIndex = parseInt(parts[1], 10) - 1; // Mês é 0-indexado
            day = parseInt(parts[2], 10);
        }
    } else if (dateOnlyString.includes('/')) {
        // Formato 2: "DD/MM/YYYY"
        parts = dateOnlyString.split('/');
        if (parts.length === 3) {
            day = parseInt(parts[0], 10);
            monthIndex = parseInt(parts[1], 10) - 1; // Mês é 0-indexado
            year = parseInt(parts[2], 10);
        }
    }

    // Verifica se os valores são válidos
    if (!isNaN(year) && !isNaN(monthIndex) && !isNaN(day)) {
        // Validação extra para anos curtos (ex: "25" ao invés de "2025")
        if (year < 100) {
             year += 2000; // Suposição simples
        }
        // Cria a data na hora local
        return new Date(year, monthIndex, day);
    }
    
    // Fallback para o caso de um formato que o JS já entenda (ex: ISO completa)
    const dt = new Date(dateString);
    if (!isNaN(dt.getTime())) return dt;

    console.warn('Falha ao fazer parse da data:', dateString);
    return null; // Retorna null se tudo falhar
};

// Função para formatar a data de AAAA-MM-DD para DD/MM/AAAA
const formatarData = (dataString) => {
    // Se a data não existir, retorna um texto padrão
    if (!dataString) {
        return 'Não informada';
    }
    // Divide a string da data e remonta no formato brasileiro
    const [ano, mes, dia] = dataString.split('-');
    return `${dia}/${mes}/${ano}`;
};

const formatDateToAPI = (date) => {
    if (!date) return null;
    const d = new Date(date);
    return d.toISOString().split('T')[0];
}
const contatoStats = computed(() => {
  const lista = entidadeParaEditar.value?.contatos || [];
  return {
    telefones: lista.filter(c => c.tipo_contato === 'T').length,
    emails:    lista.filter(c => c.tipo_contato === 'E').length,
  };
});
const toggleOverlay = (event, items) => {
    overlayItems.value = items;
    op.value.toggle(event);
};
const onlyDigits = (s) => (s || '').replace(/\D/g, '');
const maskDoc = (s) => {
  const d = onlyDigits(s);
  if (!d) return '';
  if (d.length > 11) {
    return d.replace(
      /^(\d{0,2})(\d{0,3})(\d{0,3})(\d{0,4})(\d{0,2}).*$/,
      (_, a,b,c,e,f) => [a, b && '.'+b, c && '.'+c, e && '/'+e, f && '-'+f]
        .filter(Boolean).join('')
    );
  }
  return d.replace(
    /^(\d{0,3})(\d{0,3})(\d{0,3})(\d{0,2}).*$/,
    (_, a,b,c,dig) => [a, b && '.'+b, c && '.'+c, dig && '-'+dig]
      .filter(Boolean).join('')
  );
};
const maskPhone = (s) => {
  const d = onlyDigits(s).slice(0, 11);
  if (!d) return '';
  if (d.length <= 10) {
    return d.replace(
      /^(\d{0,2})(\d{0,4})(\d{0,4}).*$/,
      (_, a,b,c) => [a && `(${a})`, b && ' '+b, c && '-'+c]
        .filter(Boolean).join('')
    );
  }
  return d.replace(
    /^(\d{0,2})(\d{0,5})(\d{0,4}).*$/,
    (_, a,b,c) => [a && `(${a})`, b && ' '+b, c && '-'+c]
      .filter(Boolean).join('')
  );
};
const isValidEmail = (s) => !!s && /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(s);
const onDocInput = (e) => { entidadeParaEditar.value.documento = onlyDigits(e.target.value).slice(0, 14); };
const onPhoneInput = (contato, e) => { contato.valor = onlyDigits(e.target.value).slice(0, 11); };

// --- NAVEGAÇÃO E FORMATAÇÃO --- (Nenhuma alteração aqui)
const goToRegistrarEntrada = () => {
    if (!entidade.value) return;
    router.push({
        name: 'EntradaDoacao',
        query: {
            doador_id: entidade.value.id,
            doador_nome: entidade.value.nome_fantasia || entidade.value.razao_social || entidade.value.nome,
            content_type_id: entidade.value.content_type_id || null
        }
    });
};
const goToRegistrarSaida = () => {
    if (!entidade.value) return;
    router.push({
        name: 'SaidaDoacao',
        query: {
            entidade_id: entidade.value.id,
            entidade_nome: entidade.value.nome_fantasia || entidade.value.nome || entidade.value.razao_social
        }
    });
};
const editarEntrada = (registro) => {
    if (!registro?.id) return;
    router.push({ name: 'EditarEntradaDoacao', params: { id: registro.id } });
};
const editarSaida = (registro) => {
    if (!registro?.id) return;
    router.push({ name: 'EditarSaidaDoacao', params: { id: registro.id } });
};
const formatarMesAno = (dataString) => {
    const data = parseAPIDate(dataString);
    if (!data) return 'Data inválida';

    return data.toLocaleString('pt-BR', { month: 'long', year: 'numeric' });
};
const formatarDia = (dataString) => {
    const data = parseAPIDate(dataString);
    if (!data) return '?';

    return data.getDate();
};

// --- BUSCA DE DADOS ---
const fetchEntidadeData = () => {
    loading.value = true;
    const entidadeId = route.params.id;

    // 3. USAMOS 'api' PARA BUSCAR A ENTIDADE
    api.get(`/entidades/${entidadeId}/`)
        .then(response => {
            entidade.value = response.data;
            if (entidade.value.eh_gestor) {
                activeTabValue.value = 'entregas';
            } else if (entidade.value.eh_doador) {
                activeTabValue.value = 'entradas';
            } else {
                activeTabValue.value = 'responsaveis';
            }
            if (entidade.value.eh_gestor) {
                fetchAtendimentos(entidadeId);
            }
            if (entidade.value.eh_doador) {
                fetchDoacoes(entidadeId);
            }
        })
        .catch(error => console.error("Erro ao buscar detalhes da entidade:", error))
        .finally(() => loading.value = false);
};

const fetchAtendimentos = (entidadeId) => {
    // 4. USAMOS 'api' PARA BUSCAR ATENDIMENTOS
    api.get(`/entidades/${entidadeId}/atendimentos/`)
        .then(response => {
            historicoAtendimentos.value = response.data;
        });
};

const fetchDoacoes = (entidadeId) => {
    // 5. USAMOS 'api' PARA BUSCAR DOAÇÕES
    api.get(`/entidades/${entidadeId}/doacoes/`)
        .then(response => {
            historicoDoacoes.value = response.data;
        });
};

const fetchCategorias = () => {
    // 6. USAMOS 'api' PARA BUSCAR CATEGORIAS
    api.get('/categorias/').then((response) => {
        categorias.value = response.data.results;
    });
};

onMounted(() => {
    fetchEntidadeData();
    fetchCategorias();
});

// A CHAMADA PARA O VIACEP CONTINUA USANDO 'axios' POR SER EXTERNA
watch(() => entidadeParaEditar.value.cep, (novoCep) => {
    const cepLimpo = (novoCep || '').replace(/\D/g, '');
    if (cepLimpo.length === 8) {
        axios.get(`https://viacep.com.br/ws/${cepLimpo}/json/`)
            .then(response => {
                if (response.data.erro) {
                    toast.add({ severity: 'warn', summary: 'Aviso', detail: 'CEP não encontrado.', life: 3000 });
                } else {
                    entidadeParaEditar.value.logradouro = response.data.logradouro;
                    entidadeParaEditar.value.bairro = response.data.bairro;
                }
            })
            .catch(error => {
                console.error("Erro ao buscar CEP:", error);
                toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível consultar o CEP.', life: 3000 });
            });
    }
});

// --- LÓGICA DO MODAL DE EDIÇÃO E CONTATOS ---
const openEditDialog = () => {
    entidadeParaEditar.value = JSON.parse(JSON.stringify(entidade.value));
    entidadeParaEditar.value.contatos = entidadeParaEditar.value.contatos || [];
    entidadeParaEditar.value.eh_doador = !!entidadeParaEditar.value.eh_doador;
    entidadeParaEditar.value.eh_gestor = !!entidadeParaEditar.value.eh_gestor;
    const cat = entidadeParaEditar.value.categoria;
    entidadeParaEditar.value.categoria = (cat && typeof cat === 'object') ? cat.id : (cat ?? null);
    entidadeParaEditar.value.data_cadastro = parseAPIDate(entidadeParaEditar.value.data_cadastro);
    entidadeParaEditar.value.vigencia_de = parseAPIDate(entidadeParaEditar.value.vigencia_de);
    entidadeParaEditar.value.vigencia_ate = parseAPIDate(entidadeParaEditar.value.vigencia_ate);
    submitted.value = false;
    toggleError.value = false;
    entidadeDialog.value = true;
};
const hideDialog = () => {
    entidadeDialog.value = false;
    submitted.value = false;
};
const saveEntidade = async () => {
    submitted.value = true;
    toggleError.value = !(entidadeParaEditar.value.eh_doador || entidadeParaEditar.value.eh_gestor);
    if (toggleError.value) {
        toast.add({ severity: 'warn', summary: 'Atenção', detail: 'Selecione Doador e/ou Gestor.', life: 2500 });
        return;
    }
    if (!entidadeParaEditar.value.razao_social) return;

    let entidadePayload = { ...entidadeParaEditar.value };
    entidadePayload.data_cadastro = formatDateToAPI(entidadePayload.data_cadastro);
    entidadePayload.vigencia_de = formatDateToAPI(entidadePayload.vigencia_de);
    entidadePayload.vigencia_ate = formatDateToAPI(entidadePayload.vigencia_ate);
    entidadePayload.categoria = entidadePayload.categoria ?? null;
    entidadePayload.documento = onlyDigits(entidadePayload.documento);
    entidadePayload.cep = onlyDigits(entidadePayload.cep);
    delete entidadePayload.contatos;

    try {
        // 7. USAMOS 'api' PARA ATUALIZAR A ENTIDADE
        const response = await api.put(`/entidades/${entidadeParaEditar.value.id}/`, entidadePayload);
        const savedEntidade = response.data;

        // 8. USAMOS 'api' PARA ATUALIZAR/CRIAR CONTATOS
        const contatosPromises = entidadeParaEditar.value.contatos.map(contato => {
            const contatoPayload = { ...contato, entidade: savedEntidade.id };
            if (contatoPayload.tipo_contato === 'T') {
                contatoPayload.valor = onlyDigits(contatoPayload.valor);
            }
            if (contatoPayload.tipo_contato === 'E' && contatoPayload.valor && !isValidEmail(contatoPayload.valor)) {
                return Promise.reject({ message: 'E-mail inválido em contatos.' });
            }
            return contato.id
                ? api.put(`/contatos/${contato.id}/`, contatoPayload)
                : api.post('/contatos/', contatoPayload);
        });
        
        await Promise.all(contatosPromises);

        toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Entidade atualizada com sucesso!', life: 3000 });
        entidadeDialog.value = false;
        fetchEntidadeData();

    } catch (err) {
        console.error("Erro ao salvar entidade:", err.response?.data || err);
        toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível salvar a entidade.', life: 3000 });
    }
};
const addContato = (tipo) => {
    entidadeParaEditar.value.contatos.push({
        tipo_contato: tipo,
        valor: '',
        descricao: ''
    });
};
const removeContato = (contatoParaRemover) => {
    entidadeParaEditar.value.contatos = entidadeParaEditar.value.contatos.filter(c => c !== contatoParaRemover);
    if (contatoParaRemover.id) {
        // 9. USAMOS 'api' PARA DELETAR CONTATO
        api.delete(`/contatos/${contatoParaRemover.id}/`)
            .then(() => toast.add({ severity: 'info', summary: 'Aviso', detail: 'Contato removido.', life: 2000 }))
            .catch(err => console.error("Erro ao deletar contato:", err));
    }
};

// --- CRUD DE RESPONSÁVEIS ---
const openNovoResponsavelDialog = () => {
    responsavel.value = {};
    submitted.value = false;
    isEditMode.value = false;
    responsavelDialog.value = true;
};
const editResponsavel = (responsavelParaEditar) => {
    responsavel.value = {
        ...responsavelParaEditar.pessoa_fisica,
        cargo: responsavelParaEditar.cargo,
        vinculoId: responsavelParaEditar.id
    };
    if (responsavel.value.data_nascimento) {
        responsavel.value.data_nascimento = parseAPIDate(responsavel.value.data_nascimento);
    }
    submitted.value = false;
    isEditMode.value = true;
    responsavelDialog.value = true;
};
const saveResponsavel = async () => {
    submitted.value = true;
    if (!responsavel.value.nome_completo || !responsavel.value.cargo) return;

    const pessoaPayload = {
        nome_completo: responsavel.value.nome_completo,
        cpf: responsavel.value.cpf,
        telefone: responsavel.value.telefone,
        email: responsavel.value.email,
        data_nascimento: formatDateToAPI(responsavel.value.data_nascimento)
    };

    try {
        let pessoaSalva;
        // 10. USAMOS 'api' PARA SALVAR PESSOA FÍSICA
        if (isEditMode.value) {
            const response = await api.put(`/pessoas/${responsavel.value.id}/`, pessoaPayload);
            pessoaSalva = response.data;
        } else {
            const response = await api.post('/pessoas/', pessoaPayload);
            pessoaSalva = response.data;
        }

        const vinculoPayload = {
            entidade: entidade.value.id,
            pessoa_fisica: pessoaSalva.id,
            cargo: responsavel.value.cargo
        };

        // 11. USAMOS 'api' PARA SALVAR VÍNCULO DE RESPONSÁVEL
        if (isEditMode.value) {
            await api.put(`/responsaveis/${responsavel.value.vinculoId}/`, vinculoPayload);
        } else {
            await api.post('/responsaveis/', vinculoPayload);
        }

        toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Responsável salvo com sucesso!', life: 3000 });
        responsavelDialog.value = false;
        fetchEntidadeData();

    } catch (err) {
        console.error("Erro ao salvar responsável:", err.response?.data || err);
        toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível salvar.', life: 3000 });
    }
};

// --- EXCLUSÃO DE VÍNCULO E CRUD DE BENEFICIADOS ---
const confirmRemoverVinculo = (tipo, vinculo) => {
    vinculoParaDeletar.value = { tipo, ...vinculo };
    deleteVinculoDialog.value = true;
};
const deleteVinculoConfirmado = () => {
    const { tipo, id } = vinculoParaDeletar.value;
    const endpoint = tipo === 'responsável' ? 'responsaveis' : 'beneficiarios';

    // 12. USAMOS 'api' PARA DELETAR VÍNCULO
    api.delete(`/${endpoint}/${id}/`)
        .then(() => {
            toast.add({ severity: 'success', summary: 'Sucesso', detail: `${tipo} desvinculado.`, life: 3000 });
            fetchEntidadeData();
        })
        .catch(err => {
            console.error(`Erro ao remover ${tipo}:`, err);
            toast.add({ severity: 'error', summary: 'Erro', detail: `Não foi possível desvincular o ${tipo}.`, life: 3000 });
        })
        .finally(() => {
            deleteVinculoDialog.value = false;
            vinculoParaDeletar.value = {};
        });
};
const openNovoBeneficiadoDialog = () => {
    beneficiado.value = {};
    submitted.value = false;
    isBeneficiadoEditMode.value = false;
    beneficiadoDialog.value = true;
};
const editBeneficiado = (beneficiadoParaEditar) => {
    beneficiado.value = {
        ...beneficiadoParaEditar.pessoa_fisica,
        vinculoId: beneficiadoParaEditar.id
    };
    if (beneficiado.value.data_nascimento) {
        beneficiado.value.data_nascimento = parseAPIDate(beneficiado.value.data_nascimento);
    }
    submitted.value = false;
    isBeneficiadoEditMode.value = true;
    beneficiadoDialog.value = true;
};
const saveBeneficiado = async () => {
    submitted.value = true;
    if (!beneficiado.value.nome_completo) return;

    const pessoaPayload = {
        nome_completo: beneficiado.value.nome_completo,
        cpf: beneficiado.value.cpf,
        telefone: beneficiado.value.telefone,
        email: beneficiado.value.email,
        data_nascimento: formatDateToAPI(beneficiado.value.data_nascimento)
    };

    try {
        let pessoaSalva;
        // 13. USAMOS 'api' PARA SALVAR PESSOA FÍSICA DO BENEFICIADO
        if (isBeneficiadoEditMode.value) {
            const response = await api.put(`/pessoas/${beneficiado.value.id}/`, pessoaPayload);
            pessoaSalva = response.data;
        } else {
            const response = await api.post('/pessoas/', pessoaPayload);
            pessoaSalva = response.data;
        }

        const vinculoPayload = {
            entidade_intermediaria: entidade.value.id,
            pessoa_fisica: pessoaSalva.id
        };

        // 14. USAMOS 'api' PARA SALVAR VÍNCULO DE BENEFICIADO
        if (isBeneficiadoEditMode.value) {
            await api.put(`/beneficiarios/${beneficiado.value.vinculoId}/`, vinculoPayload);
        } else {
            await api.post('/beneficiarios/', vinculoPayload);
        }

        toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Beneficiado salvo com sucesso!', life: 3000 });
        beneficiadoDialog.value = false;
        fetchEntidadeData();

    } catch (err) {
        console.error("Erro ao salvar beneficiado:", err.response?.data || err);
        toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível salvar.', life: 3000 });
    }
};
const abrirEmNovaAba = (name, params) => {
  const { href } = router.resolve({ name, params });
  window.open(href, '_blank');
};
</script>

<template>
    <div>
        <div class="card" v-if="entidade">
            <div class="flex flex-wrap gap-2 items-center justify-between mb-6">
                <div class="flex gap-2">
                    <router-link to="/app/entidades">
                        <Button icon="pi pi-arrow-left" severity="secondary" text rounded />
                    </router-link>
                    <div>
                        <h3 class="m-0">{{ entidade.nome_fantasia }}</h3>
                        <div>
                            <Tag v-if="entidade.eh_doador" value="Doador" severity="success" class="mr-2"></Tag>
                            <Tag v-if="entidade.eh_gestor" value="Gestor" severity="info" class="mr-2"></Tag>
                            <Tag v-if="entidade.eh_gestor" severity="info">
                                {{ entidade.categoria?.nome || (categorias.find(c => c.id === entidade.categoria)?.nome) || 'Não definida' }}
                            </Tag>
                        </div>
                    </div>
                </div>
                <div>
                    <Button icon="pi pi-pencil" label="Editar Dados Gerais" class="p-button-text mr-3" @click="openEditDialog" />
                    <Button
                        label="Relatório da entidade"
                        icon="pi pi-print"
                        class="p-button-help"
                        :disabled="!entidade?.id"
                        @click="abrirEmNovaAba('RelatorioEntidade', { id: entidade?.id })"
                    />
                </div>
            </div>
            <Divider />
            <div class="flex flex-col gap-4">
                <div class="grid grid-cols-12 gap-4">
                    <div class="flex items-center gap-2 col-span-8"><strong>Razão Social:</strong> {{ entidade.razao_social }}</div>
                    <div class="flex items-center gap-2 col-span-4"><strong>Documento:</strong> {{ maskDoc(entidade.documento) }}</div>
                </div>
                <div><strong>Endereço:</strong> {{ entidade.logradouro }}, {{ entidade.numero }} - {{ entidade.bairro }}</div>
                <div><strong>Observações:</strong> {{ entidade.observacoes }}</div>
                <div class="grid grid-cols-12 gap-4">
                    <Fieldset class="col-span-6" legend="Vigência">
                        <p class="m-0"><strong>Início:</strong> {{ formatarData(entidade.vigencia_de) }}</p>
                        <p class="m-0"><strong>Término:</strong> {{ formatarData(entidade.vigencia_ate) }}</p>
                    </Fieldset>
                    <Fieldset class="col-span-6" legend="Contatos">
                        <div v-if="entidade.contatos && entidade.contatos.length > 0">
                            <div v-for="contato in entidade.contatos" :key="contato.id" class="flex flex-col gap-4">
                                <div class="flex items-center gap-2">
                                    <i class="pi text-xl text-primary" :class="contato.tipo_contato === 'T' ? 'pi-phone' : 'pi-envelope'"></i>
                                    <div>
                                        <div class="font-bold">{{ contato.valor }}</div>
                                        <small v-if="contato.descricao" class="text-500">{{ contato.descricao }}</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div v-else>
                            <Message severity="error">Nenhum contato cadastrado para esta entidade.</Message>
                        </div>
                    </Fieldset>
                </div>
            </div>
            <Tabs v-model:value="activeTabValue" class="mt-5">
                <TabList>
                    <Tab v-if="entidade.eh_gestor" value="entregas">Histórico de Doações (Entregas)</Tab>
                    <Tab v-if="entidade.eh_doador" value="entradas">Histórico de Doações (Entradas)</Tab>
                    <Tab value="responsaveis">Responsáveis (Equipe)</Tab>
                    <Tab v-if="entidade.eh_gestor" value="beneficiados">Beneficiados (Munícipes)</Tab>
                </TabList>
                <TabPanels>
                    <TabPanel v-if="entidade.eh_gestor" value="entregas">
                        <div class="flex items-center justify-between mb-3">
                            <h5 class="m-0">Histórico de Doações (Entregas)</h5>
                            <Button
                                label="Registrar Entrega"
                                icon="pi pi-arrow-up"
                                @click="goToRegistrarSaida"
                            />
                        </div>
                        <Timeline :value="historicoAtendimentos" align="alternate" class="customized-timeline">
                            <template #marker="slotProps">
                                <span class="custom-marker shadow-2">
                                    <i class="pi pi-box"></i>
                                </span>
                            </template>
                            <template #content="slotProps">
                                <Card>
                                    <template #title>{{ formatarMesAno(slotProps.item.data_saida) }}</template>
                                    <template #subtitle>Dia: {{ formatarDia(slotProps.item.data_saida) }}</template>
                                    <template #content>
                                        <p>{{ slotProps.item.observacoes || 'Nenhuma observação.' }}</p>
                                        <Button label="Ver Itens Entregues" class="p-button-text" @click="toggleOverlay($event, slotProps.item)"></Button>
                                    </template>
                                    <template #footer>
                                        <div class="flex justify-end">
                                            <Button
                                                label="Editar"
                                                icon="pi pi-pencil"
                                                text
                                                @click="editarSaida(slotProps.item)"
                                            />
                                        </div>
                                    </template>
                                </Card>
                            </template>
                        </Timeline>
                    </TabPanel>

                    <TabPanel v-if="entidade.eh_doador" value="entradas">
                        <div class="flex items-center justify-between mb-3">
                            <h5 class="m-0">Histórico de Doações Recebidas (Entradas)</h5>
                            <Button
                                label="Registrar Entrada"
                                icon="pi pi-arrow-down"
                                @click="goToRegistrarEntrada"
                            />
                        </div>
                        <Timeline :value="historicoDoacoes" align="alternate" class="customized-timeline">
                            <template #marker="slotProps">
                                <span class="custom-marker shadow-2">
                                    <i class="pi pi-box"></i>
                                </span>
                            </template>
                            <template #content="slotProps">
                                <Card>
                                    <template #title>{{ formatarMesAno(slotProps.item.data_doacao) }}</template>
                                    <template #subtitle>Dia: {{ formatarDia(slotProps.item.data_doacao) }}</template>
                                    <template #content>
                                        <p>{{ slotProps.item.observacoes || 'Nenhuma observação.' }}</p>
                                        <Button label="Ver Itens Doados" class="p-button-text" @click="toggleOverlay($event, slotProps.item)"></Button>
                                    </template>
                                    <template #footer>
                                        <div class="flex justify-end">
                                            <Button
                                                label="Editar"
                                                icon="pi pi-pencil"
                                                text
                                                @click="editarEntrada(slotProps.item)"
                                            />
                                        </div>
                                    </template>
                                </Card>
                            </template>
                        </Timeline>
                    </TabPanel>

                    <TabPanel value="responsaveis">
                        <Toolbar class="mb-4">
                            <template #start>
                                <Button label="Cadastrar Responsável" icon="pi pi-plus" class="p-button-success" @click="openNovoResponsavelDialog" />
                            </template>
                        </Toolbar>
                        <DataTable :value="entidade.responsaveis" responsiveLayout="scroll">
                            <Column field="pessoa_fisica.nome_completo" header="Nome" sortable></Column>
                            <Column field="cargo" header="Cargo" sortable></Column>
                            <Column field="pessoa_fisica.telefone" header="Telefone"></Column>
                            <Column field="pessoa_fisica.email" header="E-mail"></Column>
                            <Column headerStyle="width: 12rem; text-align: center" header="Ações">
                                <template #body="slotProps">
                                    <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editResponsavel(slotProps.data)" />
                                    <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmRemoverVinculo('responsável', slotProps.data)" />
                                </template>
                            </Column>
                        </DataTable>
                    </TabPanel>
                    
                    <TabPanel v-if="entidade.eh_gestor" value="beneficiados">
                        <Toolbar class="mb-4">
                            <template #start>
                                <Button label="Cadastrar Beneficiado" icon="pi pi-plus" class="p-button-success" @click="openNovoBeneficiadoDialog" />
                            </template>
                        </Toolbar>
                        <DataTable :value="entidade.beneficiarios" responsiveLayout="scroll">
                            <Column field="pessoa_fisica.nome_completo" header="Nome" sortable></Column>
                            <Column field="pessoa_fisica.cpf" header="CPF" sortable></Column>
                            <Column field="pessoa_fisica.telefone" header="Telefone"></Column>
                            <Column headerStyle="width: 12rem; text-align: center" header="Ações">
                                <template #body="slotProps">
                                    <Button icon="pi pi-pencil" outlined rounded class="mr-2" @click="editBeneficiado(slotProps.data)" />
                                    <Button icon="pi pi-trash" outlined rounded severity="danger" @click="confirmRemoverVinculo('beneficiado', slotProps.data)" />
                                </template>
                            </Column>
                        </DataTable>
                    </TabPanel>
                </TabPanels>
            </Tabs>
        </div>
        
        <div class="card text-center" v-else>
            <ProgressSpinner />
            <p>Carregando dados da entidade...</p>
        </div>

        <Dialog v-model:visible="entidadeDialog" :style="{ width: '50rem' }" header="Detalhes da Entidade" :modal="true">
            <div class="flex flex-col gap-6">
                <div class="grid grid-cols-12 gap-4">
                    <div class="flex items-center col-span-6">
                        <InputSwitch v-model="entidadeParaEditar.eh_gestor" inputId="gestor-switch" />
                        <label for="gestor-switch" class="font-bold ml-3"> Marcar como Gestor/Recebedor</label>
                    </div>
                    <div class="flex items-center col-span-6">
                        <InputSwitch v-model="entidadeParaEditar.eh_doador" inputId="doador-switch" />
                        <label for="doador-switch" class="font-bold ml-3"> Marcar como Doador</label>
                    </div>
                </div>
                <small class="p-error" v-if="submitted && toggleError">Selecione pelo menos uma opção (Gestor/Recebedor ou Doador).</small>
                <Divider class="my-2" />
                <div class="grid grid-cols-12 gap-4">
                    <div class="col-span-8">
                        <label for="razao_social" class="block font-bold mb-3">Razão Social</label>
                        <InputText id="razao_social" v-model.trim="entidadeParaEditar.razao_social" required="true" autofocus :class="{'p-invalid': submitted && !entidadeParaEditar.razao_social}" fluid />
                        <small class="p-error" v-if="submitted && !entidadeParaEditar.razao_social">Razão Social é obrigatório.</small>
                    </div>
                    <div class="col-span-4">
                        <label for="documento" class="block font-bold mb-3">CNPJ ou CPF</label>
                        <InputText
                          id="documento"
                          :value="maskDoc(entidadeParaEditar.documento)"
                          @input="onDocInput"
                          inputmode="numeric"
                          required
                          :class="{'p-invalid': submitted && !entidadeParaEditar.documento}"
                          fluid
                        />
                        <small class="p-error" v-if="submitted && !entidadeParaEditar.documento">Documento é obrigatório.</small>
                    </div>
                </div>
                <div class="grid grid-cols-12 gap-4">
                    <div class="col-span-8">
                        <label for="nome_fantasia" class="block font-bold mb-3">Nome Fantasia</label>
                        <InputText id="nome_fantasia" v-model.trim="entidadeParaEditar.nome_fantasia" fluid />
                    </div>
                    <div class="col-span-4">
                        <label for="categoria" class="block font-bold mb-3">Categoria</label>
                        <Dropdown
                            id="categoria"
                            v-model="entidadeParaEditar.categoria"
                            :options="categorias"
                            optionLabel="nome"
                            optionValue="id"
                            placeholder="Selecione"
                            fluid
                        />
                    </div>
                </div>
                <div class="grid grid-cols-12 gap-4">
                    <div class="col-span-4">
                        <label for="data_cadastro" class="block font-bold mb-3">Data de Cadastro</label>
                        <Calendar id="data_cadastro" v-model="entidadeParaEditar.data_cadastro" dateFormat="dd/mm/yy" fluid />
                    </div>
                    <div class="col-span-4">
                        <label for="vigencia_de" class="block font-bold mb-3">Vigência De (MM/AAAA)</label>
                        <Calendar id="vigencia_de" v-model="entidadeParaEditar.vigencia_de" view="month" dateFormat="mm/yy" fluid />
                    </div>
                    <div class="col-span-4">
                        <label for="vigencia_ate" class="block font-bold mb-3">Vigência Até (MM/AAAA)</label>
                        <Calendar id="vigencia_ate" v-model="entidadeParaEditar.vigencia_ate" view="month" dateFormat="mm/yy" fluid />
                    </div>
                </div>
                <Divider class="m-0" align="left" type="solid">
                    <b>Contatos</b>
                </Divider>
                <div class="mb-2 text-sm text-gray-600">
                    {{ contatoStats.telefones }} telefone(s) · {{ contatoStats.emails }} e-mail(s)
                </div>
                <div v-for="(contato, index) in entidadeParaEditar.contatos" :key="index">
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
                                <InputText
                                    v-model.trim="contato.valor"
                                    type="email"
                                    :class="{'p-invalid': contato.valor && !isValidEmail(contato.valor)}"
                                    placeholder="email@exemplo.com"
                                    fluid
                                />
                            <small class="p-error" v-if="contato.valor && !isValidEmail(contato.valor)">E-mail inválido.</small>
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
                        <InputMask id="cep" v-model="entidadeParaEditar.cep" mask="99999-999" :unmask="true" fluid />
                    </div>
                    <div class="col-span-9">
                        <label for="logradouro" class="block font-bold mb-3">Logradouro (Rua, Av.)</label>
                        <InputText id="logradouro" v-model="entidadeParaEditar.logradouro" fluid />
                    </div>
                    <div class="col-span-3">
                        <label for="numero" class="block font-bold mb-3">Número</label>
                        <InputText id="numero" v-model="entidadeParaEditar.numero" fluid />
                    </div>
                    <div class="col-span-9">
                        <label for="bairro" class="block font-bold mb-3">Bairro</label>
                        <InputText id="bairro" v-model="entidadeParaEditar.bairro" fluid />
                    </div>
                </div>
                <div>
                    <label for="observacoes" class="block font-bold mb-3">Observações</label>
                    <Textarea id="observacoes" v-model="entidadeParaEditar.observacoes" rows="3" fluid />
                </div>
            </div>
            <template #footer>
                <Button label="Cancelar" icon="pi pi-times" text @click="hideDialog" />
                <Button label="Salvar" icon="pi pi-check" @click="saveEntidade" />
            </template>
        </Dialog>

        <Dialog v-model:visible="responsavelDialog" :style="{ width: '50rem' }" :header="isEditMode ? 'Editar Responsável' : 'Cadastrar Novo Responsável'" :modal="true" class="p-fluid">
            <div class="flex flex-col gap-6">
                <div>
                    <label for="nome_completo" class="block font-bold mb-3">Nome Completo</label>
                    <InputText id="nome_completo" v-model.trim="responsavel.nome_completo" required="true" autofocus :class="{'p-invalid': submitted && !responsavel.nome_completo}" fluid />
                    <small class="p-error" v-if="submitted && !responsavel.nome_completo">Nome é obrigatório.</small>
                </div>
                <div class="grid grid-cols-12 gap-4">
                    <div class="col-span-6">
                        <label for="cpf" class="block font-bold mb-3">CPF</label>
                        <InputText id="cpf" v-model.trim="responsavel.cpf" fluid />
                    </div>
                    <div class="col-span-6">
                        <label for="data_nascimento" class="block font-bold mb-3">Data de Nascimento</label>
                        <Calendar id="data_nascimento" v-model="responsavel.data_nascimento" dateFormat="dd/mm/yy" fluid />
                    </div>
                </div>
                <div class="grid grid-cols-12 gap-4">
                    <div class="col-span-4">
                        <label for="telefone" class="block font-bold mb-3">Telefone</label>
                        <InputText id="telefone" v-model.trim="responsavel.telefone" fluid />
                    </div>
                    <div class="col-span-8">
                        <label for="email" class="block font-bold mb-3">Email</label>
                        <InputText id="email" v-model.trim="responsavel.email" fluid />
                    </div>
                </div>
                <Divider align="left" type="solid">
                    <b>Dados do Vínculo</b>
                </Divider>
                <div>
                    <label for="cargo" class="block font-bold mb-3">Cargo</label>
                    <InputText id="cargo" v-model.trim="responsavel.cargo" required="true" :class="{'p-invalid': submitted && !responsavel.cargo}" fluid />
                    <small class="p-error" v-if="submitted && !responsavel.cargo">Cargo é obrigatório.</small>
                </div>
            </div>
            <template #footer>
                <Button label="Cancelar" icon="pi pi-times" text @click="responsavelDialog = false" />
                <Button label="Salvar" icon="pi pi-check" @click="saveResponsavel" />
            </template>
        </Dialog>

        <Dialog v-model:visible="deleteVinculoDialog" :style="{ width: '450px' }" header="Confirmar Exclusão" :modal="true">
            <div class="flex align-items-center">
                <i class="pi pi-exclamation-triangle mr-3" style="font-size: 2rem" />
                <span>
                    Tem certeza que deseja desvincular 
                    <b>{{ vinculoParaDeletar.pessoa_fisica?.nome_completo }}</b>?
                </span>
            </div>
            <template #footer>
                <Button label="Não" icon="pi pi-times" text @click="deleteVinculoDialog = false" />
                <Button label="Sim" icon="pi pi-check" @click="deleteVinculoConfirmado" />
            </template>
        </Dialog>

        <Dialog v-model:visible="beneficiadoDialog" :style="{ width: '50rem' }" :header="isEditMode ? 'Editar Beneficiado' : 'Cadastrar Novo Beneficiado'" :modal="true" class="p-fluid">
            <div class="flex flex-col gap-6">
                <div>
                    <label for="ben-nome_completo" class="block font-bold mb-3">Nome Completo</label>
                    <InputText id="ben-nome_completo" v-model.trim="beneficiado.nome_completo" required="true" autofocus :class="{'p-invalid': submitted && !beneficiado.nome_completo}" fluid />
                    <small class="p-error" v-if="submitted && !beneficiado.nome_completo">Nome é obrigatório.</small>
                </div>
                <div class="grid grid-cols-12 gap-4">
                    <div class="col-span-6">
                        <label for="ben-cpf" class="block font-bold mb-3">CPF</label>
                        <InputText id="ben-cpf" v-model.trim="beneficiado.cpf" fluid />
                    </div>
                    <div class="col-span-6">
                        <label for="ben-data_nascimento" class="block font-bold mb-3">Data de Nascimento</label>
                        <Calendar id="ben-data_nascimento" v-model="beneficiado.data_nascimento" dateFormat="dd/mm/yy" fluid />
                    </div>
                </div>
                <div class="grid grid-cols-12 gap-4">
                    <div class="col-span-4">
                        <label for="ben-telefone" class="block font-bold mb-3">Telefone</label>
                        <InputText id="ben-telefone" v-model.trim="beneficiado.telefone" fluid />
                    </div>
                    <div class="col-span-8">
                        <label for="ben-email" class="block font-bold mb-3">Email</label>
                        <InputText id="ben-email" v-model.trim="beneficiado.email" fluid />
                    </div>
                </div>
            </div>
            <template #footer>
                <Button label="Cancelar" icon="pi pi-times" text @click="beneficiadoDialog = false" />
                <Button label="Salvar" icon="pi pi-check" @click="saveBeneficiado" />
            </template>
        </Dialog>
        <Popover ref="op">
            <DataTable :value="overlayItems.itens_doados || overlayItems.itens_saida || []">
                <Column field="item.nome" header="Item"></Column>
                <Column field="quantidade" header="Qtd"></Column>
            </DataTable>
            <DataTable :value="overlayItems.kits_saida || []" v-if="overlayItems.kits_saida">
                <Column field="kit.nome" header="Kit"></Column>
                <Column field="quantidade" header="Qtd"></Column>
            </DataTable>
        </Popover>
    </div>
</template>

<style lang="scss" scoped>
.custom-marker {
    display: flex;
    width: 2rem;
    height: 2rem;
    align-items: center;
    justify-content: center;
    color: #ffffff;
    border-radius: 50%;
    background-color: var(--primary-color);
    z-index: 1;
}
</style>