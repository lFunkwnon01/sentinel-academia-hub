<script setup lang="ts">
import { RouterLink } from 'vue-router';
import AppButton from '@/components/common/AppButton.vue';
import { marked } from 'marked';
import { computed } from 'vue';
import type { ChatMessageUI } from '@/types/api';

interface Props {
  message: ChatMessageUI;
}

const props = defineProps<Props>();

const formattedContent = computed(() => {
  if (props.message.role !== 'assistant') {
    return String(props.message.content || '');
  }
  // Defensive: marked.parse throws on null/undefined
  const content = String(props.message.content || '');
  if (!content) return '';
  try {
    return marked.parse(content, { async: false }) as string;
  } catch (e) {
    console.error('ChatMessage: marked.parse failed', e);
    return content;
  }
});
</script>

<template>
  <article :class="['chat-message', `chat-message--${message.role}`]">
    <div class="chat-message__avatar" aria-hidden="true">
      <span v-if="message.role === 'user'">Tu</span>
      <span v-else>IA</span>
    </div>
    <div class="chat-message__body">
      <div class="chat-message__content">
        <div
          v-if="message.role === 'assistant'"
          class="chat-message__markdown"
          v-html="formattedContent"
        />
        <p v-else class="chat-message__text">{{ message.content }}</p>
        <span v-if="!message.complete && message.role === 'assistant'" class="chat-message__cursor" aria-hidden="true">▍</span>
      </div>

      <details v-if="message.sources && message.sources.length" class="chat-message__sources">
        <summary>{{ message.sources.length }} fuente{{ message.sources.length > 1 ? 's' : '' }}</summary>
        <ul>
          <li v-for="(src, i) in message.sources" :key="i">
            <div class="chat-message__source-header">
              <strong>{{ src.title || src.source || src.id || 'Fuente' }}</strong>
              <span v-if="src.score != null" class="chat-message__source-score">{{ (src.score * 100).toFixed(0) }}% relevancia</span>
            </div>
            <p class="chat-message__source-content">{{ (src.content || '').slice(0, 250) }}{{ src.content && src.content.length > 250 ? '...' : '' }}</p>
          </li>
        </ul>
      </details>

      <time class="chat-message__time" :datetime="message.timestamp">
        {{ new Date(message.timestamp).toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' }) }}
      </time>
    </div>
  </article>
</template>

<style scoped>
.chat-message {
  display: flex;
  gap: var(--space-3);
  max-width: 85%;
}

.chat-message--user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.chat-message--assistant {
  align-self: flex-start;
}

.chat-message__avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-xs);
  font-weight: var(--font-bold);
  color: white;
  flex-shrink: 0;
}

.chat-message--user .chat-message__avatar {
  background: var(--color-primary);
}

.chat-message--assistant .chat-message__avatar {
  background: var(--color-info);
}

.chat-message__body {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  max-width: 100%;
}

.chat-message__content {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg);
  word-wrap: break-word;
}

.chat-message--user .chat-message__content {
  background: var(--color-primary);
  color: white;
  border-bottom-right-radius: var(--radius-sm);
}

.chat-message--assistant .chat-message__content {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-bottom-left-radius: var(--radius-sm);
}

.chat-message__text {
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  white-space: pre-wrap;
}

.chat-message__markdown {
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
}

.chat-message__markdown :deep(p) {
  margin: 0 0 var(--space-2) 0;
}

.chat-message__markdown :deep(p:last-child) {
  margin-bottom: 0;
}

.chat-message__markdown :deep(code) {
  padding: 2px 6px;
  background: var(--color-bg-muted);
  border-radius: var(--radius-sm);
  font-size: 0.9em;
  font-family: var(--font-mono);
}

.chat-message__markdown :deep(ul),
.chat-message__markdown :deep(ol) {
  padding-left: var(--space-5);
  margin: var(--space-2) 0;
}

.chat-message__markdown :deep(strong) {
  font-weight: var(--font-semibold);
}

.chat-message__cursor {
  display: inline-block;
  animation: blink 1s infinite;
  color: var(--color-info);
  font-weight: bold;
}

@keyframes blink {
  50% { opacity: 0; }
}

.chat-message__sources {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.chat-message__sources summary {
  cursor: pointer;
  padding: var(--space-1) 0;
  font-weight: var(--font-medium);
}

.chat-message__sources summary:hover {
  color: var(--color-text);
}

.chat-message__sources ul {
  margin-top: var(--space-2);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.chat-message__sources li {
  padding: var(--space-2);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
}

.chat-message__source-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-1);
  font-size: var(--text-xs);
}

.chat-message__source-score {
  color: var(--color-text-muted);
  font-weight: var(--font-normal);
}

.chat-message__source-content {
  font-size: var(--text-xs);
  line-height: var(--leading-normal);
  color: var(--color-text-muted);
}

.chat-message__time {
  font-size: var(--text-xs);
  color: var(--color-text-subtle);
  padding: 0 var(--space-2);
}
</style>
