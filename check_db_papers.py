#!/usr/bin/env python3
"""Quick script to check papers in database"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables
os.environ["POSTGRES_DATABASE_URL"] = "postgresql+psycopg2://rag_user:rag_password@localhost:5432/rag_db"

from src.db.factory import make_database
from src.models.paper import Paper

database = make_database()

print("DATABASE PAPER INSPECTION")
print("=" * 60)

with database.get_session() as session:
    # Total count
    total_papers = session.query(Paper).count()
    print(f"Total papers in database: {total_papers}")

    # Papers with raw_text
    papers_with_text = session.query(Paper).filter(
        Paper.raw_text != None,
        Paper.raw_text != ""
    ).count()
    print(f"Papers with raw_text: {papers_with_text}")

    # Papers processed
    papers_processed = session.query(Paper).filter(
        Paper.pdf_processed == True
    ).count()
    print(f"Papers marked as pdf_processed: {papers_processed}")

    print("\n" + "=" * 60)
    print("SAMPLE PAPERS (first 5):")
    print("=" * 60)

    # Get all papers
    all_papers = session.query(Paper).limit(5).all()

    if all_papers:
        for i, paper in enumerate(all_papers, 1):
            print(f"\n{i}. arXiv ID: {paper.arxiv_id}")
            print(f"   Title: {paper.title[:60]}...")
            print(f"   PDF Processed: {paper.pdf_processed}")
            print(f"   Parser Used: {paper.parser_used}")

            # Check raw_text
            if paper.raw_text is None:
                print(f"   raw_text: NULL")
            elif paper.raw_text == "":
                print(f"   raw_text: EMPTY STRING")
            else:
                print(f"   raw_text: {len(paper.raw_text):,} characters")

            # Check sections
            if paper.sections:
                if isinstance(paper.sections, list):
                    print(f"   sections: {len(paper.sections)} sections (list)")
                elif isinstance(paper.sections, dict):
                    print(f"   sections: {len(paper.sections)} sections (dict)")
                else:
                    print(f"   sections: {type(paper.sections)}")
            else:
                print(f"   sections: None/Empty")
    else:
        print("No papers found in database!")

print("\n" + "=" * 60)
