import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';

interface ApiKeySetupProps {
  onComplete: () => void;
}

export function ApiKeySetup({ onComplete }: ApiKeySetupProps) {
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState('');

  const validateMutation = useMutation({
    mutationFn: async (key: string) => {
      const response = await axios.post('/api/v1/settings/api-keys/validate', {
        provider: 'openai',
        api_key: key
      });
      return response.data;
    },
    onSuccess: () => {
      localStorage.setItem('api_key_configured', 'true');
      onComplete();
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Invalid API key');
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!apiKey.startsWith('sk-')) {
      setError('Invalid OpenAI API key format. Must start with "sk-"');
      return;
    }

    validateMutation.mutate(apiKey);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="mb-4">
          <h2 className="text-2xl font-bold text-gray-900">API Key Required</h2>
          <p className="text-gray-600 mt-2">
            Enter your OpenAI API key to enable document processing and answer generation.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              OpenAI API Key
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-proj-..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              Get your key from{' '}
              <a
                href="https://platform.openai.com/api-keys"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                platform.openai.com/api-keys
              </a>
            </p>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={validateMutation.isPending || !apiKey}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {validateMutation.isPending ? 'Validating...' : 'Validate & Save'}
          </button>

          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Security</h4>
            <ul className="text-xs text-gray-600 space-y-1">
              <li>✓ Stored encrypted in database</li>
              <li>✓ Never sent to our servers (only to OpenAI)</li>
              <li>✓ You can update/remove anytime</li>
            </ul>
          </div>
        </form>
      </div>
    </div>
  );
}
