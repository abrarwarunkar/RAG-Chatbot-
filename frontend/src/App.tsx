import React, { useState } from 'react';
import DocumentUpload from './components/DocumentUpload';
import ChatInterface from './components/ChatInterface';
import Sidebar from './components/Sidebar';
import { UploadedDocument } from './types';
import { MessageSquare, Menu } from 'lucide-react';

function App() {
  const [uploadedDocuments, setUploadedDocuments] = useState<UploadedDocument[]>([]);
  const [activeView, setActiveView] = useState<'upload' | 'chat'>('upload');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleUploadComplete = (documents: UploadedDocument[]) => {
    setUploadedDocuments(prev => [...prev, ...documents]);
    setActiveView('chat');
  };

  return (
    <div className="flex h-screen bg-white">
      {/* Sidebar */}
      <Sidebar 
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        uploadedDocuments={uploadedDocuments}
        activeView={activeView}
        onViewChange={setActiveView}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
              >
                <Menu className="h-5 w-5" />
              </button>
              <div className="flex items-center space-x-3">
                <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-2 rounded-xl">
                  <MessageSquare className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-semibold text-gray-900">RAG Assistant</h1>
                  <p className="text-sm text-gray-500">
                    {activeView === 'upload' ? 'Upload documents to get started' : 'Ask questions about your documents'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <main className="flex-1 overflow-hidden">
          {activeView === 'upload' ? (
            <div className="h-full flex items-center justify-center p-8">
              <div className="max-w-2xl w-full">
                <div className="text-center mb-8">
                  <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4 rounded-2xl w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                    <MessageSquare className="h-8 w-8 text-white" />
                  </div>
                  <h2 className="text-3xl font-bold text-gray-900 mb-4">
                    Welcome to RAG Assistant
                  </h2>
                  <p className="text-lg text-gray-600">
                    Upload your documents and start having intelligent conversations with your data.
                  </p>
                </div>
                <DocumentUpload onUploadComplete={handleUploadComplete} />
              </div>
            </div>
          ) : (
            <ChatInterface hasDocuments={uploadedDocuments.length > 0} />
          )}
        </main>
      </div>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-40 bg-black bg-opacity-50" onClick={() => setSidebarOpen(false)} />
      )}
    </div>
  );
}

export default App;