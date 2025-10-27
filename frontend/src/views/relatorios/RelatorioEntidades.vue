<script setup>
import { ref, onMounted, computed } from 'vue';
import api from '@/services/api';
import ReportLayout from '@/views/reports/ReportLayout.vue';

const rows = ref([]);
const loading = ref(true);

// --- FUNÇÕES DE FILTRO E UI ---
const paramsFromRoute = () => {
    const q = new URLSearchParams(location.search);
    return {
        classificacao: q.get('classificacao') || '',
        categoria: q.get('categoria') || '',
        bairro: q.get('bairro') || '',
        search: q.get('search') || ''
    };
};

const filtrosAtivos = computed(() => {
    const p = paramsFromRoute();
    const parts = [];
    if (p.classificacao) parts.push(`Classificação: ${p.classificacao}`);
    if (p.categoria) parts.push(`Categoria: ${p.categoria}`);
    if (p.bairro) parts.push(`Bairro: ${p.bairro}`);
    if (p.search) parts.push(`Busca: "${p.search}"`);
    return parts.join(' • ') || 'Sem filtros';
});

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
    if (!Array.isArray(contatos) || contatos.length === 0) {
        return '-';
    }

    const contatosDoTipo = contatos.filter(c => c.tipo_contato === tipo);

    if (contatosDoTipo.length === 0) {
        return '-';
    }

    // Tenta encontrar um contato cuja descrição contenha "principal"
    const principal = contatosDoTipo.find(c =>
        c.descricao && c.descricao.toLowerCase().includes('principal')
    );

    const valor = principal ? principal.valor : contatosDoTipo[0].valor;

    // Aplica máscara se for telefone e solicitado
    if (tipo === 'T' && usarMascara) {
        return maskPhone(valor);
    }
    
    return valor || '-'; // Retorna o valor ou '-' se estiver vazio
};

// --- BUSCA DE DADOS ---
const fetchAll = async () => {
    loading.value = true;
    rows.value = [];

    // 3. CONSTRUÍMOS A URL INICIAL COM CAMINHO RELATIVO E PARÂMETROS
    const p = paramsFromRoute();
    const params = new URLSearchParams({ page_size: 100 });
    if (p.classificacao) params.set('classificacao', p.classificacao);
    if (p.categoria) params.set('categoria', p.categoria);
    if (p.bairro) params.set('bairro', p.bairro);
    if (p.search) params.set('search', p.search);
    
    let nextUrl = `/entidades/?${params.toString()}`;

    while (nextUrl) {
        try {
            // 4. USAMOS 'api.get'
            const r = await api.get(nextUrl);
            rows.value.push(...(r.data?.results ?? r.data ?? []));
            // 5. USAMOS A URL COMPLETA RETORNADA PELA API PARA PAGINAÇÃO
            nextUrl = r.data?.next || null; 
        } catch (error) {
            console.error("Erro ao buscar relatório de entidades:", error);
            nextUrl = null; // Encerra o loop em caso de erro
        }
    }
    loading.value = false;
};

const printNow = () => window.print();

onMounted(fetchAll);
</script>

<template>
  <ReportLayout title="Relatório — Entidades" :subtitle="filtrosAtivos">

    <div v-if="loading">Carregando…</div>
    <div v-else>
      <table class="w-full report-table">
        <thead>
          <tr>
            <th class="text-left p-2 border">Nome</th>
            <th class="text-left p-2 border">Classificação</th>
            <th class="text-left p-2 border">Categoria</th>
            <th class="text-left p-2 border">Bairro</th>
            <th class="text-left p-2 border">Telefone</th>
            <th class="text-left p-2 border">Email</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in rows" :key="e.id">
            <td class="p-2 border">{{ e.nome_fantasia || e.razao_social || e.nome }}</td>
            <td class="p-2 border">
              <span v-if="e.eh_gestor && e.eh_doador">Gestor & Doador</span>
              <span v-else-if="e.eh_gestor">Gestor</span>
              <span v-else-if="e.eh_doador">Doador</span>
              <span v-else>-</span>
            </td>
            <td class="p-2 border">{{ e.categoria?.nome || '-' }}</td>
            <td class="p-2 border">{{ e.bairro || '-' }}</td>
            <td class="p-2 border">{{ getPrincipalContato(e.contatos, 'T', true) }}</td> 
            <td class="p-2 border">{{ getPrincipalContato(e.contatos, 'E') }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </ReportLayout>
</template>

<style>
/* Estilos existentes para no-print e card */
@media print {
  .no-print { display: none !important; }
  .card { box-shadow: none !important; }

  /* Configuração da página para paisagem */
  @page {
    size: A4 landscape; /* Define o tamanho como A4 e a orientação como paisagem */
    margin: 1cm; /* Ajuste as margens conforme necessário */
  }

  /* Opcional: Ajustes finos na tabela para impressão */
  body {
    -webkit-print-color-adjust: exact; /* Força impressão de cores de fundo/bordas no Chrome */
    print-color-adjust: exact;
  }
  .report-table {
    width: 100%;
    border-collapse: collapse; /* Garante que as bordas fiquem juntas */
    font-size: 9pt; /* Reduz um pouco a fonte para caber mais */
  }
  .report-table th, .report-table td {
    border: 1px solid #ccc; /* Garante bordas visíveis na impressão */
    padding: 4px; /* Reduz o padding */
    word-break: break-word; /* Quebra palavras longas se necessário */
  }
  .report-table th {
      background-color: #f2f2f2; /* Cor de fundo leve para cabeçalho */
  }
}
</style>
