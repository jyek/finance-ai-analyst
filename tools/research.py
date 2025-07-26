"""
Web Research and Document Download Utilities for Financial Data

Provides functions for researching investor relations pages and downloading
financial documents like annual reports, presentations, and SEC filings.
"""

import os
import re
import requests
from typing import Annotated, Dict, Any, List, Optional, Union
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime
import json
from pathlib import Path

# For web scraping and search
try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False
    print("⚠️ BeautifulSoup not available. Install with: pip install beautifulsoup4")

try:
    from ddgs import DDGS
    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DUCKDUCKGO_AVAILABLE = False
    print("⚠️ DuckDuckGo search not available. Install with: pip install ddgs")

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️ Playwright not available. Install with: pip install playwright")

class ResearchUtils:
    """Utilities for researching and downloading financial documents"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create drive folder if it doesn't exist
        self.drive_folder = Path("drive")
        self.drive_folder.mkdir(exist_ok=True)
    
    @staticmethod
    def _index_filings_from_company_website(
        company_name: Annotated[str, "name of the company to search for"],
        search_terms: Annotated[Optional[List[str]], "additional search terms to include"] = None
    ) -> str:
        """
        Search for a company's investor relations page and find financial documents.
        
        Args:
            company_name: Name of the company (e.g., "Apple Inc", "Microsoft")
            search_terms: Additional search terms to include
            
        Returns:
            JSON string with search results and found documents
        """
        if not DUCKDUCKGO_AVAILABLE:
            return json.dumps({
                "error": "DuckDuckGo search not available. Install with: pip install ddgs"
            })
        
        try:
            # Step 1: Find the official company website
            print(f"🔍 Step 1: Finding {company_name}'s official website...")
            official_site = ResearchUtils._find_official_website(company_name)
            
            if not official_site:
                return json.dumps({
                    "error": f"Could not find official website for {company_name}",
                    "company": company_name
                })
            
            print(f"✅ Found official website: {official_site}")
            
            # Step 2: Find the investor relations section
            print(f"🔍 Step 2: Looking for investor relations section...")
            ir_section = ResearchUtils._find_investor_relations_section(official_site, company_name)
            
            if not ir_section:
                return json.dumps({
                    "error": f"Could not find investor relations section for {company_name}",
                    "company": company_name,
                    "official_website": official_site
                })
            
            print(f"✅ Found investor relations section: {ir_section}")
            
            # Step 3: Search for financial documents in the IR section
            print(f"🔍 Step 3: Searching for financial documents...")
            documents = ResearchUtils._search_financial_documents(ir_section, company_name)
            
            result = {
                "company": company_name,
                "official_website": official_site,
                "investor_relations_page": {
                    "url": ir_section,
                    "title": f"{company_name} Investor Relations",
                    "description": f"Investor relations section found on {official_site}"
                },
                "documents_found": documents,
                "search_strategy": "3-step approach: official site → IR section → documents"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": f"Search failed: {str(e)}",
                "company": company_name
            })
    
    @staticmethod
    def _find_official_website(company_name: str) -> Optional[str]:
        """Step 1: Find the official company website"""
        if not DUCKDUCKGO_AVAILABLE:
            return None
        
        try:
            # Clean company name for domain search
            clean_name = company_name.lower().replace(" ", "").replace(".", "").replace("inc", "").replace("ltd", "").replace("llc", "").replace("&", "").replace("and", "")
            
            # Search for the company's official website
            with DDGS() as ddgs:
                search_results = list(ddgs.text(f'"{company_name}" official website', max_results=5))
            
            # If that doesn't work well, try searching for the company domain directly
            if not search_results or all('bing.com/aclick' in result.get('href', '') for result in search_results):
                clean_name = company_name.lower().replace(" ", "").replace(".", "").replace("inc", "").replace("ltd", "").replace("llc", "").replace("&", "").replace("and", "")
                potential_domains = [
                    f"https://www.{clean_name}.com",
                    f"https://{clean_name}.com",
                    f"https://www.{clean_name}.org",
                    f"https://{clean_name}.org"
                ]
                
                # Test if these domains exist
                for domain in potential_domains:
                    try:
                        response = requests.head(domain, timeout=5, allow_redirects=True)
                        if response.status_code == 200:
                            return domain
                    except:
                        continue
            
            if not search_results:
                return None
            
            # Look for the most likely official website
            for result in search_results:
                url = result.get('href', '')
                title = result.get('title', '').lower()
                
                # Filter out ads, affiliate links, and non-official sites
                if any(term in url for term in ['bing.com/aclick', 'googleadservices', 'doubleclick', 'affiliate', 'tracking', 'utm_', 'ref=']):
                    continue
                
                # Check if this looks like an official company website
                if any(term in title for term in [company_name.lower(), clean_name]) and \
                   not any(term in url for term in ['wikipedia', 'linkedin', 'twitter', 'facebook', 'youtube', 'news', 'blog', 'bing.com', 'google.com']):
                    return url
            
            # If no clear match, return the first result that's not a social media/news site or ad
            for result in search_results:
                url = result.get('href', '')
                if not any(term in url for term in ['wikipedia', 'linkedin', 'twitter', 'facebook', 'youtube', 'news', 'blog', 'bing.com', 'google.com', 'bing.com/aclick', 'googleadservices', 'doubleclick', 'affiliate', 'tracking', 'utm_', 'ref=']):
                    return url
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error finding official website: {e}")
            return None
    
    @staticmethod
    def _find_investor_relations_section(official_site: str, company_name: str) -> Optional[str]:
        """Step 2: Find the investor relations section on the official website"""
        if not PLAYWRIGHT_AVAILABLE:
            return None
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = context.new_page()
                
                # Navigate to the official website
                page.goto(official_site, wait_until='networkidle', timeout=30000)
                page.wait_for_timeout(2000)
                
                # Look for investor relations links
                ir_keywords = ['investor relations', 'investors', 'ir', 'shareholder', 'financial reports', 'sec filings']
                
                # Try to find IR links in navigation or main content
                for keyword in ir_keywords:
                    try:
                        # Look for links containing the keyword
                        links = page.query_selector_all(f'a[href*="{keyword}"]')
                        if not links:
                            links = page.query_selector_all(f'a:has-text("{keyword}")')
                        
                        for link in links:
                            href = link.get_attribute('href')
                            if href:
                                # Filter out affiliate/tracking links
                                if any(term in href for term in ['get.revolut.com', 'af_', 'utm_', 'ref=', 'tracking', 'affiliate']):
                                    continue
                                
                                # Make URL absolute
                                if href.startswith('/'):
                                    ir_url = urljoin(official_site, href)
                                elif href.startswith('http'):
                                    ir_url = href
                                else:
                                    ir_url = urljoin(official_site, href)
                                
                                # Verify it's likely an IR page and not an affiliate link
                                if any(term in ir_url.lower() for term in ir_keywords) and \
                                   not any(term in ir_url.lower() for term in ['get.revolut.com', 'af_', 'utm_', 'ref=', 'tracking', 'affiliate']) and \
                                   urlparse(ir_url).netloc == urlparse(official_site).netloc:
                                    browser.close()
                                    return ir_url
                    except:
                        continue
                
                # If no IR links found, try common IR URL patterns
                common_ir_paths = [
                    '/investor-relations',
                    '/investors',
                    '/ir',
                    '/shareholders',
                    '/financial-reports',
                    '/reports-and-results',
                    '/investor-relations/',
                    '/investors/',
                    '/ir/',
                    '/en-US/reports-and-results',
                    '/en-US/investors',
                    '/en-US/investor-relations',
                    '/reports',
                    '/financials',
                    '/about/investors',
                    '/about/investor-relations'
                ]
                
                for path in common_ir_paths:
                    try:
                        test_url = urljoin(official_site, path)
                        # Ensure we stay on the same domain
                        if urlparse(test_url).netloc == urlparse(official_site).netloc:
                            response = page.goto(test_url, wait_until='networkidle', timeout=10000)
                            if response and response.status == 200:
                                browser.close()
                                return test_url
                    except:
                        continue
                
                browser.close()
                return None
                
        except Exception as e:
            print(f"⚠️ Error finding investor relations section: {e}")
            return None
    

    @staticmethod
    def _filter_and_prioritize_documents(
        documents: List[Dict[str, Any]], 
        document_types: List[str], 
        document_keywords: Optional[List[str]] = None,
        prioritize_latest: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Filter and prioritize documents based on type, keywords, and recency.
        
        Args:
            documents: List of found documents
            document_types: Types of documents to include
            document_keywords: Keywords to look for in titles
            prioritize_latest: Whether to prioritize recent documents
            
        Returns:
            Filtered and prioritized list of documents
        """
        filtered_docs = []
        
        for doc in documents:
            # Check document type
            if doc["type"] not in document_types:
                continue
            
            # Check keywords if specified
            if document_keywords:
                title_lower = doc["title"].lower()
                if not any(keyword.lower() in title_lower for keyword in document_keywords):
                    continue
            
            # Add relevance score
            relevance_score = 0
            
            # Boost score for annual reports and financial statements
            if any(term in doc["title"].lower() for term in ['annual', 'financial statements', '10-k']):
                relevance_score += 10
            
            # Boost score for quarterly reports
            if any(term in doc["title"].lower() for term in ['quarterly', 'q1', 'q2', 'q3', 'q4']):
                relevance_score += 8
            
            # Boost score for earnings reports
            if any(term in doc["title"].lower() for term in ['earnings', 'results']):
                relevance_score += 6
            
            # Boost score for recent years (2024, 2023, etc.)
            current_year = datetime.now().year
            for year in range(current_year, current_year - 3, -1):
                if str(year) in doc["title"]:
                    relevance_score += (current_year - year + 1) * 2
                    break
            
            # Boost score for specific keywords if provided
            if document_keywords:
                title_lower = doc["title"].lower()
                for keyword in document_keywords:
                    if keyword.lower() in title_lower:
                        relevance_score += 5
            
            doc["relevance_score"] = relevance_score
            filtered_docs.append(doc)
        
        # Sort by relevance score (highest first)
        filtered_docs.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return filtered_docs
    
    @staticmethod
    def _search_financial_documents(ir_url: str, company_name: str) -> List[Dict[str, Any]]:
        """Search for financial documents on an investor relations page"""
        # Try Playwright first (better for anti-bot protection)
        if PLAYWRIGHT_AVAILABLE:
            try:
                return ResearchUtils._search_financial_documents_with_playwright(ir_url, company_name)
            except Exception as e:
                print(f"⚠️ Playwright search failed, falling back to requests: {e}")
        
        # Fallback to requests + BeautifulSoup
        if not BEAUTIFULSOUP_AVAILABLE:
            return []
        
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            response = session.get(ir_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            documents = []
            
            # Look for document links
            document_patterns = [
                r'annual\s*report',
                r'10-k',
                r'10-q', 
                r'presentation',
                r'earnings\s*release',
                r'quarterly\s*report',
                r'financial\s*results',
                r'sec\s*filing',
                r'\.pdf$',
                r'\.doc$',
                r'\.xlsx$'
            ]
            
            # Find all links
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True).lower()
                
                # Check if link matches document patterns
                is_document = any(re.search(pattern, text, re.IGNORECASE) or 
                                re.search(pattern, href, re.IGNORECASE) 
                                for pattern in document_patterns)
                
                if is_document:
                    # Determine document type
                    doc_type = "other"
                    if any(term in text for term in ['annual', '10-k', 'annual report', 'financial statements']):
                        doc_type = "annual_report"
                    elif any(term in text for term in ['presentation', 'earnings', 'quarterly', 'q1', 'q2', 'q3', 'q4']):
                        doc_type = "presentation"
                    elif any(term in text for term in ['filing', 'sec', '10-q', 'pillar', 'disclosure']):
                        doc_type = "filing"
                    
                    # Make URL absolute
                    full_url = urljoin(ir_url, href)
                    
                    documents.append({
                        "title": link.get_text(strip=True),
                        "url": full_url,
                        "type": doc_type
                    })
            
            return documents[:10]  # Limit to 10 documents
            
        except Exception as e:
            print(f"⚠️ Error searching documents on {ir_url}: {e}")
            return []
    
    @staticmethod
    def _search_financial_documents_with_playwright(ir_url: str, company_name: str) -> List[Dict[str, Any]]:
        """Search for financial documents using Playwright browser simulation"""
        if not PLAYWRIGHT_AVAILABLE:
            return []
        
        try:
            with sync_playwright() as p:
                # Launch browser with realistic settings
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--disable-gpu'
                    ]
                )
                
                # Create context with realistic user agent
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080}
                )
                
                page = context.new_page()
                
                # Navigate to the page
                print(f"🌐 Loading page with browser simulation: {ir_url}")
                page.goto(ir_url, wait_until='networkidle', timeout=30000)
                
                # Wait a bit for dynamic content to load
                page.wait_for_timeout(3000)
                
                # Look for document links
                document_patterns = [
                    r'annual\s*report',
                    r'10-k',
                    r'10-q', 
                    r'presentation',
                    r'earnings\s*release',
                    r'quarterly\s*report',
                    r'financial\s*results',
                    r'sec\s*filing',
                    r'\.pdf$',
                    r'\.doc$',
                    r'\.xlsx$'
                ]
                
                documents = []
                
                # Find all links on the page
                links = page.query_selector_all('a[href]')
                
                for link in links:
                    try:
                        href = link.get_attribute('href') or ''
                        text = link.inner_text().lower()
                        
                        # Check if link matches document patterns
                        is_document = any(re.search(pattern, text, re.IGNORECASE) or 
                                        re.search(pattern, href, re.IGNORECASE) 
                                        for pattern in document_patterns)
                        
                        if is_document:
                            # Determine document type
                            doc_type = "other"
                            if any(term in text for term in ['annual', '10-k', 'annual report', 'financial statements']):
                                doc_type = "annual_report"
                            elif any(term in text for term in ['presentation', 'earnings', 'quarterly', 'q1', 'q2', 'q3', 'q4']):
                                doc_type = "presentation"
                            elif any(term in text for term in ['filing', 'sec', '10-q', 'pillar', 'disclosure']):
                                doc_type = "filing"
                            
                            # Make URL absolute
                            full_url = urljoin(ir_url, href)
                            
                            documents.append({
                                "title": link.inner_text().strip(),
                                "url": full_url,
                                "type": doc_type
                            })
                    except Exception as e:
                        # Skip problematic links
                        continue
                
                browser.close()
                return documents[:10]  # Limit to 10 documents
                
        except Exception as e:
            print(f"⚠️ Playwright error searching documents on {ir_url}: {e}")
            return []
    
    @staticmethod
    def _download_document(url: str, company_name: str, doc_type: str, title: str) -> Dict[str, Any]:
        """Download a single document"""
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            response = session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Determine file extension
            content_type = response.headers.get('content-type', '')
            if 'pdf' in content_type:
                ext = '.pdf'
            elif 'excel' in content_type or 'spreadsheet' in content_type:
                ext = '.xlsx'
            elif 'word' in content_type or 'document' in content_type:
                ext = '.docx'
            else:
                ext = '.pdf'  # Default to PDF
            
            # Create filename - shorter and more manageable
            safe_company = re.sub(r'[^\w\s-]', '', company_name).strip()
            
            # Extract key information from title for shorter filename
            title_lower = title.lower()
            
            # Try to extract year
            year_match = re.search(r'20\d{2}', title)
            year = year_match.group() if year_match else datetime.now().strftime("%Y")
            
            # Try to extract quarter
            quarter_match = re.search(r'q[1-4]', title_lower)
            quarter = quarter_match.group().upper() if quarter_match else ""
            
            # Try to extract document type keywords
            doc_keywords = []
            if any(term in title_lower for term in ['annual', 'financial statements']):
                doc_keywords.append('annual')
            elif any(term in title_lower for term in ['quarterly', 'q1', 'q2', 'q3', 'q4']):
                doc_keywords.append('quarterly')
            elif any(term in title_lower for term in ['pillar', 'disclosure']):
                doc_keywords.append('regulatory')
            elif any(term in title_lower for term in ['earnings', 'results']):
                doc_keywords.append('earnings')
            
            # Create short descriptive name
            if doc_keywords:
                doc_desc = doc_keywords[0]
            else:
                # Take first few words of title (max 3 words)
                words = re.sub(r'[^\w\s]', '', title).split()[:3]
                doc_desc = '_'.join(words).lower()
            
            # Build filename: Company_Type_Year_Quarter_ShortDesc.pdf
            filename_parts = [safe_company, doc_type, year]
            if quarter:
                filename_parts.append(quarter)
            filename_parts.append(doc_desc)
            
            filename = '_'.join(filename_parts) + ext
            
            # Create company folder
            company_folder = Path("drive") / safe_company
            company_folder.mkdir(exist_ok=True)
            
            filepath = company_folder / filename
            
            # Download file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return {
                "success": True,
                "filename": filename,
                "filepath": str(filepath),
                "url": url,
                "type": doc_type,
                "title": title,
                "size_bytes": os.path.getsize(filepath)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "type": doc_type,
                "title": title
            }
    
    @staticmethod
    def get_filings_from_company_website(
        company_name: Annotated[str, "name of the company"],
        search_criteria: Annotated[Dict[str, Any], "search criteria including document_types, keywords, max_documents, etc."]
    ) -> str:
        """
        Search for and download specific documents based on agent's criteria.
        
        Args:
            company_name: Name of the company
            search_criteria: Dictionary with search criteria:
                - document_types: List of document types to look for
                - keywords: List of keywords to search for in titles
                - max_documents: Maximum number of documents to download
                - prioritize_latest: Whether to prioritize recent documents
                - description: Agent's description of what they're looking for
                
        Returns:
            JSON string with search and download results
        """
        try:
            # Extract search criteria (handle both singular and plural forms)
            document_types = search_criteria.get('document_types', search_criteria.get('document_type', ['annual_report', 'presentation', 'filing']))
            keywords = search_criteria.get('keywords', [])
            max_documents = search_criteria.get('max_documents', 5)
            prioritize_latest = search_criteria.get('prioritize_latest', True)
            description = search_criteria.get('description', '')
            
            print(f"🔍 Searching for documents matching criteria: {description}")
            print(f"   Document types: {document_types}")
            print(f"   Keywords: {keywords}")
            print(f"   Max documents: {max_documents}")
            
            # Search for documents
            search_result = ResearchUtils._index_filings_from_company_website(company_name)
            search_data = json.loads(search_result)
            
            if "error" in search_data:
                return search_result
            
            documents = search_data["documents_found"]
            
            # Filter and prioritize documents
            filtered_docs = ResearchUtils._filter_and_prioritize_documents(
                documents, document_types, keywords, prioritize_latest
            )
            
            # Show what was found
            print(f"📋 Found {len(filtered_docs)} relevant documents:")
            for i, doc in enumerate(filtered_docs[:max_documents]):
                score = doc.get('relevance_score', 0)
                print(f"   {i+1}. {doc['title']} (score: {score})")
            
            # Download documents
            downloaded = []
            download_count = 0
            
            for doc in filtered_docs[:max_documents]:
                try:
                    download_result = ResearchUtils._download_document(
                        doc["url"], 
                        company_name, 
                        doc["type"], 
                        doc["title"]
                    )
                    if download_result["success"]:
                        downloaded.append(download_result)
                        download_count += 1
                        print(f"   ✅ Downloaded: {doc['title']}")
                    else:
                        print(f"   ❌ Failed to download: {doc['title']}")
                except Exception as e:
                    print(f"   ❌ Error downloading {doc['title']}: {e}")
            
            # Create a clean copy of search criteria for JSON serialization
            clean_search_criteria = {
                "document_types": document_types,
                "keywords": keywords,
                "max_documents": max_documents,
                "prioritize_latest": prioritize_latest,
                "description": description
            }
            
            result = {
                "company": company_name,
                "search_criteria": clean_search_criteria,
                "documents_found": len(filtered_docs),
                "documents_downloaded": len(downloaded),
                "downloaded_files": downloaded,
                "filtered_documents": [
                    {
                        "title": doc["title"],
                        "type": doc["type"],
                        "url": doc["url"],
                        "relevance_score": doc.get("relevance_score", 0)
                    }
                    for doc in filtered_docs[:max_documents]
                ]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            # Create a safe copy of search criteria for error reporting
            safe_search_criteria = {
                "document_types": search_criteria.get('document_types', search_criteria.get('document_type', [])),
                "max_documents": search_criteria.get('max_documents', 5),
                "prioritize_latest": search_criteria.get('prioritize_latest', True)
            }
            return json.dumps({
                "error": f"Search and download failed: {str(e)}",
                "company": company_name,
                "search_criteria": safe_search_criteria
            })
    
    @staticmethod
    def list_downloaded_filings(
        company_name: Annotated[Optional[str], "filter by company name"] = None
    ) -> str:
        """
        List all downloaded financial documents.
        
        Args:
            company_name: Optional company name to filter results
            
        Returns:
            JSON string with list of downloaded documents
        """
        try:
            drive_folder = Path("drive")
            if not drive_folder.exists():
                return json.dumps({"documents": [], "total": 0})
            
            documents = []
            
            for company_folder in drive_folder.iterdir():
                if company_folder.is_dir():
                    if company_name and company_name.lower() not in company_folder.name.lower():
                        continue
                    
                    for file_path in company_folder.iterdir():
                        if file_path.is_file():
                            # Parse filename to extract metadata
                            filename = file_path.name
                            parts = filename.split('_')
                            
                            if len(parts) >= 3:
                                doc_type = parts[1] if len(parts) > 1 else "unknown"
                                title = "_".join(parts[2:-1]) if len(parts) > 3 else "unknown"
                            else:
                                doc_type = "unknown"
                                title = filename
                            
                            documents.append({
                                "company": company_folder.name,
                                "filename": filename,
                                "filepath": str(file_path),
                                "type": doc_type,
                                "title": title,
                                "size_bytes": file_path.stat().st_size,
                                "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                            })
            
            result = {
                "documents": documents,
                "total": len(documents)
            }
            
            if company_name:
                result["filtered_by"] = company_name
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": f"Failed to list documents: {str(e)}"
            }) 