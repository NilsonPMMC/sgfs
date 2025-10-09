// src/store/auth.js
import { defineStore } from 'pinia';
import api from '@/services/api.js'; 
import router from '@/router'; // Importe o router

export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: null
    }),
    getters: {
        isAuthenticated: (state) => !!state.user,
        hasPermission: (state) => (permissionCodename) => {
            return state.user?.permissions?.includes(permissionCodename);
        }
    },
    actions: {
        async fetchUser() {
            try {
                const response = await api.get('/users/me/');
                this.user = response.data;
            } catch (error) {
                this.user = null;
                localStorage.removeItem('accessToken');
                localStorage.removeItem('refreshToken');
                console.error('Não foi possível buscar os dados do usuário.', error);
            }
        },

        // ADICIONE ESTA NOVA AÇÃO
        logout() {
            // 1. Limpa os dados do usuário da store
            this.user = null;

            // 2. Remove os tokens do localStorage
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');

            // 3. (CRUCIAL) Remove o header de autorização da nossa instância 'api'
            delete api.defaults.headers.common['Authorization'];

            // 4. Redireciona para a tela de login
            router.push('/login');
        }
    }
});