"""
Benchmark script for Financial Documents RAG.
Uses the /ask endpoint with document_type: "financial"
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from datetime import datetime

import httpx
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
from benchmarks.rag_evaluator import RAGEvaluator, RAGResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "https://arxiv-paper-curator-v1-production.up.railway.app/api/v1")


class FinancialRAGWrapper:
    """Wrapper for Financial RAG API"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=120.0)

    async def query(self, question: str, ticker: str = None) -> RAGResponse:
        """Query /ask endpoint with document_type: financial"""
        start_time = time.time()

        try:
            payload = {
                "query": question,
                "document_type": "financial",
                "top_k": 5,
                "use_hybrid": True
            }
            if ticker:
                payload["ticker"] = ticker

            response = await self.client.post(
                f"{self.base_url}/ask",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            latency_ms = (time.time() - start_time) * 1000

            return RAGResponse(
                answer=data.get("answer", ""),
                contexts=data.get("context_chunks", [])[:3],
                source_documents=data.get("sources", []),
                latency_ms=latency_ms,
                tokens_used=data.get("tokens_used", 0),
                model_used=data.get("model_used", "unknown"),
            )

        except Exception as e:
            logger.error(f"Error querying Financial RAG: {e}")
            raise

    async def close(self):
        await self.client.aclose()


async def run_financial_benchmark():
    """Run benchmark on financial documents"""

    # Load dataset
    dataset_path = Path(__file__).parent / "data" / "financial_dataset.json"
    with open(dataset_path) as f:
        dataset = json.load(f)

    questions = dataset["questions"]
    ground_truths = dataset["ground_truths"]
    tickers = dataset.get("tickers", [None] * len(questions))

    logger.info(f"Running benchmark on {len(questions)} financial questions...")

    # Initialize
    rag = FinancialRAGWrapper(API_BASE_URL)
    evaluator = RAGEvaluator(rag_pipeline=rag.query)

    responses = []
    all_contexts = []

    # Run queries
    for i, (question, ticker) in enumerate(zip(questions, tickers)):
        logger.info(f"[{i+1}/{len(questions)}] Querying: {question[:50]}...")
        try:
            response = await rag.query(question, ticker)
            responses.append(response)
            all_contexts.append(response.contexts)
            logger.info(f"  ✓ Got answer ({response.latency_ms:.0f}ms)")
        except Exception as e:
            logger.error(f"  ✗ Failed: {e}")
            responses.append(RAGResponse(
                answer="Error",
                contexts=[],
                source_documents=[],
                latency_ms=0,
                tokens_used=0,
                model_used="error"
            ))
            all_contexts.append([])

    await rag.close()

    # Calculate RAGAS metrics (now that API returns context_chunks)
    logger.info("Calculating RAGAS metrics...")
    valid_indices = [i for i, r in enumerate(responses) if r.answer != "Error" and r.contexts]

    if valid_indices:
        valid_questions = [questions[i] for i in valid_indices]
        valid_responses = [responses[i] for i in valid_indices]
        valid_ground_truths = [ground_truths[i] for i in valid_indices]

        try:
            ragas_scores = await evaluator._calculate_ragas_scores(
                questions=valid_questions,
                responses=valid_responses,
                ground_truths=valid_ground_truths,
                ground_truth_contexts=None
            )
            ragas_scores["successful_queries"] = len(valid_indices)
            ragas_scores["total_queries"] = len(questions)
        except Exception as e:
            logger.error(f"RAGAS scoring failed: {e}")
            ragas_scores = {
                "error": str(e),
                "successful_queries": len(valid_indices),
                "total_queries": len(questions)
            }
    else:
        ragas_scores = {
            "note": "No valid responses with contexts",
            "successful_queries": 0,
            "total_queries": len(questions)
        }

    # Calculate latency metrics
    latencies = [r.latency_ms for r in responses if r.latency_ms > 0]
    latency_metrics = evaluator._calculate_latency_metrics(latencies) if latencies else {}

    # Simple retrieval metrics
    retrieval_metrics = {"note": "Retrieval metrics require relevant doc IDs"}

    # Compile results
    results = {
        "benchmark_type": "financial",
        "timestamp": datetime.now().isoformat(),
        "num_questions": len(questions),
        "ragas_scores": ragas_scores,
        "retrieval_metrics": retrieval_metrics,
        "latency_metrics": latency_metrics,
        "companies_tested": list(set(tickers)),
    }

    # Save results
    output_path = Path(__file__).parent / "results" / f"financial_benchmark_{int(time.time())}.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Print summary
    print("\n" + "=" * 60)
    print("FINANCIAL RAG BENCHMARK RESULTS")
    print("=" * 60)
    print(f"\nQuestions: {len(questions)}")
    print(f"Companies: {', '.join(set(tickers))}")
    print(f"\nRAGAS Scores:")
    for key, value in ragas_scores.items():
        if isinstance(value, (int, float)):
            print(f"  {key}: {value:.3f}")
    print(f"\nLatency:")
    print(f"  Avg: {latency_metrics.get('avg', 0):.0f}ms")
    print(f"  P50: {latency_metrics.get('p50', 0):.0f}ms")
    print(f"  P95: {latency_metrics.get('p95', 0):.0f}ms")
    print(f"\nResults saved to: {output_path}")

    return results


if __name__ == "__main__":
    asyncio.run(run_financial_benchmark())
