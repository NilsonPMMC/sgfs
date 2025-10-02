// src/App.vue
<script setup>
import { onMounted } from 'vue';
import { useAuthStore } from '@/store/auth';

const authStore = useAuthStore();
onMounted(() => {
    authStore.fetchUser();
});
</script>
<template>
    <router-view />
</template>

<style scoped></style>
