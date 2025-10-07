<script setup>
import { useAuthStore } from '@/store/auth';
import { ref, onMounted, watch, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import axios from 'axios';

import Divider from 'primevue/divider';
import Tag from 'primevue/tag';
import Message from 'primevue/message';
import Fieldset from 'primevue/fieldset';

// --- ESTADO DO COMPONENTE ---
const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();
const toast = useToast();
const entidade = ref(null);
const loading = ref(true);
const API_BASE_URL = 'http://127.0.0.1:8005/api/';

const entidadeDialog = ref(false); // Controla a visibilidade do modal
const entidadeParaEditar = ref({ contatos: [] }); // Armazena os dados do formulário de edição
const categorias = ref([]); // Para o dropdown de categorias
const submitted = ref(false); // Para validação do formulário

// --- ESTADO PARA CRUD DE RESPONSÁVEIS ---
const responsavelDialog = ref(false); // Modal de criar/editar responsável
const responsavel = ref({}); // Objeto para o formulário de responsável
const isEditMode = ref(false); // Controla se o modal está em modo de edição

// --- NOVO ESTADO: MODAL DE CONFIRMAÇÃO DE EXCLUSÃO DE VÍNCULO ---
const deleteVinculoDialog = ref(false); // Controla a visibilidade do modal
const vinculoParaDeletar = ref({}); // Guarda os dados do vínculo a ser deletado

// --- ESTADO PARA CRUD DE BENEFICIADOS (NOVO) ---
const beneficiadoDialog = ref(false); // Modal de criar/editar beneficiado
const beneficiado = ref({}); // Objeto para o formulário de beneficiado
const isBeneficiadoEditMode = ref(false); // Controla o modo do modal de beneficiado

const historicoAtendimentos = ref([]);
const historicoDoacoes = ref([]);

const op = ref();
const overlayItems = ref([]);
const toggleError = ref(false);

// --- FUNÇÕES AUXILIARES ---
const formatDateToAPI = (date) => {
    if (!date) return null;
    const d = new Date(date);
    return d.toISOString().split('T')[0]; // Formato AAAA-MM-DD
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

// === Helpers de máscara/normalização (mesmos do Entidades.vue) ===
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

// Handlers de input (mantêm o modelo só com dígitos)
const onDocInput = (e) => { entidadeParaEditar.value.documento = onlyDigits(e.target.value).slice(0, 14); };
const onPhoneInput = (contato, e) => { contato.valor = onlyDigits(e.target.value).slice(0, 11); };


// --- NAVEGAÇÃO: criar entrada/saída com prefill e editar registros ---
const goToRegistrarEntrada = () => {
    if (!entidade.value) return;
    router.push({
        name: 'EntradaDoacao',
        query: {
            doador_id: entidade.value.id,
            doador_nome: entidade.value.nome_fantasia || entidade.value.razao_social || entidade.value.nome,
            // se sua API expõe content_type_id na entidade, passe aqui:
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
    if (!registro?.id) {
        toast.add({ severity: 'warn', summary: 'Atenção', detail: 'Registro sem ID para edição.', life: 2500 });
        return;
    }
    router.push({ name: 'EditarEntradaDoacao', params: { id: registro.id } });
};

const editarSaida = (registro) => {
    if (!registro?.id) {
        toast.add({ severity: 'warn', summary: 'Atenção', detail: 'Registro sem ID para edição.', life: 2500 });
        return;
    }
    router.push({ name: 'EditarSaidaDoacao', params: { id: registro.id } });
};

const formatarMesAno = (dataString) => {
    const data = new Date(dataString);
    return data.toLocaleString('pt-BR', { month: 'long', year: 'numeric' });
};
const formatarDia = (dataString) => {
    const data = new Date(dataString);
    return data.getDate();
};

// --- BUSCA DE DADOS ---
const fetchEntidadeData = () => {
    loading.value = true;
    const entidadeId = route.params.id;

    // 1. Busca os dados principais da entidade
    axios.get(`${API_BASE_URL}entidades/${entidadeId}/`)
        .then(response => {
            entidade.value = response.data;
            
            // 2. Se a busca principal deu certo, busca os históricos
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

// NOVAS FUNÇÕES DE BUSCA
const fetchAtendimentos = (entidadeId) => {
    axios.get(`${API_BASE_URL}entidades/${entidadeId}/atendimentos/`)
        .then(response => {
            historicoAtendimentos.value = response.data;
        });
};

const fetchDoacoes = (entidadeId) => {
     axios.get(`${API_BASE_URL}entidades/${entidadeId}/doacoes/`)
        .then(response => {
            historicoDoacoes.value = response.data;
        });
};

const fetchCategorias = () => {
    axios.get(`${API_BASE_URL}categorias/`).then((response) => {
        categorias.value = response.data.results;
    });
};

onMounted(() => {
    fetchEntidadeData();
    fetchCategorias();
});

watch(entidadeParaEditar, (novo) => {
  if (!novo) return;
  if (novo.eh_doador && !novo.eh_gestor) {
    const catDoador = categorias.value.find(c => c.nome?.toLowerCase() === 'doador');
    if (catDoador) novo.categoria = catDoador.id; // trabalhamos com id
  }
}, { deep: true });

watch(() => entidadeParaEditar.value.cep, (novoCep) => {
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
                    entidadeParaEditar.value.logradouro = response.data.logradouro;
                    entidadeParaEditar.value.bairro = response.data.bairro;
                    // Futuramente, podemos adicionar cidade e estado também
                }
            })
            .catch(error => {
                console.error("Erro ao buscar CEP:", error);
                toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível consultar o CEP.', life: 3000 });
            });
    }
});

// --- LÓGICA DO MODAL DE EDIÇÃO ---
const openEditDialog = () => {
    entidadeParaEditar.value = JSON.parse(JSON.stringify(entidade.value));
    entidadeParaEditar.value.contatos = entidadeParaEditar.value.contatos || [];
    entidadeParaEditar.value.eh_doador = !!entidadeParaEditar.value.eh_doador;
    entidadeParaEditar.value.eh_gestor = !!entidadeParaEditar.value.eh_gestor;

    const cat = entidadeParaEditar.value.categoria;
    entidadeParaEditar.value.categoria = (cat && typeof cat === 'object') ? cat.id : (cat ?? null);

    if (entidadeParaEditar.value.data_cadastro) entidadeParaEditar.value.data_cadastro = new Date(entidadeParaEditar.value.data_cadastro);
    if (entidadeParaEditar.value.vigencia_de) entidadeParaEditar.value.vigencia_de = new Date(entidadeParaEditar.value.vigencia_de);
    if (entidadeParaEditar.value.vigencia_ate) entidadeParaEditar.value.vigencia_ate = new Date(entidadeParaEditar.value.vigencia_ate);

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

    // 1. Prepara o payload da Entidade
    let entidadePayload = { ...entidadeParaEditar.value };
    entidadePayload.data_cadastro = formatDateToAPI(entidadePayload.data_cadastro);
    entidadePayload.vigencia_de = formatDateToAPI(entidadePayload.vigencia_de);
    entidadePayload.vigencia_ate = formatDateToAPI(entidadePayload.vigencia_ate);
    entidadePayload.categoria = entidadePayload.categoria ?? null;
    entidadePayload.documento = onlyDigits(entidadePayload.documento);
    entidadePayload.cep = onlyDigits(entidadePayload.cep);
    
    delete entidadePayload.contatos;

    try {
        // 2. Salva a Entidade
        const response = await axios.put(`${API_BASE_URL}entidades/${entidadeParaEditar.value.id}/`, entidadePayload);
        const savedEntidade = response.data;

        // 3. Processa e Salva os Contatos
        const contatosPromises = entidadeParaEditar.value.contatos.map(contato => {
            const contatoPayload = { ...contato, entidade: savedEntidade.id };
            if (contatoPayload.tipo_contato === 'T') {
                contatoPayload.valor = onlyDigits(contatoPayload.valor);
            }
            if (contatoPayload.tipo_contato === 'E' && contatoPayload.valor && !isValidEmail(contatoPayload.valor)) {
                return Promise.reject({ message: 'E-mail inválido em contatos.' });
            }
            return contato.id
                ? axios.put(`${API_BASE_URL}contatos/${contato.id}/`, contatoPayload)
                : axios.post(`${API_BASE_URL}contatos/`, contatoPayload);
        });
        
        await Promise.all(contatosPromises);

        toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Entidade atualizada com sucesso!', life: 3000 });
        entidadeDialog.value = false;
        fetchEntidadeData(); // Recarrega os dados da página

    } catch (err) {
        console.error("Erro ao salvar entidade:", err.response?.data || err);
        toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível salvar a entidade.', life: 3000 });
    }
};

// --- LÓGICA DOS CONTATOS NO MODAL ---
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
        axios.delete(`${API_BASE_URL}contatos/${contatoParaRemover.id}/`)
            .then(() => toast.add({ severity: 'info', summary: 'Aviso', detail: 'Contato removido.', life: 2000 }))
            .catch(err => console.error("Erro ao deletar contato:", err));
    }
};

// --- NOVA LÓGICA: CRUD DE RESPONSÁVEIS ---

// Abre o modal para CRIAR um novo responsável
const openNovoResponsavelDialog = () => {
    responsavel.value = {}; // Limpa o objeto
    submitted.value = false;
    isEditMode.value = false; // Define o modo como 'criação'
    responsavelDialog.value = true;
};

// Abre o modal para EDITAR um responsável existente
const editResponsavel = (responsavelParaEditar) => {
    // Monta o objeto para o formulário com dados da pessoa e do vínculo
    responsavel.value = {
        ...responsavelParaEditar.pessoa_fisica, // Copia dados da pessoa (id, nome, cpf...)
        cargo: responsavelParaEditar.cargo, // Copia o cargo
        vinculoId: responsavelParaEditar.id // Guarda o ID do VÍNCULO
    };
    if (responsavel.value.data_nascimento) {
        responsavel.value.data_nascimento = new Date(responsavel.value.data_nascimento);
    }
    submitted.value = false;
    isEditMode.value = true; // Define o modo como 'edição'
    responsavelDialog.value = true;
};

// Salva (cria ou edita) o responsável e seu vínculo
const saveResponsavel = async () => {
    submitted.value = true;
    if (!responsavel.value.nome_completo || !responsavel.value.cargo) return;

    // Prepara os dados da Pessoa Física
    const pessoaPayload = {
        nome_completo: responsavel.value.nome_completo,
        cpf: responsavel.value.cpf,
        telefone: responsavel.value.telefone,
        email: responsavel.value.email,
        data_nascimento: formatDateToAPI(responsavel.value.data_nascimento)
    };

    try {
        let pessoaSalva;

        // Se estiver em modo de edição, atualiza a pessoa existente
        if (isEditMode.value) {
            const response = await axios.put(`${API_BASE_URL}pessoas/${responsavel.value.id}/`, pessoaPayload);
            pessoaSalva = response.data;
        } else { // Senão, cria uma nova pessoa
            const response = await axios.post(`${API_BASE_URL}pessoas/`, pessoaPayload);
            pessoaSalva = response.data;
        }

        // Agora, cria ou atualiza o VÍNCULO de Responsável
        const vinculoPayload = {
            entidade: entidade.value.id,
            pessoa_fisica: pessoaSalva.id,
            cargo: responsavel.value.cargo
        };

        if (isEditMode.value) { // Atualiza o vínculo existente
            await axios.put(`${API_BASE_URL}responsaveis/${responsavel.value.vinculoId}/`, vinculoPayload);
        } else { // Cria um novo vínculo
            await axios.post(`${API_BASE_URL}responsaveis/`, vinculoPayload);
        }

        toast.add({ severity: 'success', summary: 'Sucesso', detail: 'Responsável salvo com sucesso!', life: 3000 });
        responsavelDialog.value = false;
        fetchEntidadeData(); // Recarrega os dados da entidade

    } catch (err) {
        console.error("Erro ao salvar responsável:", err.response?.data || err);
        toast.add({ severity: 'error', summary: 'Erro', detail: 'Não foi possível salvar.', life: 3000 });
    }
};

// A função 'removerVinculo' que já tínhamos para o botão de lixeira está perfeita e será usada.
const removerVinculo = (tipo, vinculoId) => {
    const confirm = window.confirm(`Tem certeza que deseja remover este ${tipo}?`);
    if (confirm) {
        const endpoint = tipo === 'responsável' ? 'responsaveis' : 'beneficiarios';
        axios.delete(`${API_BASE_URL}${endpoint}/${vinculoId}/`)
            .then(() => {
                toast.add({ severity: 'success', summary: 'Sucesso', detail: `${tipo} desvinculado.`, life: 3000 });
                fetchEntidadeData();
            })
            .catch(err => console.error(`Erro ao remover ${tipo}:`, err));
    }
};

// --- NOVA LÓGICA DE EXCLUSÃO DE VÍNCULO ---

// Passo 1: Abre o modal de confirmação
const confirmRemoverVinculo = (tipo, vinculo) => {
    vinculoParaDeletar.value = { tipo, ...vinculo }; // Guarda o tipo e os dados do vínculo
    deleteVinculoDialog.value = true; // Abre o modal
};

// Passo 2: Executa a exclusão se o usuário confirmar
const deleteVinculoConfirmado = () => {
    const { tipo, id } = vinculoParaDeletar.value;
    const endpoint = tipo === 'responsável' ? 'responsaveis' : 'beneficiarios';

    axios.delete(`${API_BASE_URL}${endpoint}/${id}/`)
        .then(() => {
            toast.add({ severity: 'success', summary: 'Sucesso', detail: `${tipo} desvinculado.`, life: 3000 });
            fetchEntidadeData(); // Atualiza a lista na tela
        })
        .catch(err => {
            console.error(`Erro ao remover ${tipo}:`, err);
            toast.add({ severity: 'error', summary: 'Erro', detail: `Não foi possível desvincular o ${tipo}.`, life: 3000 });
        })
        .finally(() => {
            deleteVinculoDialog.value = false; // Fecha o modal
            vinculoParaDeletar.value = {}; // Limpa o objeto
        });
};

// --- NOVA LÓGICA: CRUD DE BENEFICIADOS ---

// Abre o modal para CRIAR um novo beneficiado
const openNovoBeneficiadoDialog = () => {
    beneficiado.value = {};
    submitted.value = false;
    isBeneficiadoEditMode.value = false;
    beneficiadoDialog.value = true;
};

// Abre o modal para EDITAR um beneficiado existente
const editBeneficiado = (beneficiadoParaEditar) => {
    beneficiado.value = {
        ...beneficiadoParaEditar.pessoa_fisica, // Copia dados da pessoa
        vinculoId: beneficiadoParaEditar.id // Guarda o ID do VÍNCULO
    };
    if (beneficiado.value.data_nascimento) {
        beneficiado.value.data_nascimento = new Date(beneficiado.value.data_nascimento);
    }
    submitted.value = false;
    isBeneficiadoEditMode.value = true;
    beneficiadoDialog.value = true;
};

// Salva (cria ou edita) o beneficiado e seu vínculo
const saveBeneficiado = async () => {
    submitted.value = true;
    if (!beneficiado.value.nome_completo) return;

    // Prepara os dados da Pessoa Física
    const pessoaPayload = {
        nome_completo: beneficiado.value.nome_completo,
        cpf: beneficiado.value.cpf,
        telefone: beneficiado.value.telefone,
        email: beneficiado.value.email,
        data_nascimento: formatDateToAPI(beneficiado.value.data_nascimento)
    };

    try {
        let pessoaSalva;

        if (isBeneficiadoEditMode.value) { // Edição
            const response = await axios.put(`${API_BASE_URL}pessoas/${beneficiado.value.id}/`, pessoaPayload);
            pessoaSalva = response.data;
        } else { // Criação
            const response = await axios.post(`${API_BASE_URL}pessoas/`, pessoaPayload);
            pessoaSalva = response.data;
        }

        // Agora, cria ou atualiza o VÍNCULO de Beneficiado (sem o campo 'cargo')
        const vinculoPayload = {
            entidade_intermediaria: entidade.value.id,
            pessoa_fisica: pessoaSalva.id
        };

        if (isBeneficiadoEditMode.value) { // Atualiza
            await axios.put(`${API_BASE_URL}beneficiarios/${beneficiado.value.vinculoId}/`, vinculoPayload);
        } else { // Cria
            await axios.post(`${API_BASE_URL}beneficiarios/`, vinculoPayload);
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
                    <router-link to="/entidades">
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
                        <p class="m-0"><strong>Início:</strong> {{ entidade.vigencia_de }}</p>
                        <p class="m-0"><strong>Término:</strong> {{ entidade.vigencia_ate }}</p>
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
            <TabView class="mt-5">
                <TabPanel header="Histórico de Doações" v-if="entidade.eh_gestor">
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

                <TabPanel header="Histórico de Doações" v-if="entidade.eh_doador">
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

                <TabPanel header="Responsáveis (Equipe)">
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
                
                <TabPanel header="Beneficiados (Munícipes)" v-if="entidade.eh_gestor">
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
            </TabView>
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
        <OverlayPanel ref="op">
            <DataTable :value="overlayItems.itens_doados || overlayItems.itens_saida || []">
                <Column field="item.nome" header="Item"></Column>
                <Column field="quantidade" header="Qtd"></Column>
            </DataTable>
            <DataTable :value="overlayItems.kits_saida || []" v-if="overlayItems.kits_saida">
                <Column field="kit.nome" header="Kit"></Column>
                <Column field="quantidade" header="Qtd"></Column>
            </DataTable>
        </OverlayPanel>
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