// src/App.vue
<script setup>
import { onMounted } from 'vue';
import { useAuthStore } from '@/store/auth';
import { useRoute } from 'vue-router';

onMounted(async () => {
    const authStore = useAuthStore();
    const route = useRoute();
    const accessToken = localStorage.getItem('accessToken');

    const publicRoutes = ['login', 'forgotPassword', 'resetPassword', 'notfound'];

    if (accessToken && !publicRoutes.includes(route.name)) {
        await authStore.fetchUser();
    }
});
</script>
<template>
    <router-view />
</template>

<style scoped></style>
