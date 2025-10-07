<script setup>
import { ref } from 'vue';

import AppMenuItem from './AppMenuItem.vue';

const model = ref([
    {
        label: 'Home',
        items: [{ label: 'Dashboard', icon: 'pi pi-fw pi-home', to: '/' }]
    },
    {
        label: 'Módulos',
        items: [
            { label: 'Entidades', icon: 'pi pi-fw pi-building', to: '/entidades' },
            { label: 'Contatos', icon: 'pi pi-fw pi-users', to: '/agenda' },
            {
                label: 'Itens e Kits',
                icon: 'pi pi-fw pi-barcode',
                items: [
                            { label: 'Itens', icon: 'pi pi-fw pi-barcode', to: '/itens' },
                            { label: 'Kits', icon: 'pi pi-fw pi-box', to: '/kits' }
                        ]
            },
            {
                label: 'Doações',
                icon: 'pi pi-fw pi-box',
                items: [
                            { label: 'Entradas', icon: 'pi pi-fw pi-arrow-down', to: '/doacoes/entradas' },
                            { label: 'Saídas', icon: 'pi pi-fw pi-arrow-up', to: '/doacoes/saidas' }
                        ]
            }
        ]
    }
]);
</script>

<template>
    <ul class="layout-menu">
        <template v-for="(item, i) in model" :key="item">
            <app-menu-item v-if="!item.separator" :item="item" :index="i"></app-menu-item>
            <li v-if="item.separator" class="menu-separator"></li>
        </template>
    </ul>
</template>

<style lang="scss" scoped></style>
