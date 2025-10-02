// src/store/auth.js
import { defineStore } from 'pinia';
import axios from 'axios';

export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: null,
    }),
    getters: {
        isAuthenticated: (state) => !!state.user,
        // Getter que verifica se o usuário tem uma permissão específica
        hasPermission: (state) => (permissionCodename) => {
            return state.user?.permissions?.includes(permissionCodename);
        }
    },
    actions: {
        async fetchUser() {
            try {
                const response = await axios.get('http://127.0.0.1:8005/api/users/me/');
                this.user = response.data;
            } catch (error) {
                this.user = null;
                console.error("Não foi possível buscar os dados do usuário.", error);
            }
        }
    }
});