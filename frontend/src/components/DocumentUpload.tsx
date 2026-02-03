
import { useState } from 'react';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import axios from 'axios';

interface DocumentUploadProps {
  projectId: string;
}

interface Document {
  document_id: string;
  filename: string;
  file_type: string;
  processing_status: string;
  chunk_count: number;
  created_at: string;
}

export function DocumentUpload({ projectId }: DocumentUploadProps) {
  const [files, setFiles] = useState<FileList | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Fetch documents for this project
  const { data: documentsData } = useQuery({
    queryKey: ['documents', projectId],
    queryFn: async () => {
      const response = await axios.get(`/api/v1/documents/project/${projectId}`);
      return response.data;
    },
    refetchInterval: 3000 // Refresh every 3 seconds to show processing status
  });

  const documents: Document[] = documentsData?.documents || [];

  // Check if any documents are being processed
  const hasProcessingDocuments = documents.some(doc => doc.processing_status === 'processing');

  const uploadMutation = useMutation({
    mutationFn: async (files: FileList) => {
      const formData = new FormData();
      formData.append('project_id', projectId);

      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }

      const response = await axios.post('/api/v1/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    },
    onSuccess: (data) => {
      setJobId(data.job_id);
      setFiles(null);
      queryClient.invalidateQueries({ queryKey: ['documents', projectId] });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: async (documentId: string) => {
      const response = await axios.delete(`/api/v1/documents/${documentId}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', projectId] });
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (files && files.length > 0) {
      uploadMutation.mutate(files);
    }
  };

  return (
    <div className="space-y-6">
      <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
        Upload Documents
      </h3>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Select Documents (PDF, DOCX, TXT)
          </label>
          <input
            type="file"
            multiple
            accept=".pdf,.docx,.doc,.txt"
            onChange={(e) => setFiles(e.target.files)}
            className="block w-full text-sm text-gray-600
              file:mr-4 file:py-3 file:px-6
              file:rounded-xl file:border-0
              file:text-sm file:font-semibold
              file:bg-gradient-to-r file:from-blue-500 file:to-indigo-600
              file:text-white file:shadow-lg
              hover:file:from-blue-600 hover:file:to-indigo-700
              file:transform hover:file:scale-105
              file:transition-all file:duration-200
              hover:file:shadow-xl
              border-2 border-gray-300 rounded-xl
              hover:border-blue-400 transition-colors
              cursor-pointer"
          />
          {files && files.length > 0 && (
            <p className="text-sm text-blue-600 mt-2 font-medium">
              ✓ {files.length} file(s) selected
            </p>
          )}
        </div>

        <button
          type="submit"
          disabled={!files || files.length === 0 || uploadMutation.isPending}
          className="px-8 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-bold shadow-lg hover:shadow-xl transform hover:scale-105"
        >
          {uploadMutation.isPending ? '📤 Uploading...' : '📤 Upload Documents'}
        </button>
      </form>

      {uploadMutation.isSuccess && jobId && (
        <div className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-xl shadow-md">
          <p className="text-sm text-green-700 font-semibold">
            ✓ Documents uploaded successfully! Processing job ID: {jobId}
          </p>
        </div>
      )}

      {uploadMutation.isError && (
        <div className="p-4 bg-gradient-to-r from-red-50 to-pink-50 border-2 border-red-300 rounded-xl shadow-md">
          <p className="text-sm text-red-700 font-semibold">
            ✗ Upload failed. Please try again.
          </p>
        </div>
      )}

      {/* 3D Processing Animation */}
      {(uploadMutation.isPending || hasProcessingDocuments) && (
        <div className="bg-gradient-to-br from-blue-50 to-indigo-100 border-2 border-blue-300 rounded-2xl p-8 shadow-xl">
          <div className="flex flex-col items-center justify-center space-y-6">
            {/* 3D Document Stack Animation */}
            <div className="relative w-24 h-24">
              <div className="absolute inset-0 animate-spin-slow">
                <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl shadow-2xl transform rotate-12 animate-pulse"></div>
              </div>
              <div className="absolute inset-0 animate-spin-reverse delay-75">
                <div className="w-24 h-24 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl shadow-2xl transform -rotate-12 opacity-60"></div>
              </div>
              <div className="absolute inset-4 flex items-center justify-center">
                <span className="text-4xl animate-bounce">📄</span>
              </div>
            </div>

            {/* Processing Steps */}
            <div className="text-center">
              <p className="text-xl font-bold text-blue-900 mb-2 animate-pulse">
                {uploadMutation.isPending ? '📤 Uploading documents...' : '⚙️ Processing documents...'}
              </p>
              <div className="flex items-center space-x-2 text-sm text-blue-700">
                <span className="animate-bounce">📁</span>
                <span>Reading files</span>
                <span className="animate-pulse">→</span>
                <span className="animate-bounce delay-100">✂️</span>
                <span>Chunking text</span>
                <span className="animate-pulse delay-75">→</span>
                <span className="animate-bounce delay-200">🔍</span>
                <span>Creating embeddings</span>
              </div>
            </div>

            {/* Animated Dots */}
            <div className="flex space-x-2">
              <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce"></div>
              <div className="w-3 h-3 bg-indigo-600 rounded-full animate-bounce delay-100"></div>
              <div className="w-3 h-3 bg-purple-600 rounded-full animate-bounce delay-200"></div>
            </div>
          </div>
        </div>
      )}

      {/* Uploaded Documents List */}
      <div className="mt-8 pt-8 border-t-2 border-gray-200">
        <h4 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-6">
          Uploaded Documents ({documents.length})
        </h4>

        {documents.length === 0 ? (
          <div className="text-center py-12 bg-gradient-to-br from-gray-50 to-blue-50 border-2 border-gray-200 rounded-2xl">
            <div className="text-5xl mb-3">📁</div>
            <p className="text-gray-600 font-medium">No documents uploaded yet</p>
            <p className="text-sm text-gray-500 mt-1">Upload documents to get started</p>
          </div>
        ) : (
          <div className="space-y-3">
            {documents.map((doc) => (
              <div
                key={doc.document_id}
                className="bg-gradient-to-r from-white to-blue-50 border-2 border-gray-200 rounded-xl p-5 hover:border-blue-400 hover:shadow-lg transition-all duration-200 transform hover:scale-[1.01]"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-gray-900 truncate text-lg">{doc.filename}</p>
                    <div className="flex items-center gap-3 mt-2">
                      <span className="text-sm text-gray-600 font-medium">
                        {doc.file_type.toUpperCase()} • {doc.chunk_count} chunks
                      </span>
                      <span className={`inline-flex items-center px-3 py-1 rounded-lg text-xs font-bold shadow-sm ${
                        doc.processing_status === 'completed' ? 'bg-gradient-to-r from-green-100 to-emerald-100 text-green-800 border-2 border-green-300' :
                        doc.processing_status === 'processing' ? 'bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-800 animate-pulse border-2 border-blue-300' :
                        doc.processing_status === 'failed' ? 'bg-gradient-to-r from-red-100 to-pink-100 text-red-800 border-2 border-red-300' :
                        'bg-gradient-to-r from-yellow-100 to-orange-100 text-yellow-800 border-2 border-yellow-300'
                      }`}>
                        {doc.processing_status === 'completed' && '✓ '}
                        {doc.processing_status === 'processing' && '⟳ '}
                        {doc.processing_status === 'failed' && '✗ '}
                        {doc.processing_status.toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 ml-4">
                    <div className="text-sm text-gray-600 whitespace-nowrap font-medium">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </div>
                    <button
                      onClick={() => {
                        if (window.confirm(`Delete ${doc.filename}?`)) {
                          deleteMutation.mutate(doc.document_id);
                        }
                      }}
                      disabled={deleteMutation.isPending}
                      className="p-2.5 text-red-600 hover:bg-red-100 rounded-xl transition-all duration-200 disabled:opacity-50 hover:shadow-md transform hover:scale-110 border-2 border-transparent hover:border-red-300"
                      title="Delete document"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M3 6h18"></path>
                        <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                        <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
