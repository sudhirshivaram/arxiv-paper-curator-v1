"""
Comprehensive RAG System Evaluator

Evaluates RAG systems using multiple metrics:
- RAGAS scores (0-1 scale)
- MRR (Mean Reciprocal Rank)
- Hit Rate@k
- Latency measurements
- Token cost analysis
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    """Response from RAG system"""

    answer: str
    contexts: List[str]
    source_documents: List[Dict[str, Any]]
    latency_ms: float
    tokens_used: int
    model_used: str


@dataclass
class EvaluationResult:
    """Complete evaluation results"""

    # RAGAS scores (0-1 scale)
    ragas_scores: Dict[str, float]

    # Ranking metrics
    mrr: float  # Mean Reciprocal Rank
    hit_rate_at_1: float
    hit_rate_at_3: float
    hit_rate_at_5: float
    hit_rate_at_10: float

    # Performance metrics
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float

    # Cost metrics
    total_tokens: int
    avg_tokens_per_query: float
    estimated_cost_usd: float

    # Sample details
    num_samples: int
    failed_queries: int


class RAGEvaluator:
    """
    Comprehensive RAG system evaluator.

    Usage:
        evaluator = RAGEvaluator(rag_pipeline=your_rag_function)
        results = await evaluator.evaluate(evaluation_dataset)
        evaluator.print_report(results)
    """

    def __init__(
        self,
        rag_pipeline: callable,
        cost_per_1k_tokens: float = 0.0015,  # Default: ~GPT-3.5-turbo pricing
    ):
        """
        Initialize evaluator.

        Args:
            rag_pipeline: Async function that takes a query and returns RAGResponse
            cost_per_1k_tokens: Cost per 1000 tokens for cost estimation
        """
        self.rag_pipeline = rag_pipeline
        self.cost_per_1k_tokens = cost_per_1k_tokens

    async def evaluate(
        self,
        questions: List[str],
        ground_truths: List[str],
        ground_truth_contexts: Optional[List[List[str]]] = None,
        relevant_doc_ids: Optional[List[List[str]]] = None,
    ) -> EvaluationResult:
        """
        Run comprehensive evaluation.

        Args:
            questions: List of questions to evaluate
            ground_truths: List of ground truth answers
            ground_truth_contexts: Optional ground truth contexts for each question
            relevant_doc_ids: Optional list of relevant document IDs for ranking metrics

        Returns:
            EvaluationResult with all metrics
        """
        logger.info(f"Starting evaluation with {len(questions)} questions")

        # Run RAG pipeline on all questions
        responses: List[RAGResponse] = []
        latencies: List[float] = []
        failed_count = 0

        for i, question in enumerate(questions):
            try:
                logger.info(f"Processing question {i+1}/{len(questions)}: {question[:50]}...")
                response = await self.rag_pipeline(question)
                responses.append(response)
                latencies.append(response.latency_ms)
            except Exception as e:
                logger.error(f"Failed to process question {i+1}: {e}")
                failed_count += 1
                # Add placeholder response
                responses.append(
                    RAGResponse(
                        answer="",
                        contexts=[],
                        source_documents=[],
                        latency_ms=0,
                        tokens_used=0,
                        model_used="",
                    )
                )

        # Calculate RAGAS scores
        ragas_scores = await self._calculate_ragas_scores(questions, responses, ground_truths, ground_truth_contexts)

        # Calculate ranking metrics (MRR, Hit Rate@k)
        ranking_metrics = self._calculate_ranking_metrics(responses, relevant_doc_ids) if relevant_doc_ids else {}

        # Calculate latency metrics
        latencies = [r.latency_ms for r in responses if r.latency_ms > 0]
        latency_metrics = self._calculate_latency_metrics(latencies)

        # Calculate cost metrics
        cost_metrics = self._calculate_cost_metrics(responses)

        result = EvaluationResult(
            ragas_scores=ragas_scores,
            mrr=ranking_metrics.get("mrr", 0.0),
            hit_rate_at_1=ranking_metrics.get("hit_rate@1", 0.0),
            hit_rate_at_3=ranking_metrics.get("hit_rate@3", 0.0),
            hit_rate_at_5=ranking_metrics.get("hit_rate@5", 0.0),
            hit_rate_at_10=ranking_metrics.get("hit_rate@10", 0.0),
            avg_latency_ms=latency_metrics["avg"],
            p50_latency_ms=latency_metrics["p50"],
            p95_latency_ms=latency_metrics["p95"],
            p99_latency_ms=latency_metrics["p99"],
            total_tokens=cost_metrics["total_tokens"],
            avg_tokens_per_query=cost_metrics["avg_tokens"],
            estimated_cost_usd=cost_metrics["cost_usd"],
            num_samples=len(questions),
            failed_queries=failed_count,
        )

        logger.info("Evaluation completed!")
        return result

    async def _calculate_ragas_scores(
        self,
        questions: List[str],
        responses: List[RAGResponse],
        ground_truths: List[str],
        ground_truth_contexts: Optional[List[List[str]]],
    ) -> Dict[str, float]:
        """Calculate RAGAS scores using the RAGAS library"""
        logger.info("Calculating RAGAS scores...")

        # Prepare data for RAGAS
        data = {
            "question": questions,
            "answer": [r.answer for r in responses],
            "contexts": [r.contexts for r in responses],
            "ground_truth": ground_truths,
        }

        # If ground truth contexts provided, add them
        if ground_truth_contexts:
            data["ground_truth_contexts"] = ground_truth_contexts

        dataset = Dataset.from_dict(data)

        # Configure explicit LLM and embeddings to avoid missing embed_query errors
        provider = os.getenv("RAGAS_LLM_PROVIDER", "openai").lower()
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY", "")

        llm = None
        embeddings = None

        gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        if provider == "gemini" and gemini_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

                llm = ChatGoogleGenerativeAI(
                    model=gemini_model,
                    temperature=0,
                    api_key=gemini_key,
                )
                embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/embedding-001",
                    api_key=gemini_key,
                )
                logger.info("Using Gemini for RAGAS scoring")
            except Exception as e:
                logger.warning(f"Gemini not available for RAGAS, falling back to OpenAI: {e}")

        if llm is None or embeddings is None:
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=openai_key)
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=openai_key)
            logger.info("Using OpenAI for RAGAS scoring")

        # Run RAGAS evaluation
        try:
            result = evaluate(
                dataset,
                metrics=[
                    faithfulness,
                    answer_relevancy,
                    context_precision,
                    context_recall,
                ],
                llm=llm,
                embeddings=embeddings,
            )

            # Debug: Log what RAGAS actually returns
            logger.info(f"RAGAS result type: {type(result)}")
            logger.info(f"RAGAS result dir: {[x for x in dir(result) if not x.startswith('_')]}")

            # Handle different RAGAS return formats
            result_dict = {}

            # Case 1: EvaluationResult object (RAGAS v0.2+) with to_pandas() method
            if hasattr(result, 'to_pandas'):
                # Convert to pandas DataFrame
                df = result.to_pandas()
                logger.info(f"DataFrame shape: {df.shape}, columns: {list(df.columns)}")
                # Average each metric across all samples
                for key in ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']:
                    if key in df.columns:
                        values = df[key].dropna()  # Remove NaN values
                        result_dict[key] = float(values.mean()) if len(values) > 0 else 0.0
                        logger.info(f"Extracted {key}: {result_dict[key]}")
            # Case 2: Has 'scores' DataFrame attribute
            elif hasattr(result, 'scores') and hasattr(result.scores, 'to_dict'):
                df_dict = result.scores.to_dict()
                logger.info(f"DataFrame columns: {list(df_dict.keys())}")
                for key in ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']:
                    if key in df_dict:
                        values = [v for v in df_dict[key].values() if v is not None]
                        result_dict[key] = sum(values) / len(values) if values else 0.0
            # Case 3: Direct DataFrame with to_dict
            elif hasattr(result, 'to_dict'):
                df_dict = result.to_dict()
                for key in ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']:
                    if key in df_dict:
                        values = [v for v in df_dict[key].values() if v is not None]
                        result_dict[key] = sum(values) / len(values) if values else 0.0
            # Case 4: Dict
            elif isinstance(result, dict):
                result_dict = result
            else:
                logger.warning(f"Unexpected RAGAS result format: {type(result)}")
                result_dict = {}

            logger.info(f"Final result_dict: {result_dict}")

            # Safely extract scores with defaults (use _score suffix to avoid conflict with imported metrics)
            faithfulness_score = float(result_dict.get("faithfulness", 0.0)) if result_dict else 0.0
            relevancy_score = float(result_dict.get("answer_relevancy", 0.0)) if result_dict else 0.0
            precision_score = float(result_dict.get("context_precision", 0.0)) if result_dict else 0.0
            recall_score = float(result_dict.get("context_recall", 0.0)) if result_dict else 0.0

            # Calculate overall RAGAS score as average of all metrics
            overall_score = (faithfulness_score + relevancy_score + precision_score + recall_score) / 4.0

            return {
                "faithfulness": faithfulness_score,
                "answer_relevancy": relevancy_score,
                "context_precision": precision_score,
                "context_recall": recall_score,
                "ragas_score": overall_score,
            }
        except Exception as e:
            logger.error(f"RAGAS evaluation failed: {e}")
            return {
                "faithfulness": 0.0,
                "answer_relevancy": 0.0,
                "context_precision": 0.0,
                "context_recall": 0.0,
                "ragas_score": 0.0,
            }

    def _calculate_ranking_metrics(
        self, responses: List[RAGResponse], relevant_doc_ids: List[List[str]]
    ) -> Dict[str, float]:
        """
        Calculate MRR and Hit Rate@k.

        Args:
            responses: List of RAG responses
            relevant_doc_ids: List of relevant document IDs for each query

        Returns:
            Dict with mrr, hit_rate@1, hit_rate@3, hit_rate@5, hit_rate@10
        """
        logger.info("Calculating ranking metrics (MRR, Hit Rate@k)...")

        reciprocal_ranks = []
        hits_at_1 = 0
        hits_at_3 = 0
        hits_at_5 = 0
        hits_at_10 = 0

        for response, relevant_ids in zip(responses, relevant_doc_ids):
            # Extract document IDs from retrieved documents
            retrieved_ids = [doc.get("arxiv_id", doc.get("id", "")) for doc in response.source_documents]

            # Find rank of first relevant document
            first_relevant_rank = None
            for rank, doc_id in enumerate(retrieved_ids, start=1):
                if doc_id in relevant_ids:
                    first_relevant_rank = rank
                    break

            # MRR calculation
            if first_relevant_rank:
                reciprocal_ranks.append(1.0 / first_relevant_rank)
            else:
                reciprocal_ranks.append(0.0)

            # Hit Rate@k calculation
            if any(doc_id in relevant_ids for doc_id in retrieved_ids[:1]):
                hits_at_1 += 1
            if any(doc_id in relevant_ids for doc_id in retrieved_ids[:3]):
                hits_at_3 += 1
            if any(doc_id in relevant_ids for doc_id in retrieved_ids[:5]):
                hits_at_5 += 1
            if any(doc_id in relevant_ids for doc_id in retrieved_ids[:10]):
                hits_at_10 += 1

        n = len(responses)
        return {
            "mrr": sum(reciprocal_ranks) / n if n > 0 else 0.0,
            "hit_rate@1": hits_at_1 / n if n > 0 else 0.0,
            "hit_rate@3": hits_at_3 / n if n > 0 else 0.0,
            "hit_rate@5": hits_at_5 / n if n > 0 else 0.0,
            "hit_rate@10": hits_at_10 / n if n > 0 else 0.0,
        }

    def _calculate_latency_metrics(self, latencies: List[float]) -> Dict[str, float]:
        """Calculate latency percentiles"""
        if not latencies:
            return {"avg": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0}

        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)

        return {
            "avg": sum(latencies) / n,
            "p50": sorted_latencies[int(n * 0.50)],
            "p95": sorted_latencies[int(n * 0.95)],
            "p99": sorted_latencies[int(n * 0.99)] if n > 1 else sorted_latencies[-1],
        }

    def _calculate_cost_metrics(self, responses: List[RAGResponse]) -> Dict[str, Any]:
        """Calculate token usage and cost"""
        total_tokens = sum(r.tokens_used for r in responses)
        n = len(responses)

        return {
            "total_tokens": total_tokens,
            "avg_tokens": total_tokens / n if n > 0 else 0,
            "cost_usd": (total_tokens / 1000) * self.cost_per_1k_tokens,
        }

    def print_report(self, result: EvaluationResult):
        """Print formatted evaluation report"""
        print("\n" + "=" * 80)
        print("RAG SYSTEM EVALUATION REPORT".center(80))
        print("=" * 80)

        print(f"\n📊 EVALUATION SUMMARY")
        print(f"   Samples evaluated: {result.num_samples}")
        print(f"   Failed queries: {result.failed_queries}")

        print(f"\n✅ RAGAS SCORES (0-1 scale, higher is better)")
        print(f"   Overall RAGAS Score:    {result.ragas_scores.get('ragas_score', 0.0):.3f}")
        print(f"   Faithfulness:           {result.ragas_scores['faithfulness']:.3f}")
        print(f"   Answer Relevancy:       {result.ragas_scores['answer_relevancy']:.3f}")
        print(f"   Context Precision:      {result.ragas_scores['context_precision']:.3f}")
        print(f"   Context Recall:         {result.ragas_scores['context_recall']:.3f}")

        print(f"\n🎯 RANKING METRICS")
        print(f"   MRR (Mean Reciprocal Rank): {result.mrr:.3f}")
        print(f"   Hit Rate@1:                 {result.hit_rate_at_1:.1%}")
        print(f"   Hit Rate@3:                 {result.hit_rate_at_3:.1%}")
        print(f"   Hit Rate@5:                 {result.hit_rate_at_5:.1%}")
        print(f"   Hit Rate@10:                {result.hit_rate_at_10:.1%}")

        print(f"\n⚡ LATENCY METRICS (milliseconds)")
        print(f"   Average:       {result.avg_latency_ms:.1f} ms")
        print(f"   P50 (median):  {result.p50_latency_ms:.1f} ms")
        print(f"   P95:           {result.p95_latency_ms:.1f} ms")
        print(f"   P99:           {result.p99_latency_ms:.1f} ms")

        print(f"\n💰 COST METRICS")
        print(f"   Total tokens:           {result.total_tokens:,}")
        print(f"   Avg tokens per query:   {result.avg_tokens_per_query:.1f}")
        print(f"   Estimated cost:         ${result.estimated_cost_usd:.4f}")
        print(f"   Cost per query:         ${result.estimated_cost_usd/result.num_samples:.6f}")

        print("\n" + "=" * 80 + "\n")

    def export_results(self, result: EvaluationResult, output_path: str):
        """Export results to JSON file"""
        import json

        data = {
            "summary": {
                "num_samples": result.num_samples,
                "failed_queries": result.failed_queries,
            },
            "ragas_scores": result.ragas_scores,
            "ranking_metrics": {
                "mrr": result.mrr,
                "hit_rate@1": result.hit_rate_at_1,
                "hit_rate@3": result.hit_rate_at_3,
                "hit_rate@5": result.hit_rate_at_5,
                "hit_rate@10": result.hit_rate_at_10,
            },
            "latency_metrics": {
                "avg_ms": result.avg_latency_ms,
                "p50_ms": result.p50_latency_ms,
                "p95_ms": result.p95_latency_ms,
                "p99_ms": result.p99_latency_ms,
            },
            "cost_metrics": {
                "total_tokens": result.total_tokens,
                "avg_tokens_per_query": result.avg_tokens_per_query,
                "estimated_cost_usd": result.estimated_cost_usd,
            },
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Results exported to {output_path}")
