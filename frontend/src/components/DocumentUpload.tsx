import React, { useCallback, useState } from 'react';
import { Upload, FileText, X, CheckCircle, Cloud, Sparkles } from 'lucide-react';
import { uploadDocuments } from '../services/api';
import { UploadedDocument } from '../types';

interface DocumentUploadProps {
  onUploadComplete: (documents: UploadedDocument[]) => void;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({ onUploadComplete }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedDocument[]>([]);

  const handleFiles = useCallback(async (files: FileList) => {
    if (files.length === 0) return;

    // Validate file types
    const validTypes = ['.pdf', '.docx', '.txt'];
    const invalidFiles = Array.from(files).filter(file => 
      !validTypes.some(type => file.name.toLowerCase().endsWith(type))
    );

    if (invalidFiles.length > 0) {
      alert(`Invalid file types: ${invalidFiles.map(f => f.name).join(', ')}\nSupported: PDF, DOCX, TXT`);
      return;
    }

    setIsUploading(true);
    try {
      const result = await uploadDocuments(files);
      setUploadedFiles(prev => [...prev, ...result.documents]);
      onUploadComplete(result.documents);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  }, [onUploadComplete]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    handleFiles(files);
  }, [handleFiles]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      handleFiles(files);
    }
  }, [handleFiles]);

  const removeFile = (docId: string) => {
    setUploadedFiles(prev => prev.filter(doc => doc.doc_id !== docId));
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Upload Area */}
      <div
        className={`relative border-2 border-dashed rounded-3xl p-12 text-center transition-all duration-300 ${
          isDragging
            ? 'border-blue-500 bg-gradient-to-br from-blue-50 to-purple-50 scale-105'
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {/* Background decoration */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50/50 to-purple-50/50 rounded-3xl" />
        
        <div className="relative">
          {isUploading ? (
            <div className="space-y-4">
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-4 rounded-2xl w-16 h-16 mx-auto flex items-center justify-center">
                <Cloud className="h-8 w-8 text-white animate-bounce" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Processing Documents...
                </h3>
                <p className="text-gray-600">
                  Please wait while we analyze your files
                </p>
                <div className="mt-4 w-48 mx-auto bg-gray-200 rounded-full h-2">
                  <div className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full animate-pulse" style={{ width: '70%' }} />
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-4 rounded-2xl w-16 h-16 mx-auto flex items-center justify-center">
                <Upload className="h-8 w-8 text-white" />
              </div>
              
              <div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">
                  Upload Your Documents
                </h3>
                <p className="text-lg text-gray-600 mb-2">
                  Drag and drop files here, or click to browse
                </p>
                <p className="text-sm text-gray-500">
                  Supports PDF, DOCX, and TXT files up to 10MB each
                </p>
              </div>

              <input
                type="file"
                multiple
                accept=".pdf,.docx,.txt"
                onChange={handleFileSelect}
                className="hidden"
                id="file-upload"
                disabled={isUploading}
              />
              
              <label
                htmlFor="file-upload"
                className="inline-flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-2xl hover:from-blue-700 hover:to-purple-700 cursor-pointer transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                <Sparkles className="h-5 w-5" />
                <span>Choose Files</span>
              </label>

              {/* Supported formats */}
              <div className="flex items-center justify-center space-x-6 text-sm text-gray-500">
                <div className="flex items-center space-x-1">
                  <FileText className="h-4 w-4" />
                  <span>PDF</span>
                </div>
                <div className="flex items-center space-x-1">
                  <FileText className="h-4 w-4" />
                  <span>DOCX</span>
                </div>
                <div className="flex items-center space-x-1">
                  <FileText className="h-4 w-4" />
                  <span>TXT</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Uploaded Files */}
      {uploadedFiles.length > 0 && (
        <div className="mt-8">
          <div className="flex items-center space-x-2 mb-4">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <h4 className="text-lg font-semibold text-gray-900">
              Successfully Uploaded ({uploadedFiles.length})
            </h4>
          </div>
          
          <div className="grid gap-3">
            {uploadedFiles.map((doc) => (
              <div
                key={doc.doc_id}
                className="flex items-center justify-between p-4 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-2xl shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="flex items-center space-x-4">
                  <div className="bg-green-100 p-2 rounded-xl">
                    <FileText className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">
                      {doc.filename}
                    </p>
                    <p className="text-sm text-green-600">
                      ✓ {doc.chunks} chunks processed
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => removeFile(doc.doc_id)}
                  className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>

          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-2xl">
            <div className="flex items-center space-x-2 mb-2">
              <Sparkles className="h-5 w-5 text-blue-600" />
              <span className="font-medium text-blue-900">Ready to Chat!</span>
            </div>
            <p className="text-sm text-blue-700">
              Your documents have been processed and are ready for intelligent conversations. 
              Click on "New Chat" to start asking questions!
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentUpload;