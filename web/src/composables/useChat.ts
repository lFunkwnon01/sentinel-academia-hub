import { ref } from 'vue';
import { chatService } from '@/services/chatService';
import type { ChatMessageUI, ChatSource } from '@/types/api';
import { generateUUID } from '@/utils/uuid';

export function useChat() {
  const messages = ref<ChatMessageUI[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const conversationId = ref<string | undefined>(undefined);

  function addMessage(message: Omit<ChatMessageUI, 'id' | 'timestamp'>): ChatMessageUI {
    const fullMessage: ChatMessageUI = {
      id: generateUUID(),
      timestamp: new Date().toISOString(),
      role: message.role,
      content: message.content || '',
      complete: message.complete ?? true,
      sources: message.sources,
    };
    messages.value.push(fullMessage);
    return fullMessage;
  }

  function updateAssistantMessage(
    msg: ChatMessageUI,
    patch: Partial<ChatMessageUI>
  ): void {
    // Force a new reference for the message to ensure Vue reactivity
    const idx = messages.value.findIndex((m) => m.id === msg.id);
    if (idx === -1) return;
    const updated: ChatMessageUI = {
      ...msg,
      ...patch,
    };
    messages.value.splice(idx, 1, updated);
  }

  async function sendMessage(question: string): Promise<void> {
    if (!question.trim() || loading.value) return;

    error.value = null;

    addMessage({
      role: 'user',
      content: question,
      complete: true,
    });

    const assistantMessage = addMessage({
      role: 'assistant',
      content: '',
      complete: false,
    });

    loading.value = true;
    try {
      console.log('[useChat] sending question:', question.substring(0, 50));
      const response = await chatService.send({
        question,
        conversationId: conversationId.value,
      });
      console.log('[useChat] response received:', {
        answerLength: response.answer?.length,
        sources: response.sources?.length,
      });

      updateAssistantMessage(assistantMessage, {
        content: response.answer || '(sin respuesta)',
        sources: response.sources || [],
        complete: true,
      });

      if (response.conversationId) {
        conversationId.value = response.conversationId;
      }
    } catch (e) {
      console.error('[useChat] error:', e);
      const errorMsg = e instanceof Error ? e.message : 'Error al enviar mensaje';
      error.value = errorMsg;
      updateAssistantMessage(assistantMessage, {
        content: `Lo siento, ocurrio un error: ${errorMsg}`,
        complete: true,
      });
    } finally {
      loading.value = false;
    }
  }

  function clearHistory(): void {
    messages.value = [];
    conversationId.value = undefined;
  }

  return {
    messages,
    loading,
    error,
    sendMessage,
    clearHistory,
  };
}
