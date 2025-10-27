<script setup>
import { ref, onMounted, computed } from 'vue';
import api from '@/services/api';
import ReportLayout from '@/views/reports/ReportLayout.vue';
import { useRoute } from 'vue-router';

const rows = ref([]);
const loading = ref(true);
const route = useRoute();

// --- FUNÇÕES AUXILIARES ---

const parseAPIDate = (dateString) => {
    if (!dateString || typeof dateString !== 'string') return null;
    const dateOnlyString = dateString.split('T')[0];
    let parts, year, monthIndex, day;
    if (dateOnlyString.includes('/')) {
        parts = dateOnlyString.split('/');
        if (parts.length === 3) {
            day = parseInt(parts[0], 10); monthIndex = parseInt(parts[1], 10) - 1; year = parseInt(parts[2], 10);
        }
    } else if (dateOnlyString.includes('-')) {
        parts = dateOnlyString.split('-');
        if (parts.length === 3) {
            year = parseInt(parts[0], 10); monthIndex = parseInt(parts[1], 10) - 1; day = parseInt(parts[2], 10);
        }
    }
    if (!isNaN(year) && !isNaN(monthIndex) && !isNaN(day)) {
        if (year < 100) year += 2000;
        const dataObj = new Date(year, monthIndex, day);
        if (!isNaN(dataObj.getTime())) return dataObj;
    }
    console.warn(`[RelatorioEntradas] Falha ao parsear data: ${dateString}`);
    return null;
};

// Formata data YYYY-MM-DD para DD/MM/YYYY
const formatarData = (dateOrString) => {
    const dataObj = dateOrString instanceof Date ? dateOrString : parseAPIDate(dateOrString);
    if (dataObj && !isNaN(dataObj.getTime())) {
        const dia = String(dataObj.getDate()).padStart(2, '0');
        const mes = String(dataObj.getMonth() + 1).padStart(2, '0'); // Mês é 0-indexado
        const ano = dataObj.getFullYear();
        return `${dia}/${mes}/${ano}`;
    }
    // Se recebeu uma string que parseAPIDate reconhece, retorna formatado
    if (typeof dateOrString === 'string' && parseAPIDate(dateOrString)) {
         return dateOrString.split('T')[0].split('-').reverse().join('/'); // Tenta formatar YYYY-MM-DD
    }
    return dateOrString || '-'; // Retorna original ou '-'
};

// Copiadas do RelatorioEntidades.vue
const maskPhone = (s) => {
  const d = (s || '').replace(/\D/g, '').slice(0, 11);
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

const getPrincipalContato = (contatos, tipo, usarMascara = false) => {
    if (!Array.isArray(contatos) || contatos.length === 0) return '-';
    const contatosDoTipo = contatos.filter(c => c.tipo_contato === tipo);
    if (contatosDoTipo.length === 0) return '-';
    const principal = contatosDoTipo.find(c => c.descricao && c.descricao.toLowerCase().includes('principal'));
    const valor = principal ? principal.valor : contatosDoTipo[0].valor;
    if (tipo === 'T' && usarMascara) return maskPhone(valor);
    return valor || '-';
};

const shouldShowEntradaInfo = (currentRow, index) => {
    // Sempre mostra na primeira linha da tabela
    if (index === 0) {
        return true;
    }
    // Compara o ID da entrada atual com o ID da entrada da linha anterior
    const previousRow = rows.value[index - 1];
    return currentRow.id !== previousRow.id;
};

// --- FUNÇÕES DE FILTRO E UI ---
const paramsFromRoute = () => {
    const q = new URLSearchParams(location.search);
    return {
        data_inicio: q.get('data_inicio') || '',
        data_fim: q.get('data_fim') || ''
    };
};

const filtrosAtivos = computed(() => {
    const p = route.query; // Directly use route.query
    const parts = [];
    // Add checks before accessing properties
    if (p && p.data_inicio) parts.push(`De: ${formatarData(p.data_inicio)}`);
    if (p && p.data_fim) parts.push(`Até: ${formatarData(p.data_fim)}`);
    return parts.length > 0 ? `Período: ${parts.join(' ')}` : 'Sem filtro de período';
});

// --- BUSCA DE DADOS ---
const fetchAll = async () => {
    loading.value = true;
    rows.value = [];
    // Use route.query directly here as well
    const p = route.query;
    const params = new URLSearchParams({ page_size: 100 });

    // Add checks before accessing properties
    if (p && p.data_inicio) params.set('data_inicio', p.data_inicio);
    if (p && p.data_fim) params.set('data_fim', p.data_fim);

    let nextUrl = `/doacoes-recebidas/?${params.toString()}`;
    const entradasBase = [];

    // ... (rest of the fetchAll logic remains the same) ...
     // 1. Busca todas as entradas (sem detalhes do doador ainda)
    while (nextUrl) {
        try {
            const r = await api.get(nextUrl);
            const resultados = r.data?.results ?? r.data ?? [];
            entradasBase.push(...resultados.filter(e => e.object_id)); // Filtra entradas sem object_id
            nextUrl = r.data?.next || null;
        } catch (error) {
            console.error("[RelatorioEntradas] Erro ao buscar lista de entradas:", error);
            nextUrl = null;
        }
    }

    // 2. Cria promessas para buscar os detalhes de cada doador
    const doadorPromises = entradasBase.map(entrada =>
        api.get(`/entidades/${entrada.object_id}/`)
           .then(response => response.data) // Pega os dados da entidade
           .catch(err => {
               console.warn(`[RelatorioEntradas] Falha ao buscar entidade ID ${entrada.object_id} para entrada ${entrada.id}:`, err);
               return null; // Retorna null se a busca da entidade falhar
           })
    );

    // 3. Executa todas as buscas de detalhes em paralelo
    const doadoresDetalhes = await Promise.all(doadorPromises);

    // 4. Combina os dados da entrada com os detalhes do doador e "achata" os itens
    const flattenedRows = [];
    entradasBase.forEach((entrada, index) => {
        const doadorDetalhado = doadoresDetalhes[index]; // Pega o doador correspondente

        if (Array.isArray(entrada.itens_doados) && entrada.itens_doados.length > 0) {
            entrada.itens_doados.forEach(itemDoado => {
                flattenedRows.push({
                    ...entrada, // Dados originais da entrada (id, data_doacao, observacoes)
                    doador: doadorDetalhado ? {
                         ...doadorDetalhado,
                         nome_fantasia: doadorDetalhado?.nome_fantasia || doadorDetalhado?.razao_social || entrada.doador_nome
                    } : { nome_fantasia: entrada.doador_nome },
                    item_nome: itemDoado.item?.nome || 'Item não encontrado',
                    item_quantidade: itemDoado.quantidade || 0
                });
            });
        } else {
             flattenedRows.push({
                ...entrada,
                 doador: doadorDetalhado ? {
                     ...doadorDetalhado,
                     nome_fantasia: doadorDetalhado?.nome_fantasia || doadorDetalhado?.razao_social || entrada.doador_nome
                 } : { nome_fantasia: entrada.doador_nome },
                item_nome: '-',
                item_quantidade: '-'
             });
        }
    });

    rows.value = flattenedRows;
    loading.value = false;
};

// const printNow = () => window.print(); // Se precisar do botão

onMounted(fetchAll);
</script>

<template>
  <ReportLayout title="Relatório — Entradas por Período" :subtitle="filtrosAtivos">
    <div v-if="loading">Carregando detalhes das entidades...</div>
    <div v-else>
      <table class="w-full report-table report-grouped">
        <thead>
          <tr>
            <th class="text-left p-2 border">Data</th>
            <th class="text-left p-2 border">Doador</th>
            <th class="text-left p-2 border">Classificação</th>
            <th class="text-left p-2 border">Categoria</th>
            <th class="text-left p-2 border">Bairro</th>
            <th class="text-left p-2 border">Telefone</th>
            <th class="text-left p-2 border">Email</th>
            <th class="text-left p-2 border">Item</th>
            <th class="text-right p-2 border">Qtd.</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in rows" :key="`${row.id}-${index}`">

            <td
              v-if="shouldShowEntradaInfo(row, index)"
              class="p-2 border group-start"
              :rowspan="rows.filter(r => r.id === row.id).length"
            >
              {{ formatarData(row.data_doacao) }}
            </td>
            <td
              v-if="shouldShowEntradaInfo(row, index)"
              class="p-2 border group-start"
              :rowspan="rows.filter(r => r.id === row.id).length"
            >
              {{ row.doador?.nome_fantasia || row.doador?.razao_social || '-' }}
            </td>
             <td
              v-if="shouldShowEntradaInfo(row, index)"
              class="p-2 border group-start"
              :rowspan="rows.filter(r => r.id === row.id).length"
            >
                <span v-if="row.doador?.eh_gestor && row.doador?.eh_doador">Gestor & Doador</span>
                <span v-else-if="row.doador?.eh_gestor">Gestor</span>
                <span v-else-if="row.doador?.eh_doador">Doador</span>
                <span v-else>-</span>
            </td>
             <td
              v-if="shouldShowEntradaInfo(row, index)"
              class="p-2 border group-start"
              :rowspan="rows.filter(r => r.id === row.id).length"
            >
                {{ row.doador?.categoria?.nome || '-' }}
            </td>
             <td
              v-if="shouldShowEntradaInfo(row, index)"
              class="p-2 border group-start"
              :rowspan="rows.filter(r => r.id === row.id).length"
            >
              {{ row.doador?.bairro || '-' }}
            </td>
             <td
              v-if="shouldShowEntradaInfo(row, index)"
              class="p-2 border group-start"
              :rowspan="rows.filter(r => r.id === row.id).length"
            >
                {{ getPrincipalContato(row.doador?.contatos, 'T', true) }}
            </td>
            <td
              v-if="shouldShowEntradaInfo(row, index)"
              class="p-2 border group-start"
              :rowspan="rows.filter(r => r.id === row.id).length"
            >
                {{ getPrincipalContato(row.doador?.contatos, 'E') }}
            </td>

            <td class="p-2 border">{{ row.item_nome }}</td>
            <td class="p-2 border text-right">{{ row.item_quantidade }}</td>
          </tr>
          <tr v-if="rows.length === 0">
              <td colspan="9" class="p-4 text-center border">Nenhuma entrada encontrada para o período selecionado.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </ReportLayout>
</template>

<style>
@media print {
    .no-print { display: none !important; }
    .card { box-shadow: none !important; }

    @page {
        size: A4 landscape;
        margin: 1cm;
    }

    body {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }
    .report-grouped tbody tr:first-child td.group-start {
        /* Borda superior na primeira linha do grupo (se for a primeira da tabela) */
        border-top: 1px solid #ccc;
    }
    .report-grouped tbody td.group-start {
        /* Borda superior mais grossa para iniciar um novo grupo */
        border-top: 2px solid #999;
        vertical-align: top; /* Alinha o conteúdo no topo da célula mesclada */
    }

    /* Remove borda superior das células de item/qtd quando NÃO for a primeira do grupo */
    .report-grouped tbody tr td:not(.group-start) {
        border-top: 1px solid #eee; /* Borda mais fina entre itens do mesmo grupo */
    }
    /* Garante que a primeira célula de item/qtd tenha a borda superior do grupo */
    .report-grouped tbody tr:has(td.group-start) td:not(.group-start) {
        border-top: 2px solid #999;
    } 
    .report-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 8pt; /* Talvez precise diminuir mais a fonte */
    }
    .report-table th, .report-table td {
        border: 1px solid #ccc;
        padding: 3px; /* Menor padding */
        word-break: break-word;
        vertical-align: top; /* Alinha no topo para linhas com muitos itens */
    }
    .report-table th {
        background-color: #f2f2f2;
  }
}
</style>