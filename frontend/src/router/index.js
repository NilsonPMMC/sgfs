import AppLayout from '@/layout/AppLayout.vue';
import ReportBlankLayout from '@/layout/ReportBlankLayout.vue';
import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            component: AppLayout,
            children: [
                {
                    path: '/',
                    name: 'dashboard',
                    component: () => import('@/views/Dashboard.vue')
                },
                {
                    path: '/entidades',
                    name: 'entidades',
                    component: () => import('@/views/pages/Entidades.vue')
                },
                {
                    path: '/entidades/:id',
                    name: 'detalhes-entidade',
                    component: () => import('@/views/pages/DetalhesEntidade.vue')
                },
                {
                    path: '/agenda',
                    name: 'agenda',
                    component: () => import('@/views/pages/AgendaContatos.vue')
                },
                {
                    path: '/itens',
                    name: 'gestao-itens',
                    component: () => import('@/views/pages/GestaoItens.vue')
                },
                {
                    path: '/kits',
                    name: 'gestao-kits',
                    component: () => import('@/views/pages/GestaoKits.vue')
                },
                {
                    path: '/estoque',
                    name: 'controle-estoque',
                    component: () => import('@/views/pages/ControleEstoque.vue')
                },
                {
                    path: '/doacoes/entradas',
                    name: 'ListaEntradas',
                    component: () => import('@/views/pages/Entradas.vue')
                },
                {
                    path: '/doacoes/saidas',
                    name: 'ListaSaidas',
                    component: () => import('@/views/pages/Saidas.vue')
                },                  
                {
                    path: '/doacoes/entrada',
                    name: 'EntradaDoacao',
                    component: () => import('@/views/pages/EntradaDoacao.vue')
                },
                {
                    path: '/doacoes/entrada/:id',
                    name: 'EditarEntradaDoacao',
                    component: () => import('@/views/pages/EntradaDoacao.vue')
                },
                {
                    path: '/doacoes/saida',
                    name: 'SaidaDoacao',
                    component: () => import('@/views/pages/SaidaDoacao.vue')
                },
                {
                    path: '/doacoes/saida/:id',
                    name: 'EditarSaidaDoacao',
                    component: () => import('@/views/pages/SaidaDoacao.vue')
                },
                {
                    path: '/uikit/formlayout',
                    name: 'formlayout',
                    component: () => import('@/views/uikit/FormLayout.vue')
                },
                {
                    path: '/uikit/input',
                    name: 'input',
                    component: () => import('@/views/uikit/InputDoc.vue')
                },
                {
                    path: '/uikit/button',
                    name: 'button',
                    component: () => import('@/views/uikit/ButtonDoc.vue')
                },
                {
                    path: '/uikit/table',
                    name: 'table',
                    component: () => import('@/views/uikit/TableDoc.vue')
                },
                {
                    path: '/uikit/list',
                    name: 'list',
                    component: () => import('@/views/uikit/ListDoc.vue')
                },
                {
                    path: '/uikit/tree',
                    name: 'tree',
                    component: () => import('@/views/uikit/TreeDoc.vue')
                },
                {
                    path: '/uikit/panel',
                    name: 'panel',
                    component: () => import('@/views/uikit/PanelsDoc.vue')
                },

                {
                    path: '/uikit/overlay',
                    name: 'overlay',
                    component: () => import('@/views/uikit/OverlayDoc.vue')
                },
                {
                    path: '/uikit/media',
                    name: 'media',
                    component: () => import('@/views/uikit/MediaDoc.vue')
                },
                {
                    path: '/uikit/message',
                    name: 'message',
                    component: () => import('@/views/uikit/MessagesDoc.vue')
                },
                {
                    path: '/uikit/file',
                    name: 'file',
                    component: () => import('@/views/uikit/FileDoc.vue')
                },
                {
                    path: '/uikit/menu',
                    name: 'menu',
                    component: () => import('@/views/uikit/MenuDoc.vue')
                },
                {
                    path: '/uikit/charts',
                    name: 'charts',
                    component: () => import('@/views/uikit/ChartDoc.vue')
                },
                {
                    path: '/uikit/misc',
                    name: 'misc',
                    component: () => import('@/views/uikit/MiscDoc.vue')
                },
                {
                    path: '/uikit/timeline',
                    name: 'timeline',
                    component: () => import('@/views/uikit/TimelineDoc.vue')
                },
                {
                    path: '/pages/empty',
                    name: 'empty',
                    component: () => import('@/views/pages/Empty.vue')
                },
                {
                    path: '/pages/crud',
                    name: 'crud',
                    component: () => import('@/views/pages/Crud.vue')
                },
                {
                    path: '/documentation',
                    name: 'documentation',
                    component: () => import('@/views/pages/Documentation.vue')
                }
            ]
        },
        {
            path: '/relatorios',
            component: ReportBlankLayout,
            children: [
              { path: 'entidades', name: 'RelatorioEntidades', component: () => import('@/views/relatorios/RelatorioEntidades.vue') },
              { path: 'entidade/:id', name: 'RelatorioEntidade', component: () => import('@/views/relatorios/RelatorioEntidade.vue') },
              { path: 'entrada/:id', name: 'RelatorioEntrada', component: () => import('@/views/relatorios/RelatorioEntrada.vue') },
              { path: 'saida/:id',   name: 'RelatorioSaida',   component: () => import('@/views/relatorios/RelatorioSaida.vue') }
            ]
        },
        {
            path: '/landing',
            name: 'landing',
            component: () => import('@/views/pages/Landing.vue')
        },
        {
            path: '/pages/notfound',
            name: 'notfound',
            component: () => import('@/views/pages/NotFound.vue')
        },

        {
            path: '/login',
            name: 'login',
            component: () => import('@/views/pages/auth/Login.vue')
        },
        {
            path: '/auth/access',
            name: 'accessDenied',
            component: () => import('@/views/pages/auth/Access.vue')
        },
        {
            path: '/auth/error',
            name: 'error',
            component: () => import('@/views/pages/auth/Error.vue')
        }
    ]
});

export default router;
