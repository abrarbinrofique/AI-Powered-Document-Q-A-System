import { useState, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

interface QuestionGeneratorProps {
  projectId: string;
}

interface Citation {
  citation_id: string;
  document_name?: string;
  page_number: number;
  excerpt: string;
  relevance_score: number;
  citation_order: number;
}

interface Answer {
  answer_id: string;
  question_id: string;
  answer_text: string;
  is_ai_generated: boolean;
  confidence_score: number;
  retrieval_score: number;
  faithfulness_score: number;
  status: string;
  citations: Citation[];
  created_at: string;
}

interface Question {
  question_id: string;
  question_text: string;
  question_category?: string;
  question_number?: string;
  ground_truth_answer?: string;
  status: string;
}

export function QuestionGenerator({ projectId }: QuestionGeneratorProps) {
  const [questionText, setQuestionText] = useState('');
  const [generatedAnswer, setGeneratedAnswer] = useState<Answer | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [queryId, setQueryId] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [editedText, setEditedText] = useState('');
  const [bulkFile, setBulkFile] = useState<File | null>(null);
  const [batchProcessing, setBatchProcessing] = useState(false);
  const [batchAnswers, setBatchAnswers] = useState<Map<string, Answer>>(new Map());
  const [processingQuestions, setProcessingQuestions] = useState<Set<string>>(new Set());
  const queryClient = useQueryClient();

  // Fetch pending questions (uploaded but no answers)
  const { data: pendingQuestionsData } = useQuery({
    queryKey: ['pendingQuestions', projectId],
    queryFn: async () => {
      const response = await axios.get(`/api/v1/questions/project/${projectId}`);
      const allQuestions = response.data.questions || [];

      // Filter: Only questions WITHOUT answers
      const questionsWithoutAnswers = [];
      for (const question of allQuestions) {
        try {
          await axios.get(`/api/v1/questions/${question.question_id}/answer`);
          // If answer exists, skip this question
        } catch (error: any) {
          // No answer found (404), include this question
          if (error.response?.status === 404) {
            questionsWithoutAnswers.push(question);
          }
        }
      }

      return questionsWithoutAnswers;
    },
    refetchInterval: 5000
  });

  // Generate answer mutation
  const generateMutation = useMutation({
    mutationFn: async (text: string) => {
      const response = await axios.post('/api/v1/questions/generate', {
        question_text: text,
        project_id: projectId
      });
      return response.data;
    },
    onSuccess: (data) => {
      setQueryId(data.query_id || data.answer_id);
      setIsPolling(true);
    }
  });

  // Poll for answer result
  useEffect(() => {
    if (!isPolling || !queryId) return;

    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`/api/v1/queries/${queryId}`);
        if (response.data && response.data.answer_id) {
          setGeneratedAnswer(response.data);
          setEditedText(response.data.answer_text);
          setIsPolling(false);
        }
      } catch (error) {
        console.error('Error polling answer:', error);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [isPolling, queryId]);

  // Review mutation (Approve/Reject/Edit)
  const reviewMutation = useMutation({
    mutationFn: async (action: { action: string; edited_text?: string; review_notes?: string }) => {
      const response = await axios.post(`/api/v1/answers/${generatedAnswer?.answer_id}/review`, action);
      return response.data;
    },
    onSuccess: (data, variables) => {
      if (generatedAnswer) {
        setGeneratedAnswer({
          ...generatedAnswer,
          status: variables.action === 'approve' ? 'approved' : variables.action === 'reject' ? 'rejected' : 'edited',
          answer_text: variables.edited_text || generatedAnswer.answer_text
        });
      }
      setEditMode(false);

      // Invalidate questions query to update Question History tab
      if (variables.action === 'approve') {
        queryClient.invalidateQueries({ queryKey: ['questions', projectId] });
      }
    }
  });

  // Bulk upload mutation
  const bulkUploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(
        `/api/v1/questions/bulk-upload?project_id=${projectId}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      );
      return response.data;
    },
    onSuccess: (data) => {
      setBulkFile(null);
      // Clear any previous batch processing state
      setBatchAnswers(new Map());
      setProcessingQuestions(new Set());
      setBatchProcessing(false);
      // Refresh questions list
      queryClient.invalidateQueries({ queryKey: ['questions', projectId] });
      queryClient.invalidateQueries({ queryKey: ['pendingQuestions', projectId] });
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (questionText.trim()) {
      setGeneratedAnswer(null);
      setQueryId(null);
      generateMutation.mutate(questionText);
    }
  };

  const handleBulkUpload = (e: React.FormEvent) => {
    e.preventDefault();
    if (bulkFile) {
      bulkUploadMutation.mutate(bulkFile);
    }
  };

  const handleGenerateAllAnswers = async () => {
    if (!pendingQuestionsData || pendingQuestionsData.length === 0) return;

    setBatchProcessing(true);
    const processing = new Set<string>();

    for (const question of pendingQuestionsData) {
      processing.add(question.question_id);

      // Start generation for this question
      try {
        const response = await axios.post('/api/v1/questions/generate', {
          question_text: question.question_text,
          project_id: projectId
        });

        const queryId = response.data.query_id || response.data.answer_id;

        // Poll for this answer
        pollForAnswer(queryId, question.question_id);
      } catch (error) {
        console.error(`Failed to generate answer for question ${question.question_id}:`, error);
        processing.delete(question.question_id);
      }
    }

    setProcessingQuestions(processing);
  };

  const pollForAnswer = async (queryId: string, questionId: string) => {
    const maxAttempts = 60; // 2 minutes max
    let attempts = 0;

    const poll = setInterval(async () => {
      attempts++;

      try {
        const response = await axios.get(`/api/v1/queries/${queryId}`);

        if (response.data && response.data.answer_id) {
          // Answer ready
          setBatchAnswers(prev => new Map(prev).set(questionId, response.data));
          setProcessingQuestions(prev => {
            const newSet = new Set(prev);
            newSet.delete(questionId);
            return newSet;
          });
          clearInterval(poll);
        } else if (attempts >= maxAttempts) {
          // Timeout
          setProcessingQuestions(prev => {
            const newSet = new Set(prev);
            newSet.delete(questionId);
            return newSet;
          });
          clearInterval(poll);
        }
      } catch (error) {
        console.error('Polling error:', error);
        if (attempts >= maxAttempts) {
          setProcessingQuestions(prev => {
            const newSet = new Set(prev);
            newSet.delete(questionId);
            return newSet;
          });
          clearInterval(poll);
        }
      }
    }, 2000);
  };

  const handleBatchReview = async (questionId: string, action: string, editedText?: string) => {
    const answer = batchAnswers.get(questionId);
    if (!answer) return;

    try {
      if (action === 'reject') {
        // For reject: delete the question and answer completely
        await axios.delete(`/api/v1/questions/${questionId}`);

        // Remove from batch answers
        setBatchAnswers(prev => {
          const newMap = new Map(prev);
          newMap.delete(questionId);
          return newMap;
        });

        queryClient.invalidateQueries({ queryKey: ['questions', projectId] });
        queryClient.invalidateQueries({ queryKey: ['pendingQuestions', projectId] });
      } else {
        // For approve/edit: update answer status
        await axios.post(`/api/v1/answers/${answer.answer_id}/review`, {
          action,
          edited_text: editedText,
        });

        // Remove from batch answers if approved or edited
        if (action === 'approve' || action === 'edit') {
          setBatchAnswers(prev => {
            const newMap = new Map(prev);
            newMap.delete(questionId);
            return newMap;
          });
          queryClient.invalidateQueries({ queryKey: ['questions', projectId] });
          queryClient.invalidateQueries({ queryKey: ['pendingQuestions', projectId] });
        }
      }
    } catch (error) {
      console.error('Review failed:', error);
    }
  };

  const handleApprove = () => {
    reviewMutation.mutate({ action: 'approve' });
  };

  const handleReject = async () => {
    if (!confirm('Reject this answer? The question will be permanently deleted.')) {
      return;
    }

    try {
      // Delete the question (and its answer will be cascade deleted)
      if (generatedAnswer) {
        await axios.delete(`/api/v1/questions/${generatedAnswer.question_id}`);

        // Clear the generated answer and reset form
        setGeneratedAnswer(null);
        setQuestionText('');
        setQueryId(null);

        // Refresh lists
        queryClient.invalidateQueries({ queryKey: ['questions', projectId] });
        queryClient.invalidateQueries({ queryKey: ['pendingQuestions', projectId] });
      }
    } catch (error) {
      console.error('Failed to reject answer:', error);
      alert('Failed to delete question. Please try again.');
    }
  };

  const handleEdit = () => {
    setEditMode(true);
  };

  const handleSaveEdit = () => {
    reviewMutation.mutate({ action: 'edit', edited_text: editedText });
  };

  const handleDeleteQuestion = async (questionId: string) => {
    if (!confirm('Are you sure you want to delete this question? This action cannot be undone.')) {
      return;
    }

    try {
      await axios.delete(`/api/v1/questions/${questionId}`);
      // Refresh pending questions list
      queryClient.invalidateQueries({ queryKey: ['pendingQuestions', projectId] });
    } catch (error) {
      console.error('Failed to delete question:', error);
      alert('Failed to delete question. Please try again.');
    }
  };

  const handleClearAllQuestions = async () => {
    if (!pendingQuestionsData || pendingQuestionsData.length === 0) return;

    if (!confirm(`Delete all ${pendingQuestionsData.length} pending questions? This action cannot be undone.`)) {
      return;
    }

    try {
      // Delete all questions in parallel
      await Promise.all(
        pendingQuestionsData.map((q: Question) => axios.delete(`/api/v1/questions/${q.question_id}`))
      );
      // Refresh pending questions list
      queryClient.invalidateQueries({ queryKey: ['pendingQuestions', projectId] });
    } catch (error) {
      console.error('Failed to delete questions:', error);
      alert('Failed to delete some questions. Please try again.');
    }
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-700 bg-green-100';
    if (score >= 0.6) return 'text-yellow-700 bg-yellow-100';
    return 'text-red-700 bg-red-100';
  };

  const renderAnswerWithCitations = (text: string) => {
    const parts = text.split(/(\[\d+\])/g);
    return parts.map((part, i) => {
      const match = part.match(/\[(\d+)\]/);
      if (match) {
        const citationNum = parseInt(match[1]);
        return (
          <sup
            key={i}
            className="text-blue-600 font-semibold cursor-pointer hover:text-blue-800"
            title={`Jump to citation ${citationNum}`}
          >
            [{citationNum}]
          </sup>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div className="space-y-6">
      {/* Bulk Upload Section */}
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl border-2 border-purple-200 p-6 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              📤 Bulk Question Upload
            </h3>
            <p className="text-sm text-gray-600 mt-1">Upload multiple questions from CSV or Excel file</p>
          </div>
        </div>

        <form onSubmit={handleBulkUpload} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Select CSV or Excel File
            </label>
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={(e) => setBulkFile(e.target.files?.[0] || null)}
              className="block w-full text-sm text-gray-600
                file:mr-4 file:py-3 file:px-6
                file:rounded-xl file:border-0
                file:text-sm file:font-semibold
                file:bg-gradient-to-r file:from-purple-500 file:to-pink-600
                file:text-white file:shadow-lg
                hover:file:from-purple-600 hover:file:to-pink-700
                file:transform hover:file:scale-105
                file:transition-all file:duration-200
                hover:file:shadow-xl
                border-2 border-gray-300 rounded-xl
                hover:border-purple-400 transition-colors
                cursor-pointer"
            />
            {bulkFile && (
              <p className="text-sm text-purple-600 mt-2 font-medium">
                ✓ Selected: {bulkFile.name}
              </p>
            )}
          </div>

          <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-r-lg">
            <p className="text-sm text-blue-800 font-medium mb-2">📋 Required CSV/Excel Format:</p>
            <code className="text-xs text-blue-900 block bg-white p-2 rounded font-mono">
              question_number, question_text, question_category, ground_truth_answer
            </code>
            <p className="text-xs text-blue-700 mt-2">
              Only <strong>question_text</strong> is required. Other columns are optional.
            </p>
          </div>

          {bulkUploadMutation.isSuccess && (
            <div className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-xl shadow-md">
              <p className="text-sm text-green-700 font-semibold">
                ✓ Successfully uploaded {bulkUploadMutation.data.created_count} question(s)!
              </p>
              {bulkUploadMutation.data.error_count > 0 && (
                <p className="text-xs text-orange-600 mt-1">
                  ⚠️ {bulkUploadMutation.data.error_count} row(s) had errors
                </p>
              )}
            </div>
          )}

          {bulkUploadMutation.isError && (
            <div className="p-4 bg-gradient-to-r from-red-50 to-pink-50 border-2 border-red-300 rounded-xl shadow-md">
              <p className="text-sm text-red-700 font-semibold">
                ✗ Upload failed. Please check your file format.
              </p>
            </div>
          )}

          <button
            type="submit"
            disabled={!bulkFile || bulkUploadMutation.isPending}
            className="px-8 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-bold shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            {bulkUploadMutation.isPending ? '📤 Uploading...' : '📤 Upload Questions'}
          </button>
        </form>
      </div>

      {/* Pending Questions List - Professional Design */}
      {pendingQuestionsData && pendingQuestionsData.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gray-50">
            <div>
              <h3 className="text-xl font-bold text-gray-900">
                Uploaded Questions
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                {pendingQuestionsData.length} questions ready • Generate individually or batch process
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleClearAllQuestions}
                disabled={!pendingQuestionsData || pendingQuestionsData.length === 0}
                className="px-4 py-2.5 bg-red-50 text-red-600 border border-red-200 rounded-lg hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-sm hover:shadow transition-all duration-150 flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                <span>Clear All</span>
              </button>
              <button
                onClick={handleGenerateAllAnswers}
                disabled={batchProcessing || processingQuestions.size > 0}
                className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-sm hover:shadow transition-all duration-150 flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span>Generate All</span>
              </button>
            </div>
          </div>

          {/* Questions List */}
          <div className="divide-y divide-gray-100 max-h-[600px] overflow-y-auto">
            {pendingQuestionsData.map((q: any, idx: number) => (
              <div key={q.question_id} className="p-4 hover:bg-gray-50 transition-colors duration-150">
                <div className="flex items-start gap-4">
                  {/* Question Number */}
                  <div className="flex-shrink-0 w-10 h-10 bg-blue-50 text-blue-700 rounded-lg flex items-center justify-center font-semibold text-sm border border-blue-100">
                    {idx + 1}
                  </div>

                  {/* Question Content */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 mb-2 leading-relaxed">{q.question_text}</p>
                    <div className="flex flex-wrap gap-2">
                      {q.question_category && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-md bg-blue-50 text-blue-700 text-xs font-medium border border-blue-100">
                          {q.question_category}
                        </span>
                      )}
                      {q.question_number && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-md bg-gray-50 text-gray-700 text-xs font-medium border border-gray-200">
                          #{q.question_number}
                        </span>
                      )}
                    </div>
                  </div>
                  {/* Actions */}
                  <div className="flex-shrink-0 flex items-center gap-2">
                    <button
                      onClick={() => {
                        setQuestionText(q.question_text);
                        setGeneratedAnswer(null);
                        setQueryId(null);
                        generateMutation.mutate(q.question_text);
                      }}
                      disabled={generateMutation.isPending || isPolling || processingQuestions.has(q.question_id)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm shadow-sm hover:shadow transition-all duration-150 flex items-center gap-1.5"
                    >
                      {processingQuestions.has(q.question_id) ? (
                        <>
                          <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          <span>Processing</span>
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                          <span>Generate</span>
                        </>
                      )}
                    </button>

                    {/* Options Menu */}
                    <div className="relative group">
                      <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors duration-150">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                        </svg>
                      </button>
                      <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-150 z-10">
                        <button
                          onClick={() => alert(`Question: ${q.question_text}\nCategory: ${q.question_category || 'N/A'}\nNumber: ${q.question_number || 'N/A'}\nGround Truth: ${q.ground_truth_answer || 'None'}`)}
                          className="w-full text-left px-3 py-2 hover:bg-gray-50 text-xs text-gray-700 font-medium flex items-center gap-2"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                          View Details
                        </button>
                        <button
                          onClick={() => {
                            const newText = prompt('Edit question:', q.question_text);
                            if (newText) {
                              alert('Edit functionality coming soon!');
                            }
                          }}
                          className="w-full text-left px-3 py-2 hover:bg-gray-50 text-xs text-gray-700 font-medium flex items-center gap-2"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                          Edit Question
                        </button>
                        <button
                          onClick={() => handleDeleteQuestion(q.question_id)}
                          className="w-full text-left px-3 py-2 hover:bg-red-50 text-xs text-red-600 font-medium flex items-center gap-2 rounded-b-lg"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Batch Answers Review Section */}
      {(batchAnswers.size > 0 || processingQuestions.size > 0) && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border-2 border-blue-300 p-6 shadow-lg">
          <h3 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-4">
            🤖 Generated Answers ({batchAnswers.size} / {pendingQuestionsData?.length || 0})
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            Review and approve each answer below. Approved answers will move to Question History.
          </p>

          {processingQuestions.size > 0 && (
            <div className="mb-4 p-4 bg-yellow-100 border-2 border-yellow-300 rounded-lg">
              <p className="text-sm font-semibold text-yellow-800">
                ⏳ Processing {processingQuestions.size} question(s)...
              </p>
            </div>
          )}

          <div className="space-y-4">
            {Array.from(batchAnswers.entries()).map(([questionId, answer]) => {
              const question = pendingQuestionsData?.find((q: any) => q.question_id === questionId);
              if (!question) return null;

              return (
                <div key={questionId} className="bg-white rounded-xl p-6 border-2 border-blue-200 shadow-md">
                  {/* Question */}
                  <div className="mb-4 pb-4 border-b-2 border-gray-200">
                    <div className="flex items-start gap-2 mb-2">
                      <span className="text-2xl">❓</span>
                      <div className="flex-1">
                        <p className="font-bold text-gray-900 text-lg">{question.question_text}</p>
                        <div className="flex gap-2 mt-2">
                          {question.question_category && (
                            <span className="px-3 py-1 bg-blue-100 text-blue-700 text-xs rounded-full font-semibold">
                              {question.question_category}
                            </span>
                          )}
                          {question.question_number && (
                            <span className="px-3 py-1 bg-gray-100 text-gray-700 text-xs rounded-full font-semibold">
                              #{question.question_number}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Answer */}
                  <div className="mb-4">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-2xl">💡</span>
                      <h4 className="font-bold text-gray-900">AI Generated Answer</h4>
                      <span className={`ml-auto px-3 py-1 rounded-lg text-xs font-bold ${getConfidenceColor(answer.confidence_score)}`}>
                        {Math.round(answer.confidence_score * 100)}% Confidence
                      </span>
                    </div>
                    <div className="prose prose-sm max-w-none text-gray-700 bg-gray-50 rounded-lg p-4">
                      {renderAnswerWithCitations(answer.answer_text)}
                    </div>
                  </div>

                  {/* Citations */}
                  {answer.citations && answer.citations.length > 0 && (
                    <div className="mb-4">
                      <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                        <span>📚</span>
                        <span>Source Citations ({answer.citations.length})</span>
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {answer.citations.slice(0, 4).map((citation) => (
                          <div key={citation.citation_id} className="text-xs bg-gray-50 rounded-lg p-3 border border-gray-200">
                            <p className="font-semibold text-gray-900 mb-1">{citation.document_name}</p>
                            <p className="text-gray-600 line-clamp-2">{citation.excerpt}</p>
                            <p className="text-gray-500 mt-1">Page {citation.page_number} • {Math.round(citation.relevance_score * 100)}% relevant</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex gap-3 pt-4 border-t-2 border-gray-200">
                    <button
                      onClick={() => handleBatchReview(questionId, 'approve')}
                      className="flex-1 px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl hover:from-green-600 hover:to-emerald-700 font-bold shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 flex items-center justify-center gap-2"
                    >
                      <span>✓</span>
                      <span>Approve</span>
                    </button>
                    <button
                      onClick={() => {
                        const edited = prompt('Edit answer:', answer.answer_text);
                        if (edited) handleBatchReview(questionId, 'edit', edited);
                      }}
                      className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl hover:from-blue-600 hover:to-indigo-700 font-bold shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 flex items-center justify-center gap-2"
                    >
                      <span>✎</span>
                      <span>Edit</span>
                    </button>
                    <button
                      onClick={() => handleBatchReview(questionId, 'reject')}
                      className="flex-1 px-6 py-3 bg-gradient-to-r from-red-500 to-pink-600 text-white rounded-xl hover:from-red-600 hover:to-pink-700 font-bold shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 flex items-center justify-center gap-2"
                    >
                      <span>✗</span>
                      <span>Reject</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Question Input Section */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Ask a Question</h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Enter your due diligence question
            </label>
            <textarea
              value={questionText}
              onChange={(e) => setQuestionText(e.target.value)}
              rows={4}
              placeholder="e.g., What is the company's revenue for FY2023?&#10;e.g., What are the main risk factors?&#10;e.g., Who are the key executives?"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none"
              required
            />
          </div>

          <button
            type="submit"
            disabled={!questionText.trim() || generateMutation.isPending || isPolling}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
          >
            {isPolling ? 'Generating Answer...' : generateMutation.isPending ? 'Starting...' : 'Generate AI Answer'}
          </button>
        </form>

        {generateMutation.isError && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">
              Failed to generate answer. Please ensure documents are uploaded and try again.
            </p>
          </div>
        )}
      </div>

      {/* Loading State - 3D Animation */}
      {isPolling && (
        <div className="bg-gradient-to-br from-blue-50 to-indigo-100 border-2 border-blue-300 rounded-2xl p-8 shadow-xl">
          <div className="flex flex-col items-center justify-center space-y-6">
            {/* 3D Cube Animation */}
            <div className="relative w-24 h-24">
              <div className="absolute inset-0 animate-spin-slow">
                <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl shadow-2xl transform rotate-45 animate-pulse"></div>
              </div>
              <div className="absolute inset-0 animate-spin-reverse delay-75">
                <div className="w-24 h-24 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl shadow-2xl transform -rotate-45 opacity-50"></div>
              </div>
            </div>

            {/* Loading Text */}
            <div className="text-center">
              <p className="text-xl font-bold text-blue-900 mb-2 animate-pulse">🤖 AI is thinking...</p>
              <div className="flex items-center space-x-2 text-sm text-blue-700">
                <span className="animate-bounce">📄</span>
                <span>Searching documents</span>
                <span className="animate-pulse">→</span>
                <span className="animate-bounce delay-100">🔍</span>
                <span>Retrieving context</span>
                <span className="animate-pulse delay-75">→</span>
                <span className="animate-bounce delay-200">✨</span>
                <span>Generating answer</span>
              </div>
            </div>

            {/* Progress Dots */}
            <div className="flex space-x-2">
              <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce"></div>
              <div className="w-3 h-3 bg-indigo-600 rounded-full animate-bounce delay-100"></div>
              <div className="w-3 h-3 bg-purple-600 rounded-full animate-bounce delay-200"></div>
            </div>
          </div>
        </div>
      )}

      {/* Generated Answer Section */}
      {generatedAnswer && (
        <div className="space-y-6">
          {/* Confidence Score Panel */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Confidence Metrics</h3>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className={`inline-flex items-center px-4 py-2 rounded-lg font-semibold ${getConfidenceColor(generatedAnswer.confidence_score)}`}>
                  {Math.round(generatedAnswer.confidence_score * 100)}%
                </div>
                <p className="text-xs text-gray-600 mt-2">Overall</p>
              </div>

              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {Math.round(generatedAnswer.retrieval_score * 100)}%
                </div>
                <p className="text-xs text-gray-600 mt-1">Retrieval Quality</p>
              </div>

              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {Math.round(generatedAnswer.faithfulness_score * 100)}%
                </div>
                <p className="text-xs text-gray-600 mt-1">Faithfulness</p>
              </div>

              <div className="text-center">
                <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                  generatedAnswer.status === 'approved' ? 'bg-green-100 text-green-800' :
                  generatedAnswer.status === 'rejected' ? 'bg-red-100 text-red-800' :
                  generatedAnswer.status === 'edited' ? 'bg-purple-100 text-purple-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {generatedAnswer.status.replace('_', ' ').toUpperCase()}
                </div>
                <p className="text-xs text-gray-600 mt-1">Status</p>
              </div>
            </div>
          </div>

          {/* Answer & Citations Grid */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Answer Panel */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">AI-Generated Answer</h3>
                {generatedAnswer.is_ai_generated && (
                  <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs font-medium rounded">
                    AI Generated
                  </span>
                )}
              </div>

              {editMode ? (
                <textarea
                  value={editedText}
                  onChange={(e) => setEditedText(e.target.value)}
                  rows={10}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none font-sans"
                />
              ) : (
                <div className="prose prose-sm max-w-none text-gray-700 leading-relaxed">
                  {renderAnswerWithCitations(generatedAnswer.answer_text)}
                </div>
              )}

              {/* Human-in-the-Loop Actions */}
              <div className="mt-6 pt-4 border-t border-gray-200">
                <p className="text-xs font-medium text-gray-700 mb-3">Human Review Required</p>

                {editMode ? (
                  <div className="flex gap-2">
                    <button
                      onClick={handleSaveEdit}
                      disabled={reviewMutation.isPending}
                      className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium transition-colors"
                    >
                      {reviewMutation.isPending ? 'Saving...' : 'Save Changes'}
                    </button>
                    <button
                      onClick={() => {
                        setEditMode(false);
                        setEditedText(generatedAnswer.answer_text);
                      }}
                      className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <>
                    {generatedAnswer.status === 'approved' || generatedAnswer.status === 'rejected' ? (
                      <div className="text-center py-4">
                        <p className={`text-sm font-medium ${
                          generatedAnswer.status === 'approved' ? 'text-green-700' : 'text-red-700'
                        }`}>
                          {generatedAnswer.status === 'approved'
                            ? '✓ Answer has been approved and saved to Question History'
                            : '✗ Answer has been rejected'}
                        </p>
                      </div>
                    ) : (
                      <div className="flex gap-2">
                        <button
                          onClick={handleApprove}
                          disabled={reviewMutation.isPending}
                          className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium transition-colors flex items-center justify-center gap-2"
                        >
                          <span>✓</span> Approve
                        </button>
                        <button
                          onClick={handleEdit}
                          disabled={reviewMutation.isPending}
                          className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors flex items-center justify-center gap-2"
                        >
                          <span>✎</span> Edit
                        </button>
                        <button
                          onClick={handleReject}
                          disabled={reviewMutation.isPending}
                          className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 font-medium transition-colors flex items-center justify-center gap-2"
                        >
                          <span>✗</span> Reject
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Citations Panel */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Source Citations ({generatedAnswer.citations?.length || 0})
              </h3>

              {generatedAnswer.citations && generatedAnswer.citations.length > 0 ? (
                <div className="space-y-3 max-h-[500px] overflow-y-auto">
                  {generatedAnswer.citations.map((citation) => (
                    <div
                      key={citation.citation_id}
                      className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center font-bold text-sm">
                          {citation.citation_order}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-2">
                            <p className="font-medium text-gray-900 text-sm truncate">
                              {citation.document_name || 'Document'}
                            </p>
                            <span className="text-xs text-gray-500 whitespace-nowrap ml-2">
                              Page {citation.page_number}
                            </span>
                          </div>
                          <p className="text-xs text-gray-600 leading-relaxed mb-2">
                            {citation.excerpt}
                          </p>
                          <div className="flex items-center gap-2">
                            <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                              <div
                                className="bg-blue-600 h-1.5 rounded-full"
                                style={{ width: `${citation.relevance_score * 100}%` }}
                              ></div>
                            </div>
                            <span className="text-xs text-gray-600 whitespace-nowrap">
                              {Math.round(citation.relevance_score * 100)}% relevant
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <p className="text-sm">No citations available</p>
                  <p className="text-xs mt-1">Answer may not be grounded in documents</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
