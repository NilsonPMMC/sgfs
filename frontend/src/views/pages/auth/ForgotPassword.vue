<script setup>
import { ref } from 'vue';
import api from '@/services/api';
import { useToast } from 'primevue/usetoast';
const email = ref('');
const loading = ref(false);
const toast = useToast();

const submit = async () => {
  loading.value = true;
  try {
    await api.post('auth/password/reset/', { email: email.value });
    toast.add({ severity:'success', summary:'OK', detail:'Se o e-mail existir, enviamos o link.', life:4000 });
  } finally { loading.value = false; }
};
</script>
<template>
  <div class="card max-w-md mx-auto">
    <h3>Esqueci minha senha</h3>
    <div class="mb-3">
      <label class="block mb-2">E-mail</label>
      <InputText v-model="email" type="email" fluid />
    </div>
    <Button :loading="loading" label="Enviar link" @click="submit" />
  </div>
</template>
