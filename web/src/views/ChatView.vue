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
  if (confirm('Limpiar todo el historial del chat?')) {
    clearHistory();
  }
}
</script>

<template>
  <div class="chat-view">
    <header class="chat-view__header">
      <div>
        <h1>Chat con IA</h1>
        <p class="chat-view__subtitle">Asistente con acceso al reglamento y al historial de quejas (RAG)</p>
      </div>
      <AppButton v-if="messages.length" variant="ghost" size="sm" @click="clear">
        Limpiar chat
      </AppButton>
    </header>

    <div class="chat-view__messages">
      <div v-if="messages.length === 0" class="chat-view__welcome">
        <div class="chat-view__welcome-icon" aria-hidden="true">💬</div>
        <h2>Hola, soy tu asistente virtual</h2>
        <p>Pregúntame sobre el proceso de quejas, el reglamento universitario, o cualquier duda relacionada.</p>
        <div class="chat-view__suggestions">
          <p class="chat-view__suggestions-label">Preguntas frecuentes:</p>
          <button
            v-for="q in suggestedQuestions"
            :key="q"
            class="chat-view__suggestion"
            @click="useSuggestion(q)"
          >
            {{ q }}
          </button>
        </div>
      </div>

      <ChatMessage
        v-for="msg in messages"
        :key="msg.id"
        :message="msg"
      />

      <div ref="messagesEndRef" />
    </div>

    <div v-if="error" class="chat-view__error" role="alert">{{ error }}</div>

    <form class="chat-view__input" @submit.prevent="send">
      <textarea
        v-model="inputText"
        placeholder="Escribe tu pregunta..."
        rows="2"
        :disabled="loading"
        @keydown="onKeyDown"
      />
      <AppButton type="submit" variant="primary" :loading="loading" :disabled="!inputText.trim()">
        Enviar
      </AppButton>
    </form>
  </div>
</template>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 200px);
  max-height: 800px;
}

.chat-view__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-4);
}

.chat-view__header h1 {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  margin-bottom: var(--space-1);
}

.chat-view__subtitle {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.chat-view__messages {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-4) 0;
}

.chat-view__welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: var(--space-12) var(--space-6);
  height: 100%;
}

.chat-view__welcome-icon {
  font-size: 64px;
  margin-bottom: var(--space-4);
}

.chat-view__welcome h2 {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  margin-bottom: var(--space-2);
  color: var(--color-text);
}

.chat-view__welcome p {
  color: var(--color-text-muted);
  max-width: 480px;
  margin-bottom: var(--space-6);
}

.chat-view__suggestions {
  width: 100%;
  max-width: 480px;
}

.chat-view__suggestions-label {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin-bottom: var(--space-2);
  text-align: left;
}

.chat-view__suggestion {
  display: block;
  width: 100%;
  text-align: left;
  padding: var(--space-3);
  margin-bottom: var(--space-2);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--text-sm);
  color: var(--color-text);
  transition: all var(--transition-fast);
}

.chat-view__suggestion:hover {
  background: var(--color-primary-light);
  border-color: var(--color-primary);
}

.chat-view__error {
  padding: var(--space-3);
  background: var(--color-danger-light);
  color: var(--color-danger);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  margin-bottom: var(--space-3);
}

.chat-view__input {
  display: flex;
  gap: var(--space-3);
  align-items: flex-end;
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border);
}

.chat-view__input textarea {
  flex: 1;
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  font-family: var(--font-sans);
  resize: none;
  min-height: 60px;
  max-height: 120px;
}

.chat-view__input textarea:focus-visible {
  outline: none;
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}
</style>
