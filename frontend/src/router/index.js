import { createRouter, createWebHistory } from 'vue-router';
import AppLayout from '@/layout/AppLayout.vue';
import ReportBlankLayout from '@/layout/ReportBlankLayout.vue';

const router = createRouter({
    history: createWebHistory(),
    routes: [
        // 1. Rota raiz redireciona para o login
        {
            path: '/',
            redirect: '/login'
        },

        // 2. Grupo de rotas da aplicação que exigem login e usam o layout principal
        {
            path: '/app', // Usamos um prefixo como '/app' para clareza
            component: AppLayout,
            meta: { requiresAuth: true }, // Adiciona a exigência de autenticação a todo o grupo
            children: [
                {
                    path: '', // Acessado em /app, redireciona para o dashboard
                    redirect: '/app/dashboard'
                },
                {
                    path: 'dashboard',
                    name: 'dashboard',
                    component: () => import('@/views/Dashboard.vue')
                },
                {
                    path: 'entidades',
                    name: 'entidades',
                    component: () => import('@/views/pages/Entidades.vue')
                },
                {
                    path: 'entidades/:id',
                    name: 'detalhes-entidade',
                    component: () => import('@/views/pages/DetalhesEntidade.vue'),
                    props: true // Passa o :id como prop para o componente
                },
                {
                    path: 'agenda',
                    name: 'agenda',
                    component: () => import('@/views/pages/AgendaContatos.vue')
                },
                {
                    path: 'itens',
                    name: 'gestao-itens',
                    component: () => import('@/views/pages/GestaoItens.vue')
                },
                {
                    path: 'kits',
                    name: 'gestao-kits',
                    component: () => import('@/views/pages/GestaoKits.vue')
                },
                {
                    path: 'estoque',
                    name: 'controle-estoque',
                    component: () => import('@/views/pages/ControleEstoque.vue')
                },
                {
                    path: 'doacoes/entradas',
                    name: 'ListaEntradas',
                    component: () => import('@/views/pages/Entradas.vue')
                },
                {
                    path: 'doacoes/saidas',
                    name: 'ListaSaidas',
                    component: () => import('@/views/pages/Saidas.vue')
                },
                {
                    path: 'doacoes/entrada',
                    name: 'EntradaDoacao',
                    component: () => import('@/views/pages/EntradaDoacao.vue')
                },
                {
                    path: 'doacoes/entrada/:id',
                    name: 'EditarEntradaDoacao',
                    component: () => import('@/views/pages/EntradaDoacao.vue'),
                    props: true
                },
                {
                    path: 'doacoes/saida',
                    name: 'SaidaDoacao',
                    component: () => import('@/views/pages/SaidaDoacao.vue')
                },
                {
                    path: 'doacoes/saida/:id',
                    name: 'EditarSaidaDoacao',
                    component: () => import('@/views/pages/SaidaDoacao.vue'),
                    props: true
                }
            ]
        },

        // 3. Grupo de rotas de Relatórios (layout diferente, mas também exige login)
        {
            path: '/relatorios',
            component: ReportBlankLayout,
            meta: { requiresAuth: true },
            children: [
                { path: 'entidades', name: 'RelatorioEntidades', component: () => import('@/views/relatorios/RelatorioEntidades.vue') },
                { path: 'entidade/:id', name: 'RelatorioEntidade', component: () => import('@/views/relatorios/RelatorioEntidade.vue'), props: true },
                { path: 'entrada/:id', name: 'RelatorioEntrada', component: () => import('@/views/relatorios/RelatorioEntrada.vue'), props: true },
                { path: 'saida/:id', name: 'RelatorioSaida', component: () => import('@/views/relatorios/RelatorioSaida.vue'), props: true }
            ]
        },

        // 4. Rotas públicas (não exigem login)
        {
            path: '/login',
            name: 'login',
            component: () => import('@/views/pages/auth/Login.vue')
        },
        {
            path: '/forgot-password',
            name: 'forgotPassword',
            component: () => import('@/views/pages/auth/ForgotPassword.vue')
        },
        {
            path: '/reset-password/:token',
            name: 'resetPassword',
            component: () => import('@/views/pages/auth/ResetPassword.vue'),
            props: true
        },
        {
            path: '/:catchAll(.*)', // Captura qualquer rota não encontrada
            name: 'notfound',
            component: () => import('@/views/pages/NotFound.vue')
        }
    ]
});

// 5. Guarda de Navegação (ESSENCIAL PARA SEGURANÇA)
router.beforeEach((to, from, next) => {
    // Verifica se a rota para a qual o usuário está navegando exige autenticação
    const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
    const isAuthenticated = !!localStorage.getItem('accessToken');

    if (requiresAuth && !isAuthenticated) {
        // Se a rota exige login e o usuário não está logado, redireciona para o login
        next({ name: 'login' });
    } else if (to.name === 'login' && isAuthenticated) {
        // Se o usuário já está logado e tenta acessar a página de login, redireciona para o dashboard
        next({ name: 'dashboard' });
    }
    else {
        // Caso contrário, permite a navegação
        next();
    }
});

export default router;