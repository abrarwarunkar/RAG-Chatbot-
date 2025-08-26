import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, FileText, RotateCcw, Sparkles } from 'lucide-react';
import { streamChat } from '../services/api';
import { Message, Source } from '../types';

interface ChatInterfaceProps {
  hasDocuments: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ hasDocuments }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    if (!hasDocuments) {
      alert('Please upload documents first before asking questions.');
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      isStreaming: true,
    };

    setMessages(prev => [...prev, userMessage, assistantMessage]);
    setInput('');
    setIsLoading(true);

    try {
      await streamChat(
        userMessage.content,
        sessionId,
        (token: string) => {
          setMessages(prev => 
            prev.map(msg => 
              msg.id === assistantMessage.id
                ? { ...msg, content: msg.content + token }
                : msg
            )
          );
        },
        (sources: Source[], newSessionId: string) => {
          setSessionId(newSessionId);
          setMessages(prev => 
            prev.map(msg => 
              msg.id === assistantMessage.id
                ? { ...msg, sources, isStreaming: false }
                : msg
            )
          );
        },
        (error: string) => {
          setMessages(prev => 
            prev.map(msg => 
              msg.id === assistantMessage.id
                ? { ...msg, content: `Error: ${error}`, isStreaming: false }
                : msg
            )
          );
        }
      );
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setSessionId(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center p-8">
            <div className="text-center max-w-md">
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-4 rounded-2xl w-16 h-16 mx-auto mb-6 flex items-center justify-center">
                <Sparkles className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-2xl font-semibold text-gray-900 mb-3">
                {hasDocuments ? 'Ready to Chat!' : 'No Documents Yet'}
              </h3>
              <p className="text-gray-600 mb-6">
                {hasDocuments 
                  ? 'Ask me anything about your uploaded documents. I\'ll provide detailed answers with source citations.'
                  : 'Upload some documents first, then we can start having intelligent conversations about your content.'}
              </p>
              {hasDocuments && (
                <div className="space-y-2 text-sm text-gray-500">
                  <p>💡 Try asking:</p>
                  <div className="space-y-1">
                    <p>• "What are the main topics covered?"</p>
                    <p>• "Summarize the key findings"</p>
                    <p>• "What does it say about...?"</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto px-4 py-6">
            {/* Clear Chat Button */}
            <div className="flex justify-end mb-4">
              <button
                onClick={clearChat}
                className="flex items-center space-x-2 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <RotateCcw className="h-4 w-4" />
                <span>New Chat</span>
              </button>
            </div>

            {/* Messages */}
            <div className="space-y-6">
              {messages.map((message) => (
                <div key={message.id} className="group">
                  {message.role === 'user' ? (
                    <div className="flex justify-end">
                      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-2xl px-4 py-3 max-w-2xl shadow-sm">
                        <p className="whitespace-pre-wrap">{message.content}</p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex space-x-3">
                      <div className="flex-shrink-0">
                        <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-2 rounded-xl">
                          <Bot className="h-5 w-5 text-white" />
                        </div>
                      </div>
                      <div className="flex-1 space-y-3">
                        <div className="bg-gray-50 rounded-2xl px-4 py-3 max-w-none">
                          <p className="text-gray-900 whitespace-pre-wrap">{message.content}</p>
                          {message.isStreaming && (
                            <div className="flex items-center space-x-1 mt-2">
                              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" />
                              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                            </div>
                          )}
                        </div>
                        
                        {/* Sources */}
                        {message.sources && message.sources.length > 0 && (
                          <div className="bg-blue-50 border border-blue-200 rounded-xl p-3">
                            <div className="flex items-center space-x-2 mb-2">
                              <FileText className="h-4 w-4 text-blue-600" />
                              <span className="text-sm font-medium text-blue-900">Sources</span>
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                              {message.sources.map((source, idx) => (
                                <div
                                  key={idx}
                                  className="bg-white border border-blue-200 rounded-lg px-3 py-2 text-sm"
                                >
                                  <div className="font-medium text-gray-900 truncate">{source.filename}</div>
                                  <div className="text-blue-600">Chunk {source.chunk_id + 1}</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 bg-white p-4">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSubmit} className="relative">
            <div className="flex items-end space-x-3">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={hasDocuments ? "Ask me anything about your documents..." : "Upload documents first to start chatting..."}
                  disabled={!hasDocuments || isLoading}
                  rows={1}
                  className="w-full resize-none border border-gray-300 rounded-2xl px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed text-gray-900 placeholder-gray-500"
                  style={{ minHeight: '48px', maxHeight: '120px' }}
                />
              </div>
              <button
                type="submit"
                disabled={!input.trim() || !hasDocuments || isLoading}
                className="flex-shrink-0 bg-gradient-to-r from-blue-600 to-blue-700 text-white p-3 rounded-2xl hover:from-blue-700 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-sm"
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
          </form>
          <div className="mt-2 text-xs text-gray-500 text-center">
            Press Enter to send, Shift+Enter for new line
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;