import React from 'react';
import { MessageSquare, Upload, FileText, X, Plus, History } from 'lucide-react';
import { UploadedDocument } from '../types';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  uploadedDocuments: UploadedDocument[];
  activeView: 'upload' | 'chat';
  onViewChange: (view: 'upload' | 'chat') => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onClose,
  uploadedDocuments,
  activeView,
  onViewChange,
}) => {
  return (
    <>
      {/* Desktop Sidebar */}
      <div className="hidden lg:flex lg:flex-col lg:w-64 lg:bg-gray-900 lg:text-white">
        <div className="flex-1 flex flex-col min-h-0">
          {/* Header */}
          <div className="flex items-center h-16 px-4 bg-gray-800">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-2 rounded-lg">
                <MessageSquare className="h-5 w-5 text-white" />
              </div>
              <span className="font-semibold">RAG Assistant</span>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-4 space-y-2">
            <button
              onClick={() => onViewChange('chat')}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                activeView === 'chat'
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <MessageSquare className="h-5 w-5" />
              <span>New Chat</span>
            </button>

            <button
              onClick={() => onViewChange('upload')}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                activeView === 'upload'
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <Upload className="h-5 w-5" />
              <span>Upload Documents</span>
            </button>

            {/* Documents Section */}
            {uploadedDocuments.length > 0 && (
              <div className="pt-4">
                <div className="flex items-center space-x-2 px-3 py-2 text-xs font-medium text-gray-400 uppercase tracking-wider">
                  <FileText className="h-4 w-4" />
                  <span>Documents ({uploadedDocuments.length})</span>
                </div>
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {uploadedDocuments.map((doc, index) => (
                    <div
                      key={index}
                      className="px-3 py-2 text-sm text-gray-300 hover:bg-gray-800 rounded-lg cursor-pointer"
                    >
                      <div className="truncate">{doc.filename}</div>
                      <div className="text-xs text-gray-500">{doc.chunks} chunks</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-gray-700">
            <div className="text-xs text-gray-400">
              Powered by Groq & FAISS
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Sidebar */}
      <div className={`lg:hidden fixed inset-y-0 left-0 z-50 w-64 bg-gray-900 text-white transform transition-transform duration-300 ease-in-out ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <div className="flex-1 flex flex-col min-h-0">
          {/* Header */}
          <div className="flex items-center justify-between h-16 px-4 bg-gray-800">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-2 rounded-lg">
                <MessageSquare className="h-5 w-5 text-white" />
              </div>
              <span className="font-semibold">RAG Assistant</span>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-700"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-4 space-y-2">
            <button
              onClick={() => {
                onViewChange('chat');
                onClose();
              }}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                activeView === 'chat'
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <MessageSquare className="h-5 w-5" />
              <span>New Chat</span>
            </button>

            <button
              onClick={() => {
                onViewChange('upload');
                onClose();
              }}
              className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                activeView === 'upload'
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <Upload className="h-5 w-5" />
              <span>Upload Documents</span>
            </button>

            {/* Documents Section */}
            {uploadedDocuments.length > 0 && (
              <div className="pt-4">
                <div className="flex items-center space-x-2 px-3 py-2 text-xs font-medium text-gray-400 uppercase tracking-wider">
                  <FileText className="h-4 w-4" />
                  <span>Documents ({uploadedDocuments.length})</span>
                </div>
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {uploadedDocuments.map((doc, index) => (
                    <div
                      key={index}
                      className="px-3 py-2 text-sm text-gray-300 hover:bg-gray-800 rounded-lg cursor-pointer"
                    >
                      <div className="truncate">{doc.filename}</div>
                      <div className="text-xs text-gray-500">{doc.chunks} chunks</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-gray-700">
            <div className="text-xs text-gray-400">
              Powered by Groq & FAISS
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;