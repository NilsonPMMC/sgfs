<!-- src/layout/ReportBlankLayout.vue -->
<template>
  <!-- NADA de topbar/sidebar aqui -->
  <main class="p-4 print:p-0">
    <router-view />
  </main>
</template>

<style>
/* Somente estilos de impressão essenciais */
@media print {
  body { background: #fff !important; }
  .card { box-shadow: none !important; }
  /* margens do navegador */
  @page { margin: 12mm; }
}
</style>
