// src/services/api.js
import axios from 'axios';

const api = axios.create({
    baseURL: '/api'
});

// A MÁGICA ACONTECE AQUI: Request Interceptor
// Este código será executado ANTES de cada requisição ser enviada.
api.interceptors.request.use(
    (config) => {
        // Pega o token de acesso do localStorage
        const token = localStorage.getItem('accessToken');
        
        // Se o token existir, anexa ele ao header de autorização
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        
        return config;
    },
    (error) => {
        // Faz algo com o erro da requisição
        return Promise.reject(error);
    }
);

export default api;