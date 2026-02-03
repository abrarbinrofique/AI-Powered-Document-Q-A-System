import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { DocumentUpload } from './DocumentUpload';
import { QuestionGenerator } from './QuestionGenerator';
import { AnswerReview } from './AnswerReview';

const STORAGE_KEY = 'ddq_last_selected_project';

export function Dashboard() {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'upload' | 'generate' | 'review'>('upload');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  const [newProjectApiKey, setNewProjectApiKey] = useState('');
  const queryClient = useQueryClient();

  // Fetch projects
  const { data: projectsData } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/projects');
      return response.data;
    }
  });

  const projects = projectsData || [];

  // Load last selected project from localStorage on mount
  useEffect(() => {
    const savedProjectId = localStorage.getItem(STORAGE_KEY);
    if (savedProjectId && projects.length > 0) {
      // Check if the saved project still exists
      const projectExists = projects.some((p: any) => p.project_id === savedProjectId);
      if (projectExists) {
        setSelectedProjectId(savedProjectId);
      }
    }
  }, [projects]);

  // Save selected project to localStorage whenever it changes
  useEffect(() => {
    if (selectedProjectId) {
      localStorage.setItem(STORAGE_KEY, selectedProjectId);
    }
  }, [selectedProjectId]);

  // Create project mutation
  const createProjectMutation = useMutation({
    mutationFn: async (data: { name: string; description: string; api_key: string }) => {
      // Save API key first (validate and encrypt)
      if (data.api_key) {
        await axios.post('/api/v1/settings/api-keys/validate', {
          provider: 'openai',
          api_key: data.api_key
        });
      }

      // Create project
      const projectResponse = await axios.post('/api/v1/projects', {
        name: data.name,
        description: data.description
      });

      return projectResponse.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setSelectedProjectId(data.project_id);
      setShowCreateModal(false);
      setNewProjectName('');
      setNewProjectDescription('');
      setNewProjectApiKey('');
    }
  });

  const handleCreateProject = (e: React.FormEvent) => {
    e.preventDefault();
    if (newProjectName.trim() && newProjectApiKey.trim()) {
      createProjectMutation.mutate({
        name: newProjectName,
        description: newProjectDescription,
        api_key: newProjectApiKey
      });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white drop-shadow-md">DDQ Agent</h1>
              <p className="text-sm text-blue-100 mt-1">Multi-tenant Due Diligence Questionnaire Automation</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Project Selector */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-semibold text-gray-700">
              Select Project
            </label>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-semibold rounded-lg hover:from-blue-700 hover:to-indigo-700 transform hover:scale-105 transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              + Create New Project
            </button>
          </div>
          <select
            value={selectedProjectId || ''}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none bg-white text-gray-900 shadow-sm hover:border-blue-400 transition-colors"
          >
            <option value="">
              {projects.length === 0 ? 'No projects - Create one to get started' : 'Select a project...'}
            </option>
            {projects.map((project: any) => (
              <option key={project.project_id} value={project.project_id}>
                {project.name}
              </option>
            ))}
          </select>
        </div>

        {/* Tabs */}
        {selectedProjectId && (
          <>
            <div className="bg-white rounded-xl shadow-md p-1 mb-6">
              <nav className="flex space-x-2">
                <button
                  onClick={() => setActiveTab('upload')}
                  className={`${
                    activeTab === 'upload'
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  } flex-1 py-3 px-4 rounded-lg font-semibold text-sm transition-all duration-200`}
                >
                  📄 Upload Documents
                </button>
                <button
                  onClick={() => setActiveTab('generate')}
                  className={`${
                    activeTab === 'generate'
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  } flex-1 py-3 px-4 rounded-lg font-semibold text-sm transition-all duration-200`}
                >
                  🤖 Generate Answers
                </button>
                <button
                  onClick={() => setActiveTab('review')}
                  className={`${
                    activeTab === 'review'
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  } flex-1 py-3 px-4 rounded-lg font-semibold text-sm transition-all duration-200`}
                >
                  📚 Question History
                </button>
              </nav>
            </div>

            {/* Tab Content */}
            <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
              <div style={{ display: activeTab === 'upload' ? 'block' : 'none' }}>
                <DocumentUpload projectId={selectedProjectId} />
              </div>
              <div style={{ display: activeTab === 'generate' ? 'block' : 'none' }}>
                <QuestionGenerator projectId={selectedProjectId} />
              </div>
              <div style={{ display: activeTab === 'review' ? 'block' : 'none' }}>
                <AnswerReview projectId={selectedProjectId} />
              </div>
            </div>
          </>
        )}

        {!selectedProjectId && projects.length > 0 && (
          <div className="text-center py-12">
            <div className="bg-white rounded-xl shadow-lg p-8 max-w-md mx-auto border-2 border-blue-100">
              <p className="text-gray-600 text-lg">👆 Select a project to get started</p>
            </div>
          </div>
        )}

        {!selectedProjectId && projects.length === 0 && (
          <div className="text-center py-12">
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-2xl p-10 max-w-md mx-auto shadow-xl">
              <div className="text-6xl mb-4">🚀</div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">Welcome to DDQ Agent!</h3>
              <p className="text-gray-600 mb-6">
                Get started by creating your first project. A project organizes your documents and questionnaires.
              </p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 font-bold text-lg shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                Create Your First Project
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 m-4 border-2 border-blue-100 transform scale-100 animate-in">
            <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-6">Create New Project</h2>

            <form onSubmit={handleCreateProject} className="space-y-5">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Project Name *
                </label>
                <input
                  type="text"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="e.g., Q1 2024 Due Diligence"
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none bg-white text-gray-900 placeholder-gray-400 shadow-sm hover:border-blue-400 transition-colors"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Description (Optional)
                </label>
                <textarea
                  value={newProjectDescription}
                  onChange={(e) => setNewProjectDescription(e.target.value)}
                  placeholder="Brief description of this DDQ project..."
                  rows={3}
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none bg-white text-gray-900 placeholder-gray-400 shadow-sm hover:border-blue-400 transition-colors"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  OpenAI API Key *
                </label>
                <input
                  type="password"
                  value={newProjectApiKey}
                  onChange={(e) => setNewProjectApiKey(e.target.value)}
                  placeholder="sk-..."
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none bg-white text-gray-900 placeholder-gray-400 shadow-sm hover:border-blue-400 transition-colors font-mono text-sm"
                  required
                />
                <p className="text-xs text-gray-500 mt-2">
                  Your API key is encrypted and stored securely. Get your key from{' '}
                  <a
                    href="https://platform.openai.com/api-keys"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    OpenAI Platform
                  </a>
                </p>
              </div>

              {createProjectMutation.isError && (
                <div className="p-4 bg-red-50 border-2 border-red-200 rounded-xl shadow-sm">
                  <p className="text-sm text-red-700 font-medium">
                    {createProjectMutation.error?.response?.data?.detail?.includes('duplicate') ||
                     createProjectMutation.error?.response?.data?.detail?.includes('already exists')
                      ? 'A project with this name already exists. Please choose a different name.'
                      : createProjectMutation.error?.response?.data?.detail?.includes('Invalid API key')
                      ? 'Invalid OpenAI API key. Please check your API key and try again.'
                      : 'Failed to create project. Please try again.'}
                  </p>
                </div>
              )}

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewProjectName('');
                    setNewProjectDescription('');
                    setNewProjectApiKey('');
                  }}
                  className="flex-1 px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 font-semibold shadow-sm hover:shadow"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createProjectMutation.isPending || !newProjectName.trim() || !newProjectApiKey.trim()}
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-bold shadow-lg hover:shadow-xl transform hover:scale-105"
                >
                  {createProjectMutation.isPending ? 'Creating...' : 'Create Project 🚀'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
