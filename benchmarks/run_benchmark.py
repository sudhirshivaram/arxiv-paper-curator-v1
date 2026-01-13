"""
Example script to run benchmarks on your RAG system.

This script demonstrates how to:
1. Load your evaluation dataset
2. Run the RAG pipeline
3. Generate comprehensive metrics
4. Export results
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import List

import httpx
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.rag_evaluator import RAGEvaluator, RAGResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
COST_PER_1K_TOKENS = float(os.getenv("COST_PER_1K_TOKENS", "0.0015"))


class RAGPipelineWrapper:
    """Wrapper for your RAG system API"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=60.0)

    async def query(self, question: str, use_hybrid: bool = True, top_k: int = 5) -> RAGResponse:
        """Query the live /hybrid-search endpoint and build contexts for RAGAS."""
        start_time = time.time()

        try:
            response = await self.client.post(
                f"{self.base_url}/hybrid-search/",
                json={
                    "query": question,
                    "size": top_k,
                    "use_hybrid": use_hybrid,
                },
            )
            response.raise_for_status()
            data = response.json()

            latency_ms = (time.time() - start_time) * 1000

            hits = data.get("hits", [])
            contexts = [h.get("chunk_text", "") for h in hits if h.get("chunk_text")]
            source_documents = []
            for h in hits:
                source_documents.append(
                    {
                        "arxiv_id": h.get("arxiv_id"),
                        "title": h.get("title"),
                        "pdf_url": h.get("pdf_url"),
                        "chunk_id": h.get("chunk_id"),
                        "section_name": h.get("section_name"),
                    }
                )

            # If the endpoint does not generate an answer, create a simple extractive one
            answer = self._generate_answer(question, contexts)

            tokens_used = len(question + answer + " ".join(contexts)) // 4

            return RAGResponse(
                answer=answer,
                contexts=contexts[:3],  # limit contexts to keep scoring stable
                source_documents=source_documents,
                latency_ms=latency_ms,
                tokens_used=tokens_used,
                model_used=data.get("search_mode", "hybrid" if use_hybrid else "bm25"),
            )

        except Exception as e:
            logger.error(f"Error querying RAG system: {e}")
            raise

    def _generate_answer(self, question: str, contexts: List[str]) -> str:
        """
        Generate answer from contexts.

        TODO: Replace with your actual LLM generation logic.
        If you have an /ask endpoint with LLM generation, use that instead.
        """
        # Simple extractive approach for now
        return contexts[0][:500] if contexts else "No answer available"

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


async def load_evaluation_dataset(dataset_path: str) -> dict:
    """
    Load evaluation dataset from JSON file.

    Expected format:
    {
        "questions": ["What is...", "How does..."],
        "ground_truths": ["The answer is...", "It works by..."],
        "relevant_doc_ids": [["arxiv_id_1", "arxiv_id_2"], ["arxiv_id_3"]],
        "ground_truth_contexts": [["context 1"], ["context 2"]]  // Optional
    }
    """
    with open(dataset_path, "r") as f:
        return json.load(f)


async def main():
    """Run complete benchmark evaluation"""
    logger.info("Starting RAG System Benchmark")
    logger.info(f"API Base URL: {API_BASE_URL}")

    # Initialize RAG pipeline wrapper
    rag_pipeline = RAGPipelineWrapper(API_BASE_URL)

    # Load evaluation dataset
    dataset_path = Path(__file__).parent / "evaluation_dataset.json"
    if not dataset_path.exists():
        logger.error(f"Dataset not found at {dataset_path}")
        logger.info("Please create an evaluation dataset first. See sample_dataset.json for format.")
        return

    dataset = await load_evaluation_dataset(str(dataset_path))

    # Initialize evaluator
    evaluator = RAGEvaluator(
        rag_pipeline=rag_pipeline.query, cost_per_1k_tokens=COST_PER_1K_TOKENS
    )

    # Run evaluation
    logger.info(f"Evaluating {len(dataset['questions'])} questions...")
    results = await evaluator.evaluate(
        questions=dataset["questions"],
        ground_truths=dataset["ground_truths"],
        ground_truth_contexts=dataset.get("ground_truth_contexts"),
        relevant_doc_ids=dataset.get("relevant_doc_ids"),
    )

    # Print report
    evaluator.print_report(results)

    # Export results
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"benchmark_results_{int(time.time())}.json"
    evaluator.export_results(results, str(output_path))

    # Close connections
    await rag_pipeline.close()

    logger.info(f"Benchmark completed! Results saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
