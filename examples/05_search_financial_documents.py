#!/usr/bin/env python3
"""
Example: Get Filings From Company Website

This script demonstrates how to use the ResearchUtils to:
1. Search and download financial documents using different criteria
2. Show agent-specific search scenarios
3. List downloaded documents

Usage:
    python examples/05_search_financial_documents.py
"""

import json
import sys
import os

# Add the parent directory to the path so we can import the tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.research import ResearchUtils

def main():
    print("🔍 Finance AI Analyst - Get Filings From Company Website")
    print("=" * 70)
    
    # Initialize research utilities
    research_utils = ResearchUtils()
    
    # Example 1: Basic search for Revolut financial filings
    print("\n1. Basic Search: Revolut Financial Filings")
    print("-" * 50)
    basic_criteria = {
        "document_types": ["filing", "annual_report"],
        "keywords": ["financial reports", "annual report", "filing", "regulatory"],
        "max_documents": 10,
        "prioritize_latest": True,
        "description": "Revolut financial filings and annual reports"
    }
    
    revolut_result = ResearchUtils.get_filings_from_company_website("Revolut", basic_criteria)
    revolut_data = json.loads(revolut_result)
    
    if "error" not in revolut_data:
        print(f"✅ Found {revolut_data['documents_found']} documents")
        print(f"✅ Downloaded {revolut_data['documents_downloaded']} files")
        
        # Show downloaded files
        for doc in revolut_data['downloaded_files']:
            print(f"   ✅ {doc['filename']} ({doc['size_bytes']} bytes)")
            print(f"      Type: {doc['type']}")
            print(f"      Title: {doc['title']}")
    else:
        print(f"❌ Error: {revolut_data['error']}")
    
    # Example 2: Agent looking for latest annual reports
    print("\n2. Agent Scenario: Latest Annual Report for Financial Analysis")
    print("-" * 50)
    annual_report_criteria = {
        "document_types": ["annual_report"],
        "keywords": ["annual", "2024", "financial statements"],
        "max_documents": 3,
        "prioritize_latest": True,
        "description": "Latest annual report for financial analysis"
    }
    
    result2 = ResearchUtils.get_filings_from_company_website("Revolut", annual_report_criteria)
    data2 = json.loads(result2)
    
    if "error" not in data2:
        print(f"✅ Found {data2['documents_found']} relevant documents")
        print(f"✅ Downloaded {data2['documents_downloaded']} files")
    else:
        print(f"❌ Error: {data2['error']}")
    
    # Example 3: Agent looking for quarterly earnings reports
    print("\n3. Agent Scenario: Quarterly Financial Statements for Performance Analysis")
    print("-" * 50)
    quarterly_criteria = {
        "document_types": ["annual_report", "presentation"],
        "keywords": ["quarterly", "q4", "q3", "earnings", "results"],
        "max_documents": 5,
        "prioritize_latest": True,
        "description": "Quarterly financial statements for recent performance analysis"
    }
    
    result3 = ResearchUtils.get_filings_from_company_website("Revolut", quarterly_criteria)
    data3 = json.loads(result3)
    
    if "error" not in data3:
        print(f"✅ Found {data3['documents_found']} relevant documents")
        print(f"✅ Downloaded {data3['documents_downloaded']} files")
    else:
        print(f"❌ Error: {data3['error']}")
    
    # Example 4: Agent looking for regulatory filings
    print("\n4. Agent Scenario: Regulatory Filings and Compliance Documents")
    print("-" * 50)
    regulatory_criteria = {
        "document_types": ["filing"],
        "keywords": ["pillar", "disclosure", "regulatory", "compliance"],
        "max_documents": 3,
        "prioritize_latest": True,
        "description": "Regulatory filings and compliance documents"
    }
    
    result4 = ResearchUtils.get_filings_from_company_website("Revolut", regulatory_criteria)
    data4 = json.loads(result4)
    
    if "error" not in data4:
        print(f"✅ Found {data4['documents_found']} relevant documents")
        print(f"✅ Downloaded {data4['documents_downloaded']} files")
    else:
        print(f"❌ Error: {data4['error']}")
    
    # Example 5: Agent with comprehensive search criteria
    print("\n5. Agent Scenario: Comprehensive Financial Analysis")
    print("-" * 50)
    comprehensive_criteria = {
        "document_types": ["annual_report", "presentation", "filing"],
        "keywords": ["2024", "financial", "statements"],
        "max_documents": 10,
        "prioritize_latest": True,
        "description": "All recent financial documents for comprehensive analysis"
    }
    
    result5 = ResearchUtils.get_filings_from_company_website("Revolut", comprehensive_criteria)
    data5 = json.loads(result5)
    
    if "error" not in data5:
        print(f"✅ Found {data5['documents_found']} relevant documents")
        print(f"✅ Downloaded {data5['documents_downloaded']} files")
    else:
        print(f"❌ Error: {data5['error']}")
    
    # List all downloaded documents
    print("\n6. Listing All Downloaded Documents")
    print("-" * 50)
    all_docs = ResearchUtils.list_downloaded_filings()
    docs_data = json.loads(all_docs)
    
    if "error" not in docs_data:
        print(f"✅ Found {docs_data['total']} total documents")
        for doc in docs_data['documents']:
            print(f"   📄 {doc['filename']} ({doc['type']})")
            print(f"      Size: {doc['size_bytes']} bytes")
            print(f"      Modified: {doc['modified']}")
    else:
        print(f"❌ Error: {docs_data['error']}")
    
    # List Revolut documents specifically
    print("\n7. Listing Revolut Documents Only")
    print("-" * 50)
    revolut_docs = ResearchUtils.list_downloaded_filings("Revolut")
    revolut_docs_data = json.loads(revolut_docs)
    
    if "error" not in revolut_docs_data:
        print(f"✅ Found {revolut_docs_data['total']} Revolut documents")
        for doc in revolut_docs_data['documents']:
            print(f"   📄 {doc['filename']} ({doc['type']})")
            print(f"      Size: {doc['size_bytes']} bytes")
            print(f"      Modified: {doc['modified']}")
    else:
        print(f"❌ Error: {revolut_docs_data['error']}")
    
    print("\n" + "=" * 70)
    print("✅ Comprehensive financial document search completed!")
    print("\nKey Features Demonstrated:")
    print("- Basic document search and download")
    print("- Agent-specific search criteria")
    print("- Different document types (annual reports, presentations, filings)")
    print("- Keyword-based filtering")
    print("- Document prioritization by recency")
    print("- Listing and managing downloaded files")
    print("\nNote: Downloaded files are stored in the 'drive/Revolut/' folder")

if __name__ == "__main__":
    main() 