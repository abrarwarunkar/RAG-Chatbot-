import axios from 'axios';
import axiosRetry from 'axios-retry';
import { UploadedDocument } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://rag-chatbot-backend-w3ef.onrender.com';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Configure axios-retry
axiosRetry(api, {
  retries: 3, // Number of retry attempts
  retryDelay: (retryCount) => {
    return retryCount * 2000; // Exponential backoff: 2s, 4s, 6s
  },
  retryCondition: (error) => {
    // Retry on network errors and 5xx responses
    // Ensure we always return a boolean value
    return !!(axiosRetry.isNetworkError(error) ||
           (error.response && error.response.status >= 500));
  }
});

export const uploadDocuments = async (files: FileList, clearExisting: boolean = true): Promise<{ documents: UploadedDocument[] }> => {
  const formData = new FormData();
  Array.from(files).forEach(file => {
    formData.append('files', file);
  });
  
  // Add clear_existing parameter
  formData.append('clear_existing', clearExisting.toString());

  // Use a longer timeout for uploads (2 minutes instead of 30 seconds)
  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 120000, // 2 minutes
  });

  return response.data;
};

export const clearDocuments = async (): Promise<void> => {
  await api.post('/documents/clear');
};

export const streamChat = async (
  message: string,
  sessionId: string | null,
  onToken: (token: string) => void,
  onSources: (sources: any[], sessionId: string) => void,
  onError: (error: string) => void
): Promise<void> => {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') {
            return;
          }

          try {
            const parsed = JSON.parse(data);
            if (parsed.type === 'token') {
              onToken(parsed.content);
            } else if (parsed.type === 'sources') {
              onSources(parsed.sources, parsed.session_id);
            }
          } catch (e) {
            // Ignore parsing errors for malformed chunks
          }
        }
      }
    }
  } catch (error) {
    onError(error instanceof Error ? error.message : 'Unknown error occurred');
  }
};

export const getSessionHistory = async (sessionId: string) => {
  const response = await api.get(`/sessions/${sessionId}`);
  return response.data;
};

export default api;