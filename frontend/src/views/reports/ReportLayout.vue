<script setup>
const props = defineProps({
  title: { type: String, default: 'Relatório' },
  subtitle: { type: String, default: '' },
  noPrintButton: { type: Boolean, default: false }
});
const printNow = () => window.print();
</script>

<template>
  <div class="report">
    <header class="report__header">
      <div class="brand">
        <img src="@/assets/logo.svg" alt="Logo" class="report-logo" />
      </div>
      <div class="titles">
        <h2>{{ title }}</h2>
        <p v-if="subtitle" class="subtitle">{{ subtitle }}</p>
      </div>
      <div v-if="!noPrintButton" class="actions no-print">
        <Button icon="pi pi-print" label="Imprimir / PDF" @click="printNow" />
      </div>
    </header>

    <main class="report__content">
      <slot />
    </main>

    <footer class="report__footer">
      <small>SGFS • Gerado em: {{ new Date().toLocaleString() }}</small>
      <small class="page-number print-only">Página <span class="counter"></span></small>
    </footer>
  </div>
</template>

<style scoped>
.report { max-width: 1024px; margin: 0 auto; }
.report__header {
  display: grid; grid-template-columns: auto 1fr auto; gap: 1rem; align-items: center;
  border-bottom: 1px solid var(--surface-border); padding-bottom: .75rem; margin-bottom: 1rem;
}
.brand { display:flex; gap:.75rem; align-items:center; }
.brand img { height:50px }
.titles h2 { margin:0 }
.subtitle { color: var(--text-color-secondary); margin:.25rem 0 0 }
.when { color: var(--text-color-secondary); font-size:.875rem; margin:.25rem 0 0 }
.report__content { padding: .5rem 0 2rem; }
.report__footer {
  display:flex; justify-content:space-between; color: var(--text-color-secondary);
  border-top: 1px solid var(--surface-border); padding-top: .5rem; margin-top: 1rem;
}
.no-print { display: inline-flex; }
.print-only { display: none; }
.report-logo {
  width: 120px;
  margin-bottom: 1rem;
}

/* impressão */
@media print {
  .no-print { display: none !important; }
  .print-only { display: inline; }
  .report { max-width: none; }
  .report-logo { margin-bottom: 0.5rem; }
  @page { 
    margin: 12mm;
    size: auto;
    }
  .counter:after { counter-increment: page; content: counter(page); }
  body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  html::before,
  html::after,
  body::before,
  body::after {
    display: none !important;
    content: none !important;
  }
}
</style>