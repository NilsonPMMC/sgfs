import axios from 'axios';

const api = axios.create({
    baseURL: '/api'
});

// INTERCEPTOR DE REQUISIÇÃO (Request Interceptor)
// Este código já existe e está correto. Ele anexa o token a cada requisição.
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('accessToken');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// NOVO!! INTERCEPTOR DE RESPOSTA (Response Interceptor)
// Este código será executado DEPOIS de cada resposta da API ser recebida.
api.interceptors.response.use(
    (response) => {
        // Se a resposta for bem-sucedida (status 2xx), apenas a retorna.
        return response;
    },
    async (error) => {
        // Se a resposta for um erro...
        const originalRequest = error.config;

        // Verificamos se o erro é um 401 (Não Autorizado)
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true; // Evita loops infinitos de logout

            // Importamos a store de autenticação aqui dentro para evitar problemas
            // de dependência circular.
            const { useAuthStore } = await import('@/store/auth');
            const authStore = useAuthStore();

            // Chamamos a ação de logout que já criamos!
            // Ela limpa o localStorage e redireciona para a página de login.
            console.warn('Token expirado ou inválido. Fazendo logout...');
            authStore.logout();
        }

        // Para qualquer outro erro, apenas o rejeita para que o '.catch()' local possa lidar com ele.
        return Promise.reject(error);
    }
);

export default api;