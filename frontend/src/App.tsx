import React, { useState } from 'react';
import DocumentUpload from './components/DocumentUpload';
import ChatInterface from './components/ChatInterface';
import { UploadedDocument } from './types';
import { MessageSquare, Upload as UploadIcon } from 'lucide-react';

function App() {
  const [uploadedDocuments, setUploadedDocuments] = useState<UploadedDocument[]>([]);
  const [activeTab, setActiveTab] = useState<'upload' | 'chat'>('upload');

  const handleUploadComplete = (documents: UploadedDocument[]) => {
    setUploadedDocuments(prev => [...prev, ...documents]);
    setActiveTab('chat');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <div className="bg-blue-600 p-2 rounded-lg">
                <MessageSquare className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">RAG Chatbot</h1>
                <p className="text-sm text-gray-600">
                  Upload documents and ask questions
                </p>
              </div>
            </div>
            
            {/* Tab Navigation */}
            <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
              <button
                onClick={() => setActiveTab('upload')}
                className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'upload'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <UploadIcon className="h-4 w-4" />
                <span>Upload</span>
              </button>
              <button
                onClick={() => setActiveTab('chat')}
                className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'chat'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <MessageSquare className="h-4 w-4" />
                <span>Chat</span>
                {uploadedDocuments.length > 0 && (
                  <span className="bg-blue-100 text-blue-600 text-xs px-2 py-0.5 rounded-full">
                    {uploadedDocuments.length}
                  </span>
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'upload' ? (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Upload Your Documents
              </h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                Upload PDF, DOCX, or TXT files to create a knowledge base. 
                Then ask questions and get AI-powered answers with source citations.
              </p>
            </div>
            <DocumentUpload onUploadComplete={handleUploadComplete} />
          </div>
        ) : (
          <div className="h-[calc(100vh-200px)]">
            <ChatInterface hasDocuments={uploadedDocuments.length > 0} />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-sm text-gray-500">
            RAG Chatbot - Powered by OpenAI GPT-4 and FAISS Vector Search
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;