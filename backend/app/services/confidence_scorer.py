from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class ConfidenceScorer:
    """Service for calculating multi-metric confidence scores for answers."""

    async def calculate_confidence(
        self,
        retrieval_results: List[Dict],
        answer: str,
        question: str,
        api_key: str
    ) -> Dict[str, float]:
        """Calculate multi-metric confidence score.

        Args:
            retrieval_results: List of retrieved chunks
            answer: Generated answer text
            question: Original question
            api_key: OpenAI API key (decrypted)

        Returns:
            Dictionary with confidence metrics
        """
        try:
            import numpy as np

            # 1. Retrieval confidence (average similarity score)
            scores = [r.get("score", 0.0) for r in retrieval_results]
            retrieval_conf = float(np.mean(scores)) if scores else 0.0

            # 2. Coverage score (percentage of high-relevance chunks)
            high_relevance = sum(1 for s in scores if s > 0.7)
            coverage = high_relevance / max(len(scores), 1)

            # 3. Faithfulness score (LLM-verified grounding)
            faithfulness = await self._check_faithfulness(
                answer,
                [r["text"] for r in retrieval_results],
                api_key
            )

            # 4. Relevancy score (answer addresses question)
            relevancy = await self._check_relevancy(answer, question, api_key)

            # Weighted composite score
            weights = {
                "retrieval": 0.25,
                "coverage": 0.15,
                "faithfulness": 0.35,
                "relevancy": 0.25
            }

            composite = (
                weights["retrieval"] * retrieval_conf +
                weights["coverage"] * coverage +
                weights["faithfulness"] * faithfulness +
                weights["relevancy"] * relevancy
            )

            metrics = {
                "overall": round(composite, 3),
                "retrieval": round(retrieval_conf, 3),
                "coverage": round(coverage, 3),
                "faithfulness": round(faithfulness, 3),
                "relevancy": round(relevancy, 3)
            }

            logger.info(f"Calculated confidence scores: {metrics}")
            return metrics
        except Exception as e:
            logger.error(f"Failed to calculate confidence: {e}")
            # Return default scores on error
            return {
                "overall": 0.5,
                "retrieval": 0.5,
                "coverage": 0.5,
                "faithfulness": 0.5,
                "relevancy": 0.5
            }

    async def _check_faithfulness(self, answer: str, contexts: List[str], api_key: str) -> float:
        """Use LLM to verify answer grounding in context.

        Args:
            answer: Generated answer
            contexts: Context chunks
            api_key: OpenAI API key

        Returns:
            Faithfulness score (0.0 to 1.0)
        """
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            context_text = "\n---\n".join(contexts)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "system",
                    "content": """Score answer faithfulness from 0.0 to 1.0.
                    1.0 = Fully supported by context
                    0.5 = Partially supported
                    0.0 = Unsupported claims
                    Return only the numeric score."""
                }, {
                    "role": "user",
                    "content": f"Context:\n{context_text}\n\nAnswer:\n{answer}"
                }],
                temperature=0
            )

            try:
                score = float(response.choices[0].message.content.strip())
                return min(max(score, 0.0), 1.0)  # Clamp to [0, 1]
            except:
                return 0.5
        except Exception as e:
            logger.error(f"Faithfulness check failed: {e}")
            return 0.5

    async def _check_relevancy(self, answer: str, question: str, api_key: str) -> float:
        """Check if answer addresses the question.

        Args:
            answer: Generated answer
            question: Original question
            api_key: OpenAI API key

        Returns:
            Relevancy score (0.0 to 1.0)
        """
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "system",
                    "content": """Score answer relevancy from 0.0 to 1.0.
                    1.0 = Directly answers question
                    0.5 = Partially relevant
                    0.0 = Not relevant
                    Return only the numeric score."""
                }, {
                    "role": "user",
                    "content": f"Question:\n{question}\n\nAnswer:\n{answer}"
                }],
                temperature=0
            )

            try:
                score = float(response.choices[0].message.content.strip())
                return min(max(score, 0.0), 1.0)  # Clamp to [0, 1]
            except:
                return 0.5
        except Exception as e:
            logger.error(f"Relevancy check failed: {e}")
            return 0.5
