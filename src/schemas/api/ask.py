from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """Request model for RAG question answering."""

    query: str = Field(..., description="User's question", min_length=1, max_length=1000)
    top_k: int = Field(3, description="Number of top chunks to retrieve", ge=1, le=10)
    use_hybrid: bool = Field(True, description="Use hybrid search (BM25 + vector)")
    model: str = Field("qwen2.5:7b", description="Ollama model to use for generation")
    categories: Optional[List[str]] = Field(None, description="Filter by arXiv categories")
    document_type: Literal["arxiv", "financial"] = Field(
        "arxiv",
        description="Type of documents to search: 'arxiv' for papers or 'financial' for SEC filings"
    )
    ticker: Optional[str] = Field(
        None,
        description="Filter financial documents by ticker symbol (e.g., 'AAPL', 'MSFT')"
    )
    filing_types: Optional[List[str]] = Field(
        None,
        description="Filter financial documents by filing type (e.g., ['10-K', '10-Q'])"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "query": "What are transformers in machine learning?",
                    "top_k": 3,
                    "use_hybrid": True,
                    "model": "llama3.2:1b",
                    "categories": ["cs.AI", "cs.LG"],
                    "document_type": "arxiv"
                },
                {
                    "query": "What are Apple's main risk factors?",
                    "top_k": 3,
                    "use_hybrid": True,
                    "model": "llama3.2:1b",
                    "document_type": "financial",
                    "ticker": "AAPL",
                    "filing_types": ["10-K"]
                }
            ]
        }


class AskResponse(BaseModel):
    """Response model for RAG question answering."""

    query: str = Field(..., description="Original user question")
    answer: str = Field(..., description="Generated answer from LLM")
    sources: List[str] = Field(..., description="PDF URLs of source papers")
    chunks_used: int = Field(..., description="Number of chunks used for generation")
    search_mode: str = Field(..., description="Search mode used: bm25 or hybrid")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are transformers in machine learning?",
                "answer": "Transformers are a neural network architecture...",
                "sources": ["https://arxiv.org/pdf/1706.03762.pdf", "https://arxiv.org/pdf/1810.04805.pdf"],
                "chunks_used": 3,
                "search_mode": "hybrid",
            }
        }
