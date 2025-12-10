import json
import re
from pathlib import Path
from typing import Any, Dict, List

from pydantic import ValidationError
from src.schemas.ollama import RAGResponse


class RAGPromptBuilder:
    """Builder class for creating RAG prompts."""

    def __init__(self):
        """Initialize the prompt builder."""
        self.prompts_dir = Path(__file__).parent / "prompts"
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self, document_type: str = "arxiv") -> str:
        """Load the system prompt from the text file.

        Args:
            document_type: Type of documents ("arxiv" or "financial")

        Returns:
            System prompt string
        """
        if document_type == "financial":
            prompt_file = self.prompts_dir / "rag_system_financial.txt"
            if not prompt_file.exists():
                # Fallback to default financial prompt
                return (
                    "You are an AI assistant specialized in answering questions about "
                    "SEC financial filings (10-K, 10-Q reports). Base your answer STRICTLY on "
                    "the provided filing excerpts. Provide factual, data-driven responses."
                )
        else:
            prompt_file = self.prompts_dir / "rag_system.txt"
            if not prompt_file.exists():
                # Fallback to default arXiv prompt
                return (
                    "You are an AI assistant specialized in answering questions about "
                    "academic papers from arXiv. Base your answer STRICTLY on the provided "
                    "paper excerpts."
                )
        return prompt_file.read_text().strip()

    def create_rag_prompt(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        document_type: str = "arxiv"
    ) -> str:
        """Create a RAG prompt with query and retrieved chunks.

        Args:
            query: User's question
            chunks: List of retrieved chunks with metadata from OpenSearch
            document_type: Type of documents ("arxiv" or "financial")

        Returns:
            Formatted prompt string
        """
        system_prompt = self._load_system_prompt(document_type)
        prompt = f"{system_prompt}\n\n"

        if document_type == "financial":
            prompt += "### Context from SEC Filings:\n\n"

            for i, chunk in enumerate(chunks, 1):
                chunk_text = chunk.get("chunk_text", chunk.get("content", ""))
                ticker = chunk.get("ticker", "")
                company_name = chunk.get("company_name", "")
                doc_type = chunk.get("document_type", "")
                filing_date = chunk.get("filing_date", "")

                # Include financial-specific metadata
                prompt += f"[{i}. {ticker} - {company_name} {doc_type} filed {filing_date}]\n"
                prompt += f"{chunk_text}\n\n"

            prompt += f"### Question:\n{query}\n\n"
            prompt += (
                "### Answer:\nProvide a factual, data-driven response citing specific "
                "companies and filing types (e.g., [AAPL 10-K]).\n\n"
            )

        else:  # arxiv
            prompt += "### Context from Papers:\n\n"

            for i, chunk in enumerate(chunks, 1):
                chunk_text = chunk.get("chunk_text", chunk.get("content", ""))
                arxiv_id = chunk.get("arxiv_id", "")

                # Only include minimal metadata - just arxiv_id for citation
                prompt += f"[{i}. arXiv:{arxiv_id}]\n"
                prompt += f"{chunk_text}\n\n"

            prompt += f"### Question:\n{query}\n\n"
            prompt += (
                "### Answer:\nProvide a natural, conversational response (not JSON) "
                "and cite sources using [arXiv:id] format.\n\n"
            )

        return prompt

    def create_structured_prompt(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        document_type: str = "arxiv"
    ) -> Dict[str, Any]:
        """Create a prompt for Ollama with structured output format.

        Args:
            query: User's question
            chunks: List of retrieved chunks
            document_type: Type of documents ("arxiv" or "financial")

        Returns:
            Dictionary with prompt and format schema for Ollama
        """
        prompt_text = self.create_rag_prompt(query, chunks, document_type)

        # Return prompt with Pydantic model schema for structured output
        return {
            "prompt": prompt_text,
            "format": RAGResponse.model_json_schema(),
        }


class ResponseParser:
    """Parser for LLM responses."""

    @staticmethod
    def parse_structured_response(response: str) -> Dict[str, Any]:
        """Parse a structured response from Ollama.

        Args:
            response: Raw LLM response string

        Returns:
            Dictionary with parsed response
        """
        try:
            # Try to parse as JSON and validate with Pydantic
            parsed_json = json.loads(response)
            validated_response = RAGResponse(**parsed_json)
            return validated_response.model_dump()
        except (json.JSONDecodeError, ValidationError):
            # Fallback: try to extract JSON from the response
            return ResponseParser._extract_json_fallback(response)

    @staticmethod
    def _extract_json_fallback(response: str) -> Dict[str, Any]:
        """Extract JSON from response text as fallback.

        Args:
            response: Raw response text

        Returns:
            Dictionary with extracted content or fallback
        """
        # Try to find JSON in the response
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                # Validate with Pydantic, using defaults for missing fields
                validated = RAGResponse(**parsed)
                return validated.model_dump()
            except (json.JSONDecodeError, ValidationError):
                pass

        # Final fallback: return response as plain text
        return {
            "answer": response,
            "sources": [],
            "confidence": "low",
            "citations": [],
        }
