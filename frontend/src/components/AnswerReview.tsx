import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

interface AnswerReviewProps {
  projectId: string;
}

interface EvaluationMetrics {
  bleu_score: number | null;
  rouge_1_f1: number | null;
  rouge_2_f1: number | null;
  rouge_l_f1: number | null;
  semantic_similarity: number | null;
  overall_score: number | null;
}

export function AnswerReview({ projectId }: AnswerReviewProps) {
  const [selectedQuestionId, setSelectedQuestionId] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedText, setEditedText] = useState('');
  const [limit, setLimit] = useState(10);
  const [evaluationMetrics, setEvaluationMetrics] = useState<EvaluationMetrics | null>(null);
  const queryClient = useQueryClient();

  // Fetch questions (approved only)
  const { data: questionsData, isLoading: questionsLoading } = useQuery({
    queryKey: ['questions', projectId],
    queryFn: async () => {
      const response = await axios.get(`/api/v1/questions/project/${projectId}`);
      const allQuestions = response.data.questions || [];
      // Only show questions that have approved answers
      const questionsWithApprovedAnswers = [];

      for (const question of allQuestions) {
        try {
          const answerResponse = await axios.get(`/api/v1/questions/${question.question_id}/answer`);
          // Only include if answer exists and is approved
          if (answerResponse.data && answerResponse.data.status === 'approved') {
            questionsWithApprovedAnswers.push(question);
          }
        } catch (error) {
          // Skip questions without answers
          continue;
        }
      }

      return questionsWithApprovedAnswers;
    }
  });

  // Fetch answer for selected question
  const { data: answerData } = useQuery({
    queryKey: ['answer', selectedQuestionId],
    queryFn: async () => {
      if (!selectedQuestionId) return null;
      const response = await axios.get(`/api/v1/questions/${selectedQuestionId}/answer`);
      return response.data;
    },
    enabled: !!selectedQuestionId
  });

  // Fetch question details (for ground truth)
  const selectedQuestion = questionsData?.find((q: any) => q.question_id === selectedQuestionId);
  const hasGroundTruth = selectedQuestion?.ground_truth_answer && selectedQuestion.ground_truth_answer.trim();

  const reviewMutation = useMutation({
    mutationFn: async ({ answerId, action, editedText }: any) => {
      const response = await axios.post(`/api/v1/answers/${answerId}/review`, {
        action,
        edited_text: editedText
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['answer'] });
      setIsEditing(false);
    }
  });

  // Evaluation mutation
  const evaluateMutation = useMutation({
    mutationFn: async (answerId: string) => {
      const response = await axios.post(`/api/v1/answers/${answerId}/evaluate`);
      return response.data;
    },
    onSuccess: (data) => {
      if (data.metrics) {
        setEvaluationMetrics(data.metrics);
      }
    }
  });

  const handleReview = (action: string) => {
    if (!answerData) return;

    reviewMutation.mutate({
      answerId: answerData.answer_id,
      action,
      editedText: action === 'edit' ? editedText : undefined
    });
  };

  const handleEvaluate = () => {
    if (!answerData?.answer_id) return;
    evaluateMutation.mutate(answerData.answer_id);
  };

  // Reset evaluation metrics when question changes
  useState(() => {
    setEvaluationMetrics(null);
  });

  const displayedQuestions = questionsData?.slice(0, limit) || [];

  const getScoreColor = (score: number | null) => {
    if (score === null) return 'bg-gray-100 text-gray-700';
    if (score >= 0.8) return 'bg-green-100 text-green-800 border-green-300';
    if (score >= 0.6) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    return 'bg-red-100 text-red-800 border-red-300';
  };

  return (
    <div className="space-y-4">
      {/* Header with limit selector */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">Question History</h3>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Show last:</label>
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="px-3 py-1 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm"
          >
            <option value={5}>5 questions</option>
            <option value={10}>10 questions</option>
          </select>
        </div>
      </div>

      {/* Questions List and Answer Display */}
      <div className={`grid gap-4 ${selectedQuestionId && answerData ? 'grid-cols-3' : 'grid-cols-1'}`}>
        {/* Left Panel - Questions List */}
        <div className={`${selectedQuestionId && answerData ? 'col-span-1' : 'col-span-1'} border border-gray-200 rounded-lg p-4 max-h-[600px] overflow-y-auto`}>
          <h4 className="font-medium mb-3 text-gray-900">Questions ({displayedQuestions.length})</h4>
          {displayedQuestions.length === 0 ? (
            <p className="text-sm text-gray-500">No questions with answers yet</p>
          ) : (
            <div className="space-y-2">
              {displayedQuestions.map((question: any) => (
                <button
                  key={question.question_id}
                  onClick={() => setSelectedQuestionId(question.question_id)}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    selectedQuestionId === question.question_id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                  }`}
                >
                  <p className="text-sm font-medium text-gray-900 line-clamp-2">
                    {question.question_text}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(question.created_at).toLocaleDateString()}
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right Panel - Answer Display (only shown when question is selected) */}
        {selectedQuestionId && answerData && (
        <div className="col-span-2 space-y-4">
          {/* Evaluation Section (if ground truth exists) */}
          {hasGroundTruth && (
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-xl p-6 shadow-md">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  📊 Ground Truth Evaluation
                </h4>
                <button
                  onClick={handleEvaluate}
                  disabled={evaluateMutation.isPending}
                  className="px-6 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 font-semibold shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200"
                >
                  {evaluateMutation.isPending ? '⏳ Evaluating...' : '🔍 Evaluate Answer'}
                </button>
              </div>

              {/* Ground Truth Answer */}
              <div className="bg-white rounded-lg p-4 mb-4 border-2 border-blue-200">
                <p className="text-sm font-semibold text-gray-700 mb-2">Reference Answer:</p>
                <p className="text-sm text-gray-800 whitespace-pre-wrap">{selectedQuestion?.ground_truth_answer}</p>
              </div>

              {/* Evaluation Metrics */}
              {evaluationMetrics && (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  <div className={`p-4 rounded-xl border-2 ${getScoreColor(evaluationMetrics.overall_score)} shadow-sm`}>
                    <p className="text-xs font-semibold mb-1">Overall Score</p>
                    <p className="text-2xl font-bold">
                      {evaluationMetrics.overall_score !== null ? `${Math.round(evaluationMetrics.overall_score * 100)}%` : 'N/A'}
                    </p>
                  </div>

                  <div className={`p-4 rounded-xl border-2 ${getScoreColor(evaluationMetrics.bleu_score)} shadow-sm`}>
                    <p className="text-xs font-semibold mb-1">BLEU Score</p>
                    <p className="text-2xl font-bold">
                      {evaluationMetrics.bleu_score !== null ? `${Math.round(evaluationMetrics.bleu_score * 100)}%` : 'N/A'}
                    </p>
                  </div>

                  <div className={`p-4 rounded-xl border-2 ${getScoreColor(evaluationMetrics.rouge_l_f1)} shadow-sm`}>
                    <p className="text-xs font-semibold mb-1">ROUGE-L</p>
                    <p className="text-2xl font-bold">
                      {evaluationMetrics.rouge_l_f1 !== null ? `${Math.round(evaluationMetrics.rouge_l_f1 * 100)}%` : 'N/A'}
                    </p>
                  </div>

                  <div className={`p-4 rounded-xl border-2 ${getScoreColor(evaluationMetrics.rouge_1_f1)} shadow-sm`}>
                    <p className="text-xs font-semibold mb-1">ROUGE-1</p>
                    <p className="text-2xl font-bold">
                      {evaluationMetrics.rouge_1_f1 !== null ? `${Math.round(evaluationMetrics.rouge_1_f1 * 100)}%` : 'N/A'}
                    </p>
                  </div>

                  <div className={`p-4 rounded-xl border-2 ${getScoreColor(evaluationMetrics.rouge_2_f1)} shadow-sm`}>
                    <p className="text-xs font-semibold mb-1">ROUGE-2</p>
                    <p className="text-2xl font-bold">
                      {evaluationMetrics.rouge_2_f1 !== null ? `${Math.round(evaluationMetrics.rouge_2_f1 * 100)}%` : 'N/A'}
                    </p>
                  </div>

                  <div className={`p-4 rounded-xl border-2 ${getScoreColor(evaluationMetrics.semantic_similarity)} shadow-sm`}>
                    <p className="text-xs font-semibold mb-1">Semantic Sim.</p>
                    <p className="text-2xl font-bold">
                      {evaluationMetrics.semantic_similarity !== null ? `${Math.round(evaluationMetrics.semantic_similarity * 100)}%` : 'N/A'}
                    </p>
                  </div>
                </div>
              )}

              {evaluateMutation.isError && (
                <div className="mt-4 p-4 bg-red-50 border-2 border-red-200 rounded-lg">
                  <p className="text-sm text-red-700 font-semibold">
                    ✗ Evaluation failed. Please try again.
                  </p>
                </div>
              )}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
              {/* Answer Panel */}
              <div className="border border-gray-200 rounded-lg p-4">
                <div className="mb-4">
                  <span className="px-3 py-1 rounded bg-green-100 text-green-800 text-sm font-medium">
                    {Math.round((answerData.confidence_score || 0) * 100)}% Confidence
                  </span>
                </div>

                {isEditing ? (
                  <textarea
                    value={editedText}
                    onChange={(e) => setEditedText(e.target.value)}
                    rows={12}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                ) : (
                  <div className="prose max-w-none">
                    <p className="whitespace-pre-wrap text-gray-800">{answerData.answer_text}</p>
                  </div>
                )}

                <div className="flex gap-2 mt-4">
                  {isEditing ? (
                    <>
                      <button
                        onClick={() => handleReview('edit')}
                        disabled={reviewMutation.isPending}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                      >
                        Save Changes
                      </button>
                      <button
                        onClick={() => setIsEditing(false)}
                        className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => {
                        setIsEditing(true);
                        setEditedText(answerData.answer_text || '');
                      }}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      Improve the answer
                    </button>
                  )}
                </div>
              </div>

              {/* Citations Panel */}
              <div className="border border-gray-200 rounded-lg p-4 max-h-[600px] overflow-y-auto">
                <h4 className="font-medium mb-4 text-gray-900">Source Citations</h4>
                {answerData.citations?.length > 0 ? (
                  <div className="space-y-3">
                    {answerData.citations.map((citation: any, idx: number) => (
                      <div key={citation.citation_id} className="p-3 border border-gray-200 rounded-lg">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="w-6 h-6 flex items-center justify-center bg-blue-100 text-blue-700 rounded text-sm font-medium">
                            {idx + 1}
                          </span>
                          <span className="font-medium text-sm text-gray-900">{citation.document_name}</span>
                        </div>
                        <div className="text-xs text-gray-500">
                          Page {citation.page_number || 'N/A'} • {Math.round((citation.relevance_score || 0) * 100)}% relevant
                        </div>
                        <p className="text-sm mt-2 text-gray-700">{citation.excerpt}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No citations available</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
