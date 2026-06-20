<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import AppShell from '@/views/AppShell.vue';

const route = useRoute();
const isHome = computed(() => route.name === 'home');
</script>

<template>
  <!-- Home view: full-page hero (no sidebar) -->
  <div v-if="isHome" class="min-h-screen">
    <RouterView />
  </div>
  <!-- App views: with sidebar layout -->
  <AppShell v-else />
</template>

<style>
/* Global resets */
@import '@/assets/styles/main.css';
</style>
