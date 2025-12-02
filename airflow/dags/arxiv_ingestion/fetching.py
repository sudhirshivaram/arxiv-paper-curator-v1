import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from .common import get_cached_services

logger = logging.getLogger(__name__)


async def run_paper_ingestion_pipeline(
    target_date: Optional[str] = None,
    process_pdfs: bool = True,
) -> dict:
    """Async wrapper for the paper ingestion pipeline.

    :param target_date: Date to fetch papers for (YYYYMMDD format), or None for most recent
    :param process_pdfs: Whether to download and process PDFs
    :returns: Dictionary with ingestion statistics
    """
    arxiv_client, _, database, metadata_fetcher, _ = get_cached_services()

    # Override with explicit value (reduced batch size for PDF processing)
    max_results = 25
    logger.info(f"Using max_results override: {max_results}")

    with database.get_session() as session:
        return await metadata_fetcher.fetch_and_process_papers(
            max_results=max_results,
            from_date=target_date,
            to_date=target_date,
            process_pdfs=process_pdfs,
            store_to_db=True,
            db_session=session,
        )


def fetch_daily_papers(**context):
    """Fetch daily papers from arXiv and store in PostgreSQL.

    This task:
    1. Determines the target date (defaults to today for manual runs, yesterday for scheduled)
    2. Fetches papers from arXiv API
    3. Downloads and processes PDFs using Docling
    4. Stores metadata and parsed content in PostgreSQL

    Note: OpenSearch indexing is handled by a separate dedicated task
    """
    logger.info("Starting daily paper fetching task")

    # For manual runs, use today; for scheduled runs, use yesterday
    execution_date = context.get("execution_date")
    run_id = context.get("run_id", "")

    if "manual" in run_id:
        # Manual trigger - fetch papers from last 7 days
        week_ago = datetime.now() - timedelta(days=7)
        target_date = week_ago.strftime("%Y%m%d")
        logger.info(f"Manual run detected - fetching papers from last week: {target_date}")
    elif execution_date:
        # Scheduled run - use execution date minus 1 day
        target_dt = execution_date - timedelta(days=1)
        target_date = target_dt.strftime("%Y%m%d")
        logger.info(f"Scheduled run - fetching papers from: {target_date}")
    else:
        # Fallback to yesterday
        yesterday = datetime.now() - timedelta(days=1)
        target_date = yesterday.strftime("%Y%m%d")
        logger.info(f"Fallback - fetching papers from yesterday: {target_date}")

    if target_date:
        logger.info(f"Fetching papers for date: {target_date}")
    else:
        logger.info(f"Fetching most recent papers (no date restriction)")

    results = asyncio.run(
        run_paper_ingestion_pipeline(
            target_date=target_date,
            process_pdfs=True,  # Enabled with smaller batch (25 papers) to avoid OOM
        )
    )

    logger.info(f"Daily fetch complete: {results['papers_fetched']} papers for {target_date}")

    results["date"] = target_date
    ti = context.get("ti")
    if ti:
        ti.xcom_push(key="fetch_results", value=results)

    return results
