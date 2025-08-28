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
  // State for tracking upload progress and errors
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleFiles = useCallback(async (files: FileList) => {
    if (files.length === 0) return;

    // Reset states
    setUploadError(null);
    setUploadProgress(0);

    // Validate file types
    const validTypes = ['.pdf', '.docx', '.txt'];
    const invalidFiles = Array.from(files).filter(file =>
      !validTypes.some(type => file.name.toLowerCase().endsWith(type))
    );

    if (invalidFiles.length > 0) {
      setUploadError(`Invalid file types: ${invalidFiles.map(f => f.name).join(', ')}\nSupported: PDF, DOCX, TXT`);
      return;
    }

    // Validate file sizes
    const maxSize = 10 * 1024 * 1024; // 10MB
    const oversizedFiles = Array.from(files).filter(file => file.size > maxSize);
    
    if (oversizedFiles.length > 0) {
      setUploadError(`Files too large: ${oversizedFiles.map(f => f.name).join(', ')}\nMaximum size: 10MB per file`);
      return;
    }

    setIsUploading(true);
    
    // Start progress simulation
    const progressInterval = setInterval(() => {
      setUploadProgress(prev => {
        // Slowly increase to 90% (real completion will jump to 100%)
        if (prev < 90) {
          return prev + (Math.random() * 5);
        }
        return prev;
      });
    }, 500);
    
    try {
      const result = await uploadDocuments(files);
      setUploadedFiles(prev => [...prev, ...result.documents]);
      onUploadComplete(result.documents);
      setUploadProgress(100);
    } catch (error: any) {
      console.error('Upload failed:', error);
      
      // Provide more specific error messages
      if (error.code === 'ECONNABORTED') {
        setUploadError('Upload timed out. The server is taking too long to process your documents. Please try with smaller files or fewer documents.');
      } else if (error.response && error.response.status === 413) {
        setUploadError('Files too large. Please try uploading smaller documents or fewer at once.');
      } else if (error.message && error.message.includes('Network Error')) {
        setUploadError('Network error. Please check your internet connection and try again.');
      } else {
        setUploadError(`Upload failed: ${error.message || 'Unknown error'}. Please try again.`);
      }
    } finally {
      clearInterval(progressInterval);
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
                  Please wait while we analyze your files. This may take a few minutes for large documents.
                </p>
                <div className="mt-4 w-48 mx-auto bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full"
                    style={{ width: `${Math.min(uploadProgress, 100)}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  {uploadProgress < 100 ? 'Processing...' : 'Complete!'}
                </p>
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

      {/* Error Message */}
      {uploadError && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-2xl text-red-700">
          <div className="flex items-start">
            <div className="flex-shrink-0 mt-0.5">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Upload Error</h3>
              <div className="mt-1 text-sm text-red-700 whitespace-pre-line">
                {uploadError}
              </div>
              <div className="mt-3">
                <button
                  type="button"
                  onClick={() => setUploadError(null)}
                  className="inline-flex items-center px-3 py-1.5 border border-red-300 shadow-sm text-xs font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

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