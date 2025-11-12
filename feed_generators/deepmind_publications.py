#!/usr/bin/env python3
"""
RSS Feed Generator for DeepMind Publications
https://deepmind.google/research/publications/
"""

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import re
from feed_generators.date_utils import extract_date_from_element, get_fallback_date

def generate_feed():
    url = "https://deepmind.google/research/publications/"
    
    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        fg = FeedGenerator()
        fg.title('DeepMind Publications')
        fg.link(href=url, rel='alternate')
        fg.description('Latest research publications from DeepMind')
        fg.language('en')
        
        # Find all publication entries
        publications = soup.find_all(['article', 'div', 'li'], class_=re.compile(r'publication|paper|research|item', re.I))
        
        if not publications:
            # Try alternative selectors
            publications = soup.find_all('a', href=re.compile(r'/research/publications/'))
        
        seen_links = set()
        count = 0
        
        for pub in publications[:30]:  # Limit to 30 most recent
            link_elem = pub.find('a', href=True) if pub.name != 'a' else pub
            if not link_elem or not link_elem.get('href'):
                continue
                
            pub_url = link_elem['href']
            if not pub_url.startswith('http'):
                pub_url = f"https://deepmind.google{pub_url}"
            
            if pub_url in seen_links:
                continue
            seen_links.add(pub_url)
            
            # Extract title
            title_elem = pub.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'title|heading', re.I))
            if not title_elem:
                title_elem = link_elem.find(['h1', 'h2', 'h3', 'h4'])
            if not title_elem:
                title_elem = link_elem
            
            title = title_elem.get_text(strip=True) if title_elem else "Untitled Publication"
            
            # Clean title - remove dates that might have been included
            # Remove common date patterns from title (but preserve years that are part of the title)
            # Remove date patterns at the end of title
            title = re.sub(r'\s*\d{4}-\d{2}-\d{2}\s*$', '', title)  # YYYY-MM-DD at end
            title = re.sub(r'\s*\d{1,2}/\d{1,2}/\d{4}\s*$', '', title)  # MM/DD/YYYY at end
            title = re.sub(r'\s*\(\d{4}\)\s*$', '', title)  # (YYYY) at end
            title = re.sub(r'\s*-\s*\d{4}\s*$', '', title)  # - YYYY at end
            title = re.sub(r'\s+', ' ', title).strip()  # Clean up extra spaces
            title = title.strip(' -–—')  # Remove trailing separators
            
            # Extract authors
            authors_elem = pub.find(['div', 'span', 'p'], class_=re.compile(r'author|authors', re.I))
            authors = authors_elem.get_text(strip=True) if authors_elem else ""
            
            # Extract description/abstract
            desc_elem = pub.find(['p', 'div'], class_=re.compile(r'description|abstract|summary', re.I))
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            if authors:
                description = f"Authors: {authors}\n\n{description}".strip()
            
            # Extract date - try multiple methods
            pub_date = extract_date_from_element(pub, pub_url)
            
            # If still no date, use decreasing time offset for ordering
            if not pub_date:
                offset_hours = count
                pub_date = get_fallback_date(offset_hours)
            
            # Create feed entry
            fe = fg.add_entry()
            fe.title(title)
            fe.link(href=pub_url)
            fe.description(description)
            fe.pubDate(pub_date)
            
            count += 1
        
        if count == 0:
            # Fallback: try to find any links to publications
            all_links = soup.find_all('a', href=re.compile(r'/research/publications/'))
            for link in all_links[:30]:
                pub_url = link['href']
                if not pub_url.startswith('http'):
                    pub_url = f"https://deepmind.google{pub_url}"
                
                if pub_url in seen_links:
                    continue
                seen_links.add(pub_url)
                
                title = link.get_text(strip=True) or "DeepMind Publication"
                
                fe = fg.add_entry()
                fe.title(title)
                fe.link(href=pub_url)
                fe.description("")
                fe.pubDate(get_fallback_date(count))
                count += 1
        
        # Write RSS feed
        fg.rss_file('feed_deepmind_publications.xml')
        print(f"Generated feed_deepmind_publications.xml with {count} entries")
        
    except Exception as e:
        print(f"Error generating DeepMind Publications feed: {e}")
        raise

if __name__ == "__main__":
    generate_feed()

