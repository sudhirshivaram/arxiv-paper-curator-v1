"""Google Gemini client for LLM generation."""

import json
import logging
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from src.config import Settings
from src.exceptions import OllamaException  # Reuse for now
from src.services.ollama.prompts import RAGPromptBuilder, ResponseParser

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for interacting with Google Gemini API."""

    def __init__(self, settings: Settings):
        """Initialize Gemini client with settings."""
        self.api_key = settings.gemini_api_key
        self.model_name = settings.gemini_model
        self.max_tokens = settings.gemini_max_tokens

        # Configure Gemini SDK
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

        self.prompt_builder = RAGPromptBuilder()
        self.response_parser = ResponseParser()
        logger.info(f"Gemini client initialized with model: {self.model_name}")

    async def health_check(self) -> Dict[str, Any]:
        """
        Check if Gemini API is accessible.

        Returns:
            Dictionary with health status information
        """
        try:
            # Try a simple generation as health check
            response = self.model.generate_content("Hello")
            return {
                "status": "healthy",
                "message": "Gemini API is accessible",
                "model": self.model_name,
            }
        except Exception as e:
            logger.error(f"Gemini health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Gemini API error: {str(e)}",
            }

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models (stub for compatibility).

        Returns:
            List with configured model
        """
        return [{"name": self.model_name}]

    async def generate(self, model: str, prompt: str, stream: bool = False, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Generate text using Gemini API.

        Args:
            model: Model name to use (uses configured model if not specified)
            prompt: Input prompt for generation
            stream: Whether to stream response (not implemented for non-streaming)
            **kwargs: Additional generation parameters (temperature, top_p, etc.)

        Returns:
            Response dictionary compatible with Ollama format
        """
        try:
            # Extract Gemini-compatible parameters
            temperature = kwargs.get("temperature", 0.7)
            top_p = kwargs.get("top_p", 0.9)

            logger.info(f"Sending request to Gemini: model={self.model_name}, temperature={temperature}")

            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=self.max_tokens,
            )

            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )

            # Convert to Ollama-compatible format
            return {
                "model": self.model_name,
                "response": response.text,
                "done": True,
                "context": [],
                "total_duration": 0,
                "load_duration": 0,
                "prompt_eval_count": 0,  # Gemini doesn't provide token counts in free tier
                "eval_count": 0,
            }

        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise OllamaException(f"Error generating with Gemini: {e}")

    async def generate_stream(self, model: str, prompt: str, **kwargs):
        """
        Generate text with streaming response.

        Args:
            model: Model name to use
            prompt: Input prompt for generation
            **kwargs: Additional generation parameters

        Yields:
            JSON chunks in Ollama-compatible format
        """
        try:
            temperature = kwargs.get("temperature", 0.7)
            top_p = kwargs.get("top_p", 0.9)

            logger.info(f"Starting streaming generation with Gemini: model={self.model_name}")

            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=self.max_tokens,
            )

            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                stream=True
            )

            for chunk in response:
                if chunk.text:
                    # Convert to Ollama-compatible format
                    yield {
                        "model": self.model_name,
                        "response": chunk.text,
                        "done": False,
                    }

            # Final chunk
            yield {
                "model": self.model_name,
                "response": "",
                "done": True,
            }

        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            raise OllamaException(f"Error in streaming generation: {e}")

    async def generate_rag_answer(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        model: str = "gemini-1.5-flash",
        use_structured_output: bool = False,
        document_type: str = "arxiv",
    ) -> Dict[str, Any]:
        """
        Generate a RAG answer using retrieved chunks.

        Args:
            query: User's question
            chunks: Retrieved document chunks with metadata
            model: Model to use for generation
            use_structured_output: Whether to use structured output (not implemented)
            document_type: Type of documents (arxiv or financial)

        Returns:
            Dictionary with answer, sources, confidence, and citations
        """
        try:
            # Use the same prompt builder as Ollama/OpenAI
            prompt = self.prompt_builder.create_rag_prompt(query, chunks, document_type)

            logger.info(f"Generating RAG answer with Gemini model: {self.model_name}")

            generation_config = genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.9,
                max_output_tokens=self.max_tokens,
            )

            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )

            answer_text = response.text

            # Build response structure for financial documents
            if document_type == "financial":
                sources = []
                seen_urls = set()
                for chunk in chunks:
                    source_url = chunk.get("source_url")
                    if source_url and source_url not in seen_urls:
                        sources.append(source_url)
                        seen_urls.add(source_url)

                citations = []
                for chunk in chunks:
                    company = chunk.get("company_name", "")
                    filing = chunk.get("filing_type", "")
                    if company and filing:
                        citation = f"{company} {filing}"
                        if citation not in citations:
                            citations.append(citation)
            else:
                # Build response structure for arXiv papers
                sources = []
                seen_urls = set()
                for chunk in chunks:
                    arxiv_id = chunk.get("arxiv_id")
                    if arxiv_id:
                        arxiv_id_clean = arxiv_id.split("v")[0] if "v" in arxiv_id else arxiv_id
                        pdf_url = f"https://arxiv.org/pdf/{arxiv_id_clean}.pdf"
                        if pdf_url not in seen_urls:
                            sources.append(pdf_url)
                            seen_urls.add(pdf_url)

                citations = list(set(chunk.get("arxiv_id") for chunk in chunks if chunk.get("arxiv_id")))

            return {
                "answer": answer_text,
                "sources": sources,
                "confidence": "medium",
                "citations": citations[:5],
                "model_used": self.model_name,
                "tokens_used": {
                    "prompt": 0,  # Gemini free tier doesn't provide token counts
                    "completion": 0,
                    "total": 0,
                },
            }

        except Exception as e:
            logger.error(f"Error generating RAG answer with Gemini: {e}")
            raise OllamaException(f"RAG generation failed: {e}")

    async def generate_rag_answer_stream(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        model: str = "gemini-1.5-flash",
        document_type: str = "arxiv",
    ):
        """
        Generate a streaming RAG answer using retrieved chunks.

        Args:
            query: User's question
            chunks: Retrieved document chunks with metadata
            model: Model to use for generation
            document_type: Type of documents (arxiv or financial)

        Yields:
            Streaming response chunks with partial answers
        """
        try:
            # Create prompt for streaming
            prompt = self.prompt_builder.create_rag_prompt(query, chunks, document_type)

            # Stream the response
            async for chunk in self.generate_stream(
                model=model,
                prompt=prompt,
                temperature=0.7,
                top_p=0.9,
            ):
                yield chunk

        except Exception as e:
            logger.error(f"Error generating streaming RAG answer with Gemini: {e}")
            raise OllamaException(f"Failed to generate streaming RAG answer: {e}")
