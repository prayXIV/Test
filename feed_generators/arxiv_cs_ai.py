#!/usr/bin/env python3
"""
RSS Feed Generator for arXiv cs.AI (Computer Science - Artificial Intelligence)
https://arxiv.org/list/cs.AI/recent?skip=0&show=500
Generates feed with 500 most recent papers.
"""

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re
from feed_generators.date_utils import parse_date_string, get_fallback_date

def generate_feed():
    url = "https://arxiv.org/list/cs.AI/recent?skip=0&show=500"
    
    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        fg = FeedGenerator()
        fg.title('arXiv cs.AI (Computer Science - Artificial Intelligence)')
        fg.link(href=url, rel='alternate')
        fg.description('Recent papers from arXiv cs.AI category')
        fg.language('en')
        
        # arXiv uses a specific structure with dl/dt/dd tags
        entries = []
        
        # Find the main content area
        content_area = soup.find('div', id='content') or soup.find('body')
        if not content_area:
            content_area = soup
        
        dl_elements = content_area.find_all('dl')
        
        for dl in dl_elements:
            dt_elements = dl.find_all('dt')
            dd_elements = dl.find_all('dd')
            
            for i, dt in enumerate(dt_elements):
                if i >= len(dd_elements):
                    break
                
                dd = dd_elements[i]
                
                # Extract arXiv ID and link - try multiple patterns
                link_elem = dt.find('a', href=re.compile(r'arxiv\.org/abs/'))
                if not link_elem:
                    # Try finding link in the dt element text
                    link_elem = dt.find('a', href=True)
                    if link_elem and 'arxiv' in link_elem.get('href', '').lower():
                        # Make sure it's a full URL
                        href = link_elem['href']
                        if not href.startswith('http'):
                            if href.startswith('/'):
                                link_elem['href'] = f"https://arxiv.org{href}"
                            else:
                                link_elem['href'] = f"https://arxiv.org/abs/{href}"
                    else:
                        continue
                
                arxiv_url = link_elem['href']
                if not arxiv_url.startswith('http'):
                    arxiv_url = f"https://{arxiv_url}"
                
                arxiv_id = link_elem.get_text(strip=True)
                
                # Extract title
                title_elem = dd.find('div', class_='list-title')
                if title_elem:
                    title = title_elem.get_text(strip=True).replace('Title:', '').strip()
                else:
                    title = f"arXiv:{arxiv_id}"
                
                # Extract authors
                authors_elem = dd.find('div', class_='list-authors')
                authors = ""
                if authors_elem:
                    authors = authors_elem.get_text(strip=True).replace('Authors:', '').strip()
                
                # Extract abstract
                abstract_elem = dd.find('p', class_='mathjax')
                abstract = abstract_elem.get_text(strip=True) if abstract_elem else ""
                
                # Extract subjects
                subjects_elem = dd.find('div', class_='list-subjects')
                subjects = ""
                if subjects_elem:
                    subjects = subjects_elem.get_text(strip=True).replace('Subjects:', '').strip()
                
                # Build description
                description_parts = []
                if authors:
                    description_parts.append(f"Authors: {authors}")
                if subjects:
                    description_parts.append(f"Subjects: {subjects}")
                if abstract:
                    description_parts.append(f"\n{abstract}")
                
                description = "\n".join(description_parts)
                
                # Extract date from arXiv
                pub_date = None
                
                # Method 1: Try to extract from list-date div
                date_elem = dd.find('div', class_='list-date')
                if date_elem:
                    date_str = date_elem.get_text(strip=True)
                    # arXiv dates are usually in format like "Submitted on 1 Jan 2025" or "Submitted on 1 Jan 2025 (v1), 15 Jan 2025 (v2)"
                    # Extract the first date (submission date)
                    date_match = re.search(r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{4})', date_str, re.I)
                    if date_match:
                        day, month_str, year = date_match.groups()
                        month_map = {
                            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                            'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
                            'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                        }
                        month = month_map.get(month_str.lower()[:3], 1)
                        pub_date = datetime(int(year), month, int(day), tzinfo=timezone.utc)
                
                # Method 2: Extract date from arXiv ID (format: YYMM.NNNNN)
                # arXiv IDs contain year and month: YYMM
                if not pub_date and arxiv_id:
                    arxiv_id_match = re.search(r'(\d{2})(\d{2})\.\d+', arxiv_id)
                    if arxiv_id_match:
                        yy, mm = arxiv_id_match.groups()
                        year = 2000 + int(yy) if int(yy) < 50 else 1900 + int(yy)
                        month = int(mm)
                        # Use 15th of month as default day
                        pub_date = datetime(year, month, 15, tzinfo=timezone.utc)
                
                # Method 3: Extract from URL if it contains date
                if not pub_date:
                    url_date_match = re.search(r'/(\d{4})(\d{2})(\d{2})', arxiv_url)
                    if url_date_match:
                        year, month, day = url_date_match.groups()
                        pub_date = datetime(int(year), int(month), int(day), tzinfo=timezone.utc)
                
                # If still no date, use decreasing time offset for ordering
                if not pub_date:
                    # Use days instead of hours for better spacing
                    from datetime import timedelta
                    offset_days = len(entries) * 2  # Each entry is 2 days older
                    pub_date = datetime.now(timezone.utc) - timedelta(days=offset_days)
                
                # Create feed entry
                fe = fg.add_entry()
                fe.title(title)
                fe.link(href=arxiv_url)
                fe.description(description)
                fe.pubDate(pub_date)
                fe.guid(arxiv_url, permalink=True)
                
                entries.append(arxiv_id)
        
        # If no entries found with dl/dt/dd structure, try alternative parsing
        if len(entries) == 0:
            # Look for links to arxiv papers - try multiple patterns
            arxiv_links = soup.find_all('a', href=re.compile(r'arxiv\.org/abs/|/abs/\d'))
            seen_urls = set()
            
            for link in arxiv_links[:500]:
                arxiv_url = link.get('href', '')
                if not arxiv_url:
                    continue
                    
                # Normalize URL
                if not arxiv_url.startswith('http'):
                    if arxiv_url.startswith('/'):
                        arxiv_url = f"https://arxiv.org{arxiv_url}"
                    elif arxiv_url.startswith('abs/'):
                        arxiv_url = f"https://arxiv.org/{arxiv_url}"
                    else:
                        arxiv_url = f"https://arxiv.org/abs/{arxiv_url}"
                
                if arxiv_url in seen_urls:
                    continue
                seen_urls.add(arxiv_url)
                
                # Extract arXiv ID from URL
                arxiv_id_match = re.search(r'/(\d{4}\.\d{4,5})', arxiv_url)
                if arxiv_id_match:
                    arxiv_id = arxiv_id_match.group(1)
                else:
                    arxiv_id = link.get_text(strip=True) or "unknown"
                
                title = f"arXiv:{arxiv_id}"
                
                # Try to find title nearby
                parent = link.parent
                if parent:
                    title_elem = parent.find(['span', 'div'], class_=re.compile(r'title', re.I))
                    if not title_elem:
                        # Look for title in siblings
                        for sibling in parent.find_next_siblings():
                            title_elem = sibling.find(['span', 'div', 'strong'], class_=re.compile(r'title', re.I))
                            if title_elem:
                                break
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                
                fe = fg.add_entry()
                fe.title(title)
                fe.link(href=arxiv_url)
                fe.description("")
                fe.pubDate(get_fallback_date(len(entries)))
                fe.guid(arxiv_url, permalink=True)
                entries.append(arxiv_id)
        
        # Write RSS feed
        fg.rss_file('feed_arxiv_cs_ai.xml')
        print(f"Generated feed_arxiv_cs_ai.xml with {len(entries)} entries")
        
    except Exception as e:
        print(f"Error generating arXiv cs.AI feed: {e}")
        raise

if __name__ == "__main__":
    generate_feed()

