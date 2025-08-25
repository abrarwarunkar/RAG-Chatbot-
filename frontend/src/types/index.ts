export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: Source[];
  isStreaming?: boolean;
}

export interface Source {
  filename: string;
  chunk_id: number;
}

export interface UploadedDocument {
  filename: string;
  doc_id: string;
  chunks: number;
}

export interface ChatSession {
  id: string;
  messages: Message[];
  createdAt: string;
}