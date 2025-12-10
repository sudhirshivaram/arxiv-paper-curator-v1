from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from src.models.financial_document import FinancialDocument


class FinancialDocumentRepository:
    """Repository for financial document database operations"""

    def __init__(self, session: Session):
        self.session = session

    def create(self, document_data: dict) -> FinancialDocument:
        """Create a new financial document"""
        db_document = FinancialDocument(**document_data)
        self.session.add(db_document)
        self.session.commit()
        self.session.refresh(db_document)
        return db_document

    def get_by_id(self, document_id: UUID) -> Optional[FinancialDocument]:
        """Get document by UUID"""
        stmt = select(FinancialDocument).where(FinancialDocument.id == document_id)
        return self.session.scalar(stmt)

    def get_by_accession_number(self, accession_number: str) -> Optional[FinancialDocument]:
        """Get document by SEC accession number (unique identifier)"""
        stmt = select(FinancialDocument).where(FinancialDocument.accession_number == accession_number)
        return self.session.scalar(stmt)

    def get_by_ticker(self, ticker: str, limit: int = 100, offset: int = 0) -> List[FinancialDocument]:
        """Get all documents for a specific company ticker"""
        stmt = (
            select(FinancialDocument)
            .where(FinancialDocument.ticker_symbol == ticker.upper())
            .order_by(FinancialDocument.filing_date.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(stmt))

    def get_by_document_type(
        self,
        document_type: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[FinancialDocument]:
        """Get documents by type (10-K, 10-Q, etc.)"""
        stmt = (
            select(FinancialDocument)
            .where(FinancialDocument.document_type == document_type)
            .order_by(FinancialDocument.filing_date.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(stmt))

    def get_all(self, limit: int = 100, offset: int = 0) -> List[FinancialDocument]:
        """Get all financial documents"""
        stmt = (
            select(FinancialDocument)
            .order_by(FinancialDocument.filing_date.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(stmt))

    def get_count(self) -> int:
        """Get total count of documents"""
        stmt = select(func.count(FinancialDocument.id))
        return self.session.scalar(stmt) or 0

    def get_parsed_documents(self, limit: int = 100, offset: int = 0) -> List[FinancialDocument]:
        """Get documents that have been successfully parsed"""
        stmt = (
            select(FinancialDocument)
            .where(FinancialDocument.content_parsed == True)
            .order_by(FinancialDocument.parsing_date.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(stmt))

    def get_unparsed_documents(self, limit: int = 100, offset: int = 0) -> List[FinancialDocument]:
        """Get documents that haven't been parsed yet"""
        stmt = (
            select(FinancialDocument)
            .where(FinancialDocument.content_parsed == False)
            .order_by(FinancialDocument.filing_date.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(stmt))

    def get_indexed_documents(self, limit: int = 100, offset: int = 0) -> List[FinancialDocument]:
        """Get documents indexed in OpenSearch"""
        stmt = (
            select(FinancialDocument)
            .where(FinancialDocument.indexed_in_opensearch == True)
            .order_by(FinancialDocument.indexing_date.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(stmt))

    def get_unindexed_documents(self, limit: int = 100, offset: int = 0) -> List[FinancialDocument]:
        """Get parsed documents not yet indexed in OpenSearch"""
        stmt = (
            select(FinancialDocument)
            .where(
                FinancialDocument.content_parsed == True,
                FinancialDocument.indexed_in_opensearch == False
            )
            .order_by(FinancialDocument.parsing_date.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(stmt))

    def get_stats(self) -> dict:
        """Get statistics about financial documents"""
        total_docs = self.get_count()

        # Count parsed documents
        parsed_stmt = select(func.count(FinancialDocument.id)).where(
            FinancialDocument.content_parsed == True
        )
        parsed_docs = self.session.scalar(parsed_stmt) or 0

        # Count indexed documents
        indexed_stmt = select(func.count(FinancialDocument.id)).where(
            FinancialDocument.indexed_in_opensearch == True
        )
        indexed_docs = self.session.scalar(indexed_stmt) or 0

        # Count unique companies
        companies_stmt = select(func.count(func.distinct(FinancialDocument.ticker_symbol)))
        unique_companies = self.session.scalar(companies_stmt) or 0

        # Count by document type
        doc_types_stmt = select(
            FinancialDocument.document_type,
            func.count(FinancialDocument.id)
        ).group_by(FinancialDocument.document_type)
        doc_types = dict(self.session.execute(doc_types_stmt).all())

        return {
            "total_documents": total_docs,
            "parsed_documents": parsed_docs,
            "indexed_documents": indexed_docs,
            "unique_companies": unique_companies,
            "documents_by_type": doc_types,
            "parsing_rate": (parsed_docs / total_docs * 100) if total_docs > 0 else 0,
            "indexing_rate": (indexed_docs / parsed_docs * 100) if parsed_docs > 0 else 0,
        }

    def update(self, document: FinancialDocument) -> FinancialDocument:
        """Update an existing document"""
        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)
        return document

    def upsert(self, document_data: dict) -> FinancialDocument:
        """Insert or update a document based on accession number"""
        accession_number = document_data.get("accession_number")

        if accession_number:
            existing_doc = self.get_by_accession_number(accession_number)
            if existing_doc:
                # Update existing document
                for key, value in document_data.items():
                    if hasattr(existing_doc, key):
                        setattr(existing_doc, key, value)
                return self.update(existing_doc)

        # Create new document
        return self.create(document_data)

    def mark_as_parsed(self, document_id: UUID) -> FinancialDocument:
        """Mark a document as successfully parsed"""
        document = self.get_by_id(document_id)
        if document:
            document.content_parsed = True
            document.parsing_date = datetime.now()
            return self.update(document)
        return None

    def mark_as_indexed(self, document_id: UUID, chunk_count: int) -> FinancialDocument:
        """Mark a document as indexed in OpenSearch"""
        document = self.get_by_id(document_id)
        if document:
            document.indexed_in_opensearch = True
            document.indexing_date = datetime.now()
            document.chunk_count = chunk_count
            return self.update(document)
        return None
