import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import { router } from './router';
import './assets/styles/main.css';

// Polyfill for crypto.randomUUID (no funciona en HTTP, solo HTTPS/localhost)
// Axios 1.6+ lo usa internamente, asi que debemos patchearlo globalmente
if (typeof crypto === 'undefined' || typeof crypto.randomUUID !== 'function') {
  const fallbackUUID = (): string => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  };
  if (typeof crypto === 'undefined') {
    // @ts-ignore
    window.crypto = {};
  }
  // @ts-ignore
  crypto.randomUUID = fallbackUUID;
}

const app = createApp(App);

app.use(createPinia());
app.use(router);

app.mount('#app');
