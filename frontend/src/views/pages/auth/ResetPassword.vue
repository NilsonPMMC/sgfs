<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '@/services/api.js';

// Hooks
const route = useRoute(); // Para pegar parâmetros da URL
const router = useRouter(); // Para navegar

// Variáveis reativas
const token = ref('');
const password = ref('');
const passwordConfirm = ref('');
const loading = ref(false);

// Variáveis para controlar os dialogs
const showDialog = ref(false);
const dialog = ref({
    title: '',
    message: '',
    isError: false
});

// Ao carregar o componente, pega o token da URL
onMounted(() => {
    token.value = route.params.token;
    if (!token.value) {
        // Se não houver token, mostra um erro e prepara para voltar ao login
        dialog.value = {
            title: 'Erro',
            message: 'Token de redefinição inválido ou ausente. Por favor, solicite um novo link.',
            isError: true
        };
        showDialog.value = true;
    }
});

// Função chamada quando o dialog é fechado
const handleDialogClose = () => {
    showDialog.value = false;
    router.push('/login'); // Sempre volta para o login após o dialog
};

// Função para redefinir a senha
const handleResetPassword = async () => {
    // Validação dos campos
    if (!password.value || !passwordConfirm.value) {
        dialog.value = { title: 'Atenção', message: 'Por favor, preencha ambos os campos de senha.', isError: true };
        showDialog.value = true;
        return;
    }
    if (password.value !== passwordConfirm.value) {
        dialog.value = { title: 'Atenção', message: 'As senhas não coincidem.', isError: true };
        showDialog.value = true;
        return;
    }

    loading.value = true;
    try {
        // A CHAMADA CORRETA PARA A API
        await api.post('/password_reset/confirm/', {
            token: token.value,
            password: password.value
        });
        
        // Sucesso
        dialog.value = {
            title: 'Sucesso!',
            message: 'Sua senha foi redefinida com sucesso. Você já pode fazer o login com a nova senha.',
            isError: false
        };
        showDialog.value = true;

    } catch (error) {
        // Erro (ex: token expirado ou inválido)
        console.error('Erro ao redefinir a senha:', error);
        dialog.value = {
            title: 'Erro na Redefinição',
            message: 'O link de redefinição é inválido ou já expirou. Por favor, solicite um novo.',
            isError: true
        };
        showDialog.value = true;
    } finally {
        loading.value = false;
    }
};
</script>

<template>
    <Dialog :header="dialog.title" v-model:visible="showDialog" :modal="true" :style="{ width: '50vw' }" :draggable="false">
        <p class="m-0">{{ dialog.message }}</p>
        <template #footer>
            <Button label="OK" icon="pi pi-check" @click="handleDialogClose" autofocus></Button>
        </template>
    </Dialog>

    <div class="bg-surface-50 dark:bg-surface-950 flex items-center justify-center min-h-screen min-w-[100vw] overflow-hidden">
        <div class="flex flex-col items-center justify-center">
            <div style="border-radius: 56px; padding: 0.3rem; background: linear-gradient(180deg, var(--primary-color) 10%, rgba(33, 150, 243, 0) 30%)">
                <div class="w-full bg-surface-0 dark:bg-surface-900 py-20 px-8 sm:px-20" style="border-radius: 53px">
                    <div class="text-center mb-8">
                        <div class="sgfs-logo">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-label="Logo SGFS"><defs><radialGradient id="g-body" cx="256" cy="340.62" fx="256" fy="381.29" r="163.12" gradientTransform="translate(0 26.14) scale(1 .92)" gradientUnits="userSpaceOnUse"><stop offset=".4" stop-color="#b40d60"/><stop offset=".69" stop-color="#da1f75"/></radialGradient><linearGradient id="g-head" x1="255.4" y1="151.59" x2="255.4" y2="-2.5" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#d52075"/><stop offset="1" stop-color="#f08b30"/></linearGradient></defs><path fill="url(#g-body)" d="M222.48 498.94c-44.7 43.62-116.95-37.3-135.88-76.18-47.71-98 5.15-208.64 105.55-243.11 137.64-47.25 288.71 73.42 242.5 219.45-13.16 41.6-56.16 96.71-98.72 110.38-42.25 13.58-73.67-30.47-55.54-68.72 13.67-28.84 52.53-37.07 63.64-71.37 12.68-39.12-20.74-74.96-60.93-60.94-8.01 2.79-18.49 12.8-24.62 13.36-9.86.9-13.37-6.35-21.14-10.29-43.27-21.96-84.08 17.78-67.76 61.18 12.42 33.03 50.12 40.48 62.51 70.86 7.83 19.18 5.6 40.53-9.61 55.37Z"/><path fill="url(#g-head)" d="M246.97 155.38c115.25 10.31 114.69-170.76-6.19-154.32-85.52 11.63-82.91 146.35 6.19 154.32Z"/></svg>
                        </div>
                        <div class="text-surface-900 dark:text-surface-0 text-3xl font-medium mb-4">Redefinir Senha</div>
                        <span class="text-muted-color font-medium">Digite sua nova senha</span>
                    </div>

                    <form @submit.prevent="handleResetPassword">
                        <label for="password" class="block text-surface-900 dark:text-surface-0 font-medium text-xl mb-2">Nova Senha</label>
                        <Password id="password" v-model="password" :toggleMask="true" class="mb-4" fluid :feedback="true"></Password>
                        
                        <label for="passwordConfirm" class="block text-surface-900 dark:text-surface-0 font-medium text-xl mb-2">Confirmar Nova Senha</label>
                        <Password id="passwordConfirm" v-model="passwordConfirm" :toggleMask="true" class="mb-8" fluid :feedback="false"></Password>

                        <Button label="Salvar Nova Senha" class="w-full" type="submit" :loading="loading"></Button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
/* Seu CSS aqui */
.sgfs-logo { display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; }
.sgfs-logo svg { width: 80px; height: 80px; }
</style>