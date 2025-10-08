<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import { useAuthStore } from '@/store/auth';
import api from '@/services/api.js'; // 1. Usamos nosso serviço de API centralizado

// Hooks e stores
const router = useRouter();
const toast = useToast();
const authStore = useAuthStore();

// Variáveis reativas para o formulário
const username = ref('');
const password = ref('');
const checked = ref(false); // Para o checkbox "Lembrar"
const loading = ref(false);

// Função para o link "Esqueceu sua senha?"
const goToForgotPassword = () => {
    router.push('/forgot-password'); // Navega para a rota de recuperação
};

// Função principal de login
const handleLogin = async () => {
    loading.value = true;
    try {
        const response = await api.post('/token/', {
            username: username.value,
            password: password.value
        });
        
        const { access, refresh } = response.data;

        // Guarda os tokens (o interceptor vai usar o 'accessToken')
        localStorage.setItem('accessToken', access);
        localStorage.setItem('refreshToken', refresh);
        
        // A LINHA ABAIXO FOI REMOVIDA - O INTERCEPTOR FAZ ISSO AGORA!
        // api.defaults.headers.common['Authorization'] = `Bearer ${access}`;
        
        await authStore.fetchUser();

        if (checked.value) {
            localStorage.setItem('rememberedUsername', username.value);
        } else {
            localStorage.removeItem('rememberedUsername');
        }

        router.push('/');

    } catch (error) {
        console.error("Erro no login:", error);
        password.value = '';
        toast.add({ severity: 'error', summary: 'Erro de Autenticação', detail: 'Usuário ou senha inválidos.', life: 4000 });
    } finally {
        loading.value = false;
    }
};

// 5. Lógica para preencher o usuário ao carregar a página
onMounted(() => {
    const rememberedUser = localStorage.getItem('rememberedUsername');
    if (rememberedUser) {
        username.value = rememberedUser;
        checked.value = true;
    }
});
</script>

<template>
    <FloatingConfigurator />
    <div class="bg-surface-50 dark:bg-surface-950 flex items-center justify-center min-h-screen min-w-[100vw] overflow-hidden">
        <div class="flex flex-col items-center justify-center">
            <div style="border-radius: 56px; padding: 0.3rem; background: linear-gradient(180deg, var(--primary-color) 10%, rgba(33, 150, 243, 0) 30%)">
                <div class="w-full bg-surface-0 dark:bg-surface-900 py-20 px-8 sm:px-20" style="border-radius: 53px">
                    <div class="text-center mb-8">
                        <div class="sgfs-logo">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-label="Logo SGFS">
                                <defs>
                                    <radialGradient id="g-body" cx="256" cy="340.62" fx="256" fy="381.29" r="163.12" gradientTransform="translate(0 26.14) scale(1 .92)" gradientUnits="userSpaceOnUse">
                                        <stop offset=".4" stop-color="#b40d60"/>
                                        <stop offset=".69" stop-color="#da1f75"/>
                                    </radialGradient>
                                    <linearGradient id="g-head" x1="255.4" y1="151.59" x2="255.4" y2="-2.5" gradientUnits="userSpaceOnUse">
                                        <stop offset="0" stop-color="#d52075"/>
                                        <stop offset="1" stop-color="#f08b30"/>
                                    </linearGradient>
                                </defs>
                                <path fill="url(#g-body)" d="M222.48 498.94c-44.7 43.62-116.95-37.3-135.88-76.18-47.71-98 5.15-208.64 105.55-243.11 137.64-47.25 288.71 73.42 242.5 219.45-13.16 41.6-56.16 96.71-98.72 110.38-42.25 13.58-73.67-30.47-55.54-68.72 13.67-28.84 52.53-37.07 63.64-71.37 12.68-39.12-20.74-74.96-60.93-60.94-8.01 2.79-18.49 12.8-24.62 13.36-9.86.9-13.37-6.35-21.14-10.29-43.27-21.96-84.08 17.78-67.76 61.18 12.42 33.03 50.12 40.48 62.51 70.86 7.83 19.18 5.6 40.53-9.61 55.37Z"/>
                                <path fill="url(#g-head)" d="M246.97 155.38c115.25 10.31 114.69-170.76-6.19-154.32-85.52 11.63-82.91 146.35 6.19 154.32Z"/>
                            </svg>
                        </div>
                        <div class="text-surface-900 dark:text-surface-0 text-3xl font-medium mb-4">SGFS</div>
                        <span class="text-muted-color font-medium">Faça login para continuar</span>
                    </div>

                    <form @submit.prevent="handleLogin">
                        <label for="username" class="block text-surface-900 dark:text-surface-0 text-xl font-medium mb-2">Usuário</label>
                        <InputText id="username" v-model="username" type="text" class="w-full md:w-[30rem] mb-8" />

                        <label for="password" class="block text-surface-900 dark:text-surface-0 font-medium text-xl mb-2">Senha</label>
                        <Password id="password" v-model="password" placeholder="Password" :toggleMask="true" class="mb-4" fluid :feedback="false"></Password>

                        <div class="flex items-center justify-between mt-2 mb-8 gap-8">
                            <div class="flex items-center">
                                <Checkbox v-model="checked" id="rememberme1" binary class="mr-2"></Checkbox>
                                <label for="rememberme1">Lembrar</label>
                            </div>
                            <span @click="goToForgotPassword" class="font-medium no-underline ml-2 text-right cursor-pointer text-primary">Esqueceu sua senha?</span>
                        </div>
                        <Button label="Entrar" class="w-full" type="submit" :loading="loading"></Button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
/* Seu CSS aqui */
.sgfs-logo {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1rem;
}
.sgfs-logo svg {
    width: 80px;
    height: 80px;
}
.pi-eye {
    transform: scale(1.6);
    margin-right: 1rem;
}

.pi-eye-slash {
    transform: scale(1.6);
    margin-right: 1rem;
}
</style>