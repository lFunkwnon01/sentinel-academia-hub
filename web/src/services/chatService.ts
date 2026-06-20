import { apiClient } from './apiClient';
import type { ChatRequest, ChatResponse } from '@/types/api';

export const chatService = {
  async send(request: ChatRequest): Promise<ChatResponse> {
    const { data } = await apiClient.post<ChatResponse>('/api/chat', request);
    return data;
  },
};
