<script setup>
import { ref, onMounted } from 'vue';
import api from '@/services/api';
import { useToast } from 'primevue/usetoast';

const toast = useToast();
const newPassword = ref('');
const confirmPassword = ref('');
const uid = ref('');
const token = ref('');
const loading = ref(false);

onMounted(() => {
  const q = new URLSearchParams(location.search);
  uid.value = q.get('uid') || '';
  token.value = q.get('token') || '';
});

const submit = async () => {
  if (newPassword.value !== confirmPassword.value) {
    toast.add({ severity:'warn', summary:'Atenção', detail:'Senhas não coincidem.' });
    return;
  }
  loading.value = true;
  try {
    await api.post('auth/password/reset/confirm/', {
      uid: uid.value, token: token.value, new_password: newPassword.value
    });
    toast.add({ severity:'success', summary:'OK', detail:'Senha redefinida. Faça login.' });
    setTimeout(() => location.href = '/login', 1200);
  } catch (e) {
    toast.add({ severity:'error', summary:'Erro', detail:'Link inválido ou expirado.' });
  } finally { loading.value = false; }
};
</script>
<template>
  <div class="card max-w-md mx-auto">
    <h3>Redefinir senha</h3>
    <div class="mb-3">
      <label class="block mb-2">Nova senha</label>
      <Password v-model="newPassword" toggleMask fluid />
    </div>
    <div class="mb-3">
      <label class="block mb-2">Confirmar senha</label>
      <Password v-model="confirmPassword" toggleMask feedback="false" fluid />
    </div>
    <Button :loading="loading" label="Salvar" @click="submit" />
  </div>
</template>
