<script setup>
import { ref } from 'vue';
import { useLayout } from '@/layout/composables/layout';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/store/auth';
import axios from 'axios';
import AppConfigurator from './AppConfigurator.vue';
import NotificationBell from '@/components/NotificationBell.vue';

const { toggleMenu, toggleDarkMode, isDarkTheme, onMenuToggle } = useLayout();
const router = useRouter();
const authStore = useAuthStore();
const op = ref();
const us = ref();

const handleLogout = () => {
    authStore.logout();
};
</script>

<template>
    <div class="layout-topbar">
        <div class="layout-topbar-logo-container">
            <button class="layout-menu-button layout-topbar-action" @click="toggleMenu">
                <i class="pi pi-bars"></i>
            </button>
            <router-link to="/" class="layout-topbar-logo">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-label="Logo SGFS">
                    <defs>
                        <radialGradient id="g-body" cx="256" cy="340.62" fx="256" fy="381.29" r="163.12"
                        gradientTransform="translate(0 26.14) scale(1 .92)" gradientUnits="userSpaceOnUse">
                        <stop offset=".4" stop-color="#b40d60"/>
                        <stop offset=".69" stop-color="#da1f75"/>
                        </radialGradient>
                        <linearGradient id="g-head" x1="255.4" y1="151.59" x2="255.4" y2="-2.5" gradientUnits="userSpaceOnUse">
                        <stop offset="0" stop-color="#d52075"/>
                        <stop offset="1" stop-color="#f08b30"/>
                        </linearGradient>
                    </defs>
                    <path fill="url(#g-body)"
                        d="M222.48 498.94c-44.7 43.62-116.95-37.3-135.88-76.18-47.71-98 5.15-208.64 105.55-243.11 137.64-47.25 288.71 73.42 242.5 219.45-13.16 41.6-56.16 96.71-98.72 110.38-42.25 13.58-73.67-30.47-55.54-68.72 13.67-28.84 52.53-37.07 63.64-71.37 12.68-39.12-20.74-74.96-60.93-60.94-8.01 2.79-18.49 12.8-24.62 13.36-9.86.9-13.37-6.35-21.14-10.29-43.27-21.96-84.08 17.78-67.76 61.18 12.42 33.03 50.12 40.48 62.51 70.86 7.83 19.18 5.6 40.53-9.61 55.37Z"/>
                    <path fill="url(#g-head)"
                        d="M246.97 155.38c115.25 10.31 114.69-170.76-6.19-154.32-85.52 11.63-82.91 146.35 6.19 154.32Z"/>
                </svg>

                <span>SGFS</span>
            </router-link>
        </div>

        <div class="layout-topbar-actions">
            <div class="layout-config-menu">
                <button type="button" class="layout-topbar-action" @click="toggleDarkMode">
                    <i :class="['pi', { 'pi-moon': isDarkTheme, 'pi-sun': !isDarkTheme }]"></i>
                </button>
            </div>

            <button
                class="layout-topbar-menu-button layout-topbar-action"
                v-styleclass="{ selector: '@next', enterFromClass: 'hidden', enterActiveClass: 'animate-scalein', leaveToClass: 'hidden', leaveActiveClass: 'animate-fadeout', hideOnOutsideClick: true }"
            >
                <i class="pi pi-ellipsis-v"></i>
            </button>

            <div class="layout-topbar-menu hidden lg:block">
                <div class="layout-topbar-menu-content">
                    <NotificationBell />

                    <button type="button" class="layout-topbar-action" @click="us.toggle($event)">
                        <i class="pi pi-user"></i>
                        <span class="font-bold">Usuário</span>
                    </button>
                    <OverlayPanel ref="us">
                        <div class="p-4">
                            <h6 class="text-center"><i class="pi pi-user mr-2"></i> Olá, {{ authStore.user?.username || 'Usuário' }}</h6>
                            <Button @click="handleLogout" icon="pi pi-sign-out" label="Sair do sistema" severity="warn" text />
                        </div>
                    </OverlayPanel>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.sgfs-logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.sgfs-logo svg {
  width: 36px;
  height: 36px;
}
.sgfs-text {
  font-weight: 700;
  color: var(--text-color, #ffffff);
  font-size: 1.1rem;
}
.p-overlaybadge{
    display: none !important;
}
</style>