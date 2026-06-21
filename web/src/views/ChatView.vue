<script setup lang="ts">
import { ref, nextTick, useTemplateRef } from 'vue';
import { useChat } from '@/composables/useChat';
import { useNotificationStore } from '@/stores/notifications';
import AppButton from '@/components/common/AppButton.vue';
import ChatMessage from '@/components/domain/ChatMessage.vue';
import type { ChatMessageUI } from '@/types/api';

const { messages, loading, error, sendMessage, clearHistory } = useChat();
const notifications = useNotificationStore();
const inputText = ref('');
const messagesEndRef = useTemplateRef<HTMLElement>('messagesEndRef');

const suggestedQuestions = [
  '¿Cuál es el proceso para escalar una queja crítica?',
  '¿Qué hago si sufro acoso de un compañero?',
  '¿Cuánto tiempo tarda en procesarse una queja?',
  '¿Cómo puedo reportar un problema de forma anónima?',
];

async function send() {
  const text = inputText.value.trim();
  if (!text || loading.value) return;
  inputText.value = '';
  try {
    await sendMessage(text);
    await nextTick();
    messagesEndRef.value?.scrollIntoView({ behavior: 'smooth' });
  } catch (e) {
    notifications.error('Error en el chat');
  }
}

function useSuggestion(text: string) {
  inputText.value = text;
  send();
}

function onKeyDown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    send();
  }
}

function clear() {
  if (confirm('¿Limpiar todo el historial del chat?')) {
    clearHistory();
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto p-6 sm:p-8 flex flex-col" style="min-height: calc(100vh - 80px);">
    <!-- Header -->
    <header class="flex items-center justify-between gap-4 pb-5 border-b border-ink-200">
      <div>
        <h1 class="text-2xl font-semibold text-ink-900 tracking-tight">Chat con IA</h1>
        <p class="mt-1 text-sm text-ink-500">Asistente con acceso al reglamento y al historial de quejas (RAG)</p>
      </div>
      <AppButton v-if="messages.length" variant="ghost" size="sm" @click="clear">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
        </svg>
        Limpiar chat
      </AppButton>
    </header>

    <!-- Messages area -->
    <div class="flex-1 py-6 overflow-y-auto">
      <!-- Welcome state -->
      <div v-if="messages.length === 0" class="flex flex-col items-center text-center pt-4">
        <!-- Hero icon -->
        <div class="relative mb-6">
          <div class="absolute inset-0 bg-gradient-to-br from-brand-200 to-brand-100 rounded-full blur-2xl opacity-60"></div>
          <div class="relative w-20 h-20 rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-lift">
            <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.8">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
            </svg>
          </div>
        </div>

        <h2 class="text-xl sm:text-2xl font-semibold text-ink-900 mb-2">Hola, soy tu asistente virtual</h2>
        <p class="text-sm sm:text-base text-ink-600 max-w-md leading-relaxed">
          Pregúntame sobre el proceso de quejas, el reglamento universitario, o cualquier duda relacionada.
        </p>

        <!-- Suggested questions -->
        <div class="w-full max-w-xl mt-10">
          <p class="text-xs font-semibold text-ink-500 uppercase tracking-wider text-left mb-3">Preguntas frecuentes</p>
          <div class="flex flex-col gap-2">
            <button
              v-for="q in suggestedQuestions"
              :key="q"
              type="button"
              @click="useSuggestion(q)"
              :disabled="loading"
              class="group flex items-center gap-3 w-full text-left p-3.5 rounded-xl bg-white border border-ink-200 hover:border-brand-400 hover:bg-brand-50 hover:shadow-soft transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-1"
            >
              <div class="w-8 h-8 rounded-lg bg-brand-100 text-brand-600 flex items-center justify-center flex-shrink-0 group-hover:bg-brand-200 transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <span class="flex-1 text-sm text-ink-700 group-hover:text-ink-900">{{ q }}</span>
              <svg class="w-4 h-4 text-ink-400 group-hover:text-brand-600 group-hover:translate-x-0.5 transition-all flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Hint pill -->
        <div class="mt-10 inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-ink-100 text-ink-600 text-xs">
          <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
          </svg>
          Powered by Cohere · respuesta promedio en 2-3 segundos
        </div>
      </div>

      <!-- Chat state with messages -->
      <div v-else class="flex flex-col gap-4">
        <ChatMessage
          v-for="msg in messages"
          :key="msg.id"
          :message="msg"
        />
        <div ref="messagesEndRef" />
      </div>
    </div>

    <!-- Error message -->
    <div v-if="error" class="mb-3 p-3 rounded-lg bg-danger-50 border border-danger-500/20 text-danger-700 text-sm flex items-center gap-2" role="alert">
      <svg class="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
      </svg>
      {{ error }}
    </div>

    <!-- Input area -->
    <form class="flex items-end gap-3 pt-4 border-t border-ink-200" @submit.prevent="send">
      <div class="flex-1 relative">
        <textarea
          v-model="inputText"
          placeholder="Escribe tu pregunta..."
          rows="1"
          :disabled="loading"
          class="w-full px-4 py-3 pr-12 text-sm text-ink-900 placeholder:text-ink-400 bg-white border border-ink-300 rounded-xl shadow-soft transition-all duration-150 resize-none focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 disabled:bg-ink-50 disabled:text-ink-500"
          style="min-height: 48px; max-height: 160px;"
          @keydown="onKeyDown"
          @input="(e) => { const t = e.target as HTMLTextAreaElement; t.style.height = 'auto'; t.style.height = Math.min(t.scrollHeight, 160) + 'px'; }"
        />
      </div>
      <AppButton
        type="submit"
        variant="primary"
        size="lg"
        :loading="loading"
        :disabled="!inputText.trim()"
      >
        <template v-if="!loading">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
          </svg>
          Enviar
        </template>
      </AppButton>
    </form>

    <!-- Footer -->
    <footer class="mt-6 pt-4 border-t border-ink-100 text-center text-xs text-ink-400">
      Sentinel AcademIA · Hackatón 2025 · Multi-nube AWS + OCI
    </footer>
  </div>
</template>
