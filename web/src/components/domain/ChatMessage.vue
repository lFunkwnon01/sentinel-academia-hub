<script setup lang="ts">
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
  <article
    :class="[
      'flex gap-3',
      message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
    ]"
  >
    <!-- Avatar -->
    <div
      :class="[
        'flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center text-xs font-semibold text-white shadow-soft',
        message.role === 'user'
          ? 'bg-gradient-to-br from-brand-500 to-brand-700'
          : 'bg-gradient-to-br from-purple-500 to-purple-700'
      ]"
      aria-hidden="true"
    >
      <svg v-if="message.role === 'user'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
      </svg>
      <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
      </svg>
    </div>

    <!-- Body -->
    <div :class="['flex flex-col gap-1.5 max-w-[80%] sm:max-w-[70%]', message.role === 'user' ? 'items-end' : 'items-start']">
      <!-- Content bubble -->
      <div
        :class="[
          'px-4 py-3 rounded-2xl shadow-soft',
          message.role === 'user'
            ? 'bg-brand-600 text-white rounded-tr-sm'
            : 'bg-white border border-ink-200 text-ink-900 rounded-tl-sm'
        ]"
      >
        <div
          v-if="message.role === 'assistant'"
          class="prose prose-sm max-w-none prose-p:my-1.5 prose-p:leading-relaxed prose-ul:my-1.5 prose-ol:my-1.5 prose-li:my-0.5 prose-strong:font-semibold prose-code:text-ink-700 prose-code:bg-ink-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-code:before:content-none prose-code:after:content-none"
          v-html="formattedContent"
        />
        <p v-else class="text-sm leading-relaxed whitespace-pre-wrap">{{ message.content }}</p>
        <span
          v-if="!message.complete && message.role === 'assistant'"
          class="inline-block ml-0.5 text-brand-500 font-bold animate-pulse"
          aria-hidden="true"
        >▍</span>
      </div>

      <!-- Sources -->
      <details
        v-if="message.sources && message.sources.length"
        class="text-xs text-ink-500 mt-1"
      >
        <summary class="cursor-pointer font-medium hover:text-ink-700 select-none flex items-center gap-1.5">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
          </svg>
          {{ message.sources.length }} fuente{{ message.sources.length > 1 ? 's' : '' }}
        </summary>
        <ul class="mt-2 space-y-1.5">
          <li
            v-for="(src, i) in message.sources"
            :key="i"
            class="p-2.5 bg-white border border-ink-200 rounded-lg"
          >
            <div class="flex items-center justify-between mb-1 gap-2">
              <strong class="text-ink-700 text-xs truncate">{{ src.title || src.source || src.id || 'Fuente' }}</strong>
              <span v-if="src.score != null" class="text-ink-500 text-xs whitespace-nowrap">{{ (src.score * 100).toFixed(0) }}%</span>
            </div>
            <p class="text-xs text-ink-600 leading-relaxed">{{ (src.content || '').slice(0, 250) }}{{ src.content && src.content.length > 250 ? '…' : '' }}</p>
          </li>
        </ul>
      </details>

      <!-- Timestamp -->
      <time
        class="text-[10px] text-ink-400 px-1"
        :datetime="message.timestamp"
      >
        {{ new Date(message.timestamp).toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' }) }}
      </time>
    </div>
  </article>
</template>

<style scoped>
/* Markdown styles for prose container */
:deep(.prose code) {
  font-family: 'JetBrains Mono', ui-monospace, monospace;
}
</style>
