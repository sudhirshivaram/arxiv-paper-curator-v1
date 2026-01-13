"""
Helper script to generate evaluation datasets for your RAG system.

This script helps you create evaluation datasets by:
1. Extracting questions from your indexed papers
2. Using LLMs to generate synthetic QA pairs
3. Creating ground truth labels manually or semi-automatically
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import httpx
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class DatasetGenerator:
    """Generate evaluation datasets for RAG benchmarking"""

    def __init__(self, api_base_url: str, llm_api_key: str = None):
        self.api_base_url = api_base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.llm_api_key = llm_api_key or os.getenv("OPENAI_API_KEY")

    async def generate_synthetic_qa_pairs(
        self, num_pairs: int = 10, categories: List[str] = None
    ) -> Dict[str, List]:
        """
        Generate synthetic question-answer pairs from your indexed papers.

        Strategy:
        1. Fetch random papers from your index
        2. Use LLM to generate questions and answers from abstracts/content
        3. Create ground truth labels
        """
        logger.info(f"Generating {num_pairs} synthetic QA pairs...")

        dataset = {
            "questions": [],
            "ground_truths": [],
            "relevant_doc_ids": [],
            "ground_truth_contexts": [],
        }

        # Fetch papers from your index
        papers = await self._fetch_sample_papers(num_pairs, categories)

        for i, paper in enumerate(papers):
            logger.info(f"Processing paper {i+1}/{len(papers)}: {paper['title'][:50]}...")

            # Generate question and answer from paper content
            qa_pair = await self._generate_qa_from_paper(paper)

            if qa_pair:
                dataset["questions"].append(qa_pair["question"])
                dataset["ground_truths"].append(qa_pair["answer"])
                dataset["relevant_doc_ids"].append([paper["arxiv_id"]])
                dataset["ground_truth_contexts"].append([paper["abstract"]])

        return dataset

    async def _fetch_sample_papers(
        self, num_papers: int, categories: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch sample papers from your database or search index"""
        # TODO: Implement this based on your data source
        # This is a placeholder - you can query your PostgreSQL or OpenSearch directly

        logger.info(f"Fetching {num_papers} papers from database...")

        # Example: Query your hybrid search with a broad query to get diverse papers
        queries = [
            "machine learning",
            "neural networks",
            "deep learning",
            "computer vision",
            "natural language processing",
        ]

        papers = []
        for query in queries[: min(len(queries), num_papers)]:
            try:
                response = await self.client.post(
                    f"{self.api_base_url}/hybrid-search/",
                    json={
                        "query": query,
                        "size": max(1, num_papers // len(queries)),
                        "use_hybrid": True,
                        "categories": categories,
                    },
                )
                response.raise_for_status()
                data = response.json()

                for hit in data.get("hits", []):
                    papers.append(
                        {
                            "arxiv_id": hit["arxiv_id"],
                            "title": hit["title"],
                            "abstract": hit["abstract"],
                            "authors": hit.get("authors", []),
                        }
                    )

            except Exception as e:
                logger.warning(f"Failed to fetch papers for query '{query}': {e}")

        return papers[:num_papers]

    async def _generate_qa_from_paper(self, paper: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate a question-answer pair from a paper using LLM.

        Uses OpenAI/Anthropic/Gemini to create realistic questions.
        """
        try:
            # Using OpenAI as example - adjust for your preferred LLM
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.llm_api_key)

            prompt = f"""Based on this research paper, generate ONE specific question that a researcher might ask, along with a detailed answer.

Title: {paper['title']}
Abstract: {paper['abstract']}

Generate a question that:
1. Is specific and answerable from the abstract
2. Would be useful for evaluating a RAG system
3. Requires understanding of the paper's content

Return ONLY valid JSON in this format:
{{
    "question": "Your question here",
    "answer": "Detailed answer here"
}}"""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )

            result = response.choices[0].message.content
            # Parse JSON from response
            qa_pair = json.loads(result)
            return qa_pair

        except Exception as e:
            logger.error(f"Failed to generate QA pair: {e}")
            return None

    def create_manual_template(self, output_path: str, num_questions: int = 10):
        """
        Create a template JSON file for manual annotation.

        Users can fill this in with their own questions and ground truths.
        """
        template = {
            "_instructions": "Fill in your evaluation questions and ground truths below",
            "questions": ["" for _ in range(num_questions)],
            "ground_truths": ["" for _ in range(num_questions)],
            "relevant_doc_ids": [[] for _ in range(num_questions)],
            "ground_truth_contexts": [[] for _ in range(num_questions)],
        }

        with open(output_path, "w") as f:
            json.dump(template, f, indent=2)

        logger.info(f"Template created at {output_path}")
        print(f"\n✅ Template created at {output_path}")
        print("Fill in your questions, answers, and relevant document IDs.")

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate evaluation datasets for RAG benchmarking")
    parser.add_argument(
        "--mode",
        choices=["synthetic", "template"],
        default="synthetic",
        help="Generation mode: synthetic (auto-generate) or template (manual)",
    )
    parser.add_argument("--num-pairs", type=int, default=10, help="Number of QA pairs to generate")
    parser.add_argument("--output", type=str, default="evaluation_dataset.json", help="Output file path")
    parser.add_argument("--api-url", type=str, default="http://localhost:8000", help="Your RAG API base URL")

    args = parser.parse_args()

    generator = DatasetGenerator(api_base_url=args.api_url)

    if args.mode == "template":
        # Create manual template
        output_path = Path(__file__).parent / args.output
        generator.create_manual_template(str(output_path), args.num_pairs)

    else:
        # Generate synthetic dataset
        logger.info("Generating synthetic dataset...")
        dataset = await generator.generate_synthetic_qa_pairs(num_pairs=args.num_pairs)

        output_path = Path(__file__).parent / args.output
        with open(output_path, "w") as f:
            json.dump(dataset, f, indent=2)

        logger.info(f"Dataset saved to {output_path}")
        print(f"\n✅ Generated {len(dataset['questions'])} QA pairs")
        print(f"📁 Saved to: {output_path}")

    await generator.close()


if __name__ == "__main__":
    asyncio.run(main())
