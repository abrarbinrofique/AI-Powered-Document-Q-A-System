"""Evaluation service for comparing AI-generated answers with ground truth."""

import logging
from typing import Optional
import re
from app.models.schemas import EvaluationMetrics

logger = logging.getLogger(__name__)


class EvaluationService:
    """Service for evaluating answers against ground truth."""

    def __init__(self):
        """Initialize evaluation service."""
        pass

    def evaluate(self, generated_answer: str, ground_truth: str) -> EvaluationMetrics:
        """Evaluate generated answer against ground truth.

        Calculates multiple metrics:
        - BLEU score (n-gram overlap)
        - ROUGE scores (ROUGE-1, ROUGE-2, ROUGE-L)
        - Semantic similarity (cosine similarity of embeddings)
        - Overall score (weighted average)

        Args:
            generated_answer: AI-generated answer text
            ground_truth: Reference/ground truth answer text

        Returns:
            EvaluationMetrics object with all scores
        """
        try:
            # Clean and normalize texts
            gen_clean = self._normalize_text(generated_answer)
            gt_clean = self._normalize_text(ground_truth)

            # Calculate BLEU score
            bleu_score = self._calculate_bleu(gen_clean, gt_clean)

            # Calculate ROUGE scores
            rouge_scores = self._calculate_rouge(gen_clean, gt_clean)

            # Calculate semantic similarity
            semantic_sim = self._calculate_semantic_similarity(gen_clean, gt_clean)

            # Calculate overall score (weighted average)
            overall_score = self._calculate_overall_score(
                bleu_score,
                rouge_scores,
                semantic_sim
            )

            return EvaluationMetrics(
                bleu_score=round(bleu_score, 4) if bleu_score is not None else None,
                rouge_1_f1=round(rouge_scores.get('rouge1_f1', 0), 4),
                rouge_2_f1=round(rouge_scores.get('rouge2_f1', 0), 4),
                rouge_l_f1=round(rouge_scores.get('rougeL_f1', 0), 4),
                semantic_similarity=round(semantic_sim, 4) if semantic_sim is not None else None,
                overall_score=round(overall_score, 4) if overall_score is not None else None
            )

        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return EvaluationMetrics()

    def _normalize_text(self, text: str) -> str:
        """Normalize text for evaluation.

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        if not text:
            return ""

        # Lowercase
        text = text.lower()

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def _calculate_bleu(self, generated: str, reference: str) -> Optional[float]:
        """Calculate BLEU score.

        Args:
            generated: Generated text
            reference: Reference text

        Returns:
            BLEU score (0-1)
        """
        try:
            from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
            from nltk.tokenize import word_tokenize
            import nltk

            # Download required NLTK data (only once)
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt', quiet=True)

            # Tokenize
            reference_tokens = word_tokenize(reference)
            generated_tokens = word_tokenize(generated)

            if not reference_tokens or not generated_tokens:
                return 0.0

            # Use smoothing to handle edge cases
            smoothing = SmoothingFunction().method1

            # Calculate BLEU with weights for unigrams through 4-grams
            score = sentence_bleu(
                [reference_tokens],
                generated_tokens,
                weights=(0.25, 0.25, 0.25, 0.25),
                smoothing_function=smoothing
            )

            return score

        except Exception as e:
            logger.error(f"BLEU calculation failed: {e}")
            return None

    def _calculate_rouge(self, generated: str, reference: str) -> dict:
        """Calculate ROUGE scores.

        Args:
            generated: Generated text
            reference: Reference text

        Returns:
            Dictionary with ROUGE scores
        """
        try:
            from rouge_score import rouge_scorer

            scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
            scores = scorer.score(reference, generated)

            return {
                'rouge1_f1': scores['rouge1'].fmeasure,
                'rouge2_f1': scores['rouge2'].fmeasure,
                'rougeL_f1': scores['rougeL'].fmeasure
            }

        except Exception as e:
            logger.error(f"ROUGE calculation failed: {e}")
            return {
                'rouge1_f1': 0.0,
                'rouge2_f1': 0.0,
                'rougeL_f1': 0.0
            }

    def _calculate_semantic_similarity(self, generated: str, reference: str) -> Optional[float]:
        """Calculate semantic similarity using embeddings.

        Uses OpenAI embeddings to calculate cosine similarity.

        Args:
            generated: Generated text
            reference: Reference text

        Returns:
            Cosine similarity score (0-1)
        """
        try:
            from openai import OpenAI
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            import os

            # This will use the user's stored API key
            # For now, we'll return None if no API key is available
            # In production, you'd want to fetch the encrypted key from database

            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            if not client.api_key:
                logger.warning("OpenAI API key not available for semantic similarity")
                return None

            # Get embeddings
            gen_response = client.embeddings.create(
                model="text-embedding-3-small",
                input=generated
            )
            ref_response = client.embeddings.create(
                model="text-embedding-3-small",
                input=reference
            )

            gen_embedding = np.array(gen_response.data[0].embedding).reshape(1, -1)
            ref_embedding = np.array(ref_response.data[0].embedding).reshape(1, -1)

            # Calculate cosine similarity
            similarity = cosine_similarity(gen_embedding, ref_embedding)[0][0]

            return float(similarity)

        except Exception as e:
            logger.error(f"Semantic similarity calculation failed: {e}")
            return None

    def _calculate_overall_score(
        self,
        bleu: Optional[float],
        rouge: dict,
        semantic: Optional[float]
    ) -> Optional[float]:
        """Calculate overall score as weighted average.

        Weights:
        - BLEU: 25%
        - ROUGE-L: 25%
        - Semantic similarity: 50%

        Args:
            bleu: BLEU score
            rouge: ROUGE scores dict
            semantic: Semantic similarity score

        Returns:
            Overall score (0-1)
        """
        try:
            scores = []
            weights = []

            if bleu is not None:
                scores.append(bleu)
                weights.append(0.25)

            rouge_l = rouge.get('rougeL_f1', 0)
            if rouge_l is not None:
                scores.append(rouge_l)
                weights.append(0.25)

            if semantic is not None:
                scores.append(semantic)
                weights.append(0.50)

            if not scores:
                return None

            # Normalize weights
            total_weight = sum(weights)
            normalized_weights = [w / total_weight for w in weights]

            # Calculate weighted average
            overall = sum(s * w for s, w in zip(scores, normalized_weights))

            return overall

        except Exception as e:
            logger.error(f"Overall score calculation failed: {e}")
            return None
