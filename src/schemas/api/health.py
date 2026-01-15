from typing import Dict, Optional

from pydantic import BaseModel, Field


class ServiceStatus(BaseModel):
    """Individual service status."""

    status: str = Field(..., description="Service status", example="healthy")
    message: Optional[str] = Field(None, description="Status message", example="Connected successfully")


class IndexStats(BaseModel):
    """Statistics for a single index."""

    documents: int = Field(..., description="Number of documents/chunks in index")
    index_name: str = Field(..., description="Name of the OpenSearch index")
    size_mb: Optional[float] = Field(None, description="Index size in MB")


class StatsResponse(BaseModel):
    """Document statistics response model."""

    arxiv: IndexStats = Field(..., description="arXiv papers index stats")
    financial: IndexStats = Field(..., description="Financial documents index stats")
    total_documents: int = Field(..., description="Total documents across all indexes")

    class Config:
        json_schema_extra = {
            "example": {
                "arxiv": {"documents": 200, "index_name": "arxiv-papers-chunks", "size_mb": 1.5},
                "financial": {"documents": 11, "index_name": "financial-docs-chunks", "size_mb": 0.2},
                "total_documents": 211
            }
        }


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Overall health status", example="ok")
    version: str = Field(..., description="Application version", example="0.1.0")
    environment: str = Field(..., description="Deployment environment", example="development")
    service_name: str = Field(..., description="Service identifier", example="rag-api")
    services: Optional[Dict[str, ServiceStatus]] = Field(None, description="Individual service statuses")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "status": "ok",
                "version": "0.1.0",
                "environment": "development",
                "service_name": "rag-api",
                "services": {
                    "database": {"status": "healthy", "message": "Connected successfully"},
                    "pdf_parser": {"status": "healthy", "message": "Docling parser ready"},
                },
            }
        }
