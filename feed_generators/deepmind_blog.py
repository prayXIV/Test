#!/usr/bin/env python3
"""
RSS Feed Generator for DeepMind Blog
https://deepmind.google/blog/
"""

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone, timedelta
import re
import json
from feed_generators.date_utils import extract_date_from_element, get_fallback_date, parse_date_string

def generate_feed():
    url = "https://deepmind.google/blog/"
    
    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        fg = FeedGenerator()
        fg.title('DeepMind Blog')
        fg.link(href=url, rel='alternate')
        fg.description('Latest posts from DeepMind Blog')
        fg.language('en')
        
        # Find all blog posts - try multiple selectors
        articles = []
        
        # Method 1: Look for article elements
        articles = soup.find_all('article')
        
        # Method 2: Look for cards/items with blog links
        if not articles:
            articles = soup.find_all(['div', 'section'], class_=re.compile(r'post|article|card|item|blog', re.I))
        
        # Method 3: Look for any links to blog posts
        if not articles:
            blog_links = soup.find_all('a', href=re.compile(r'/blog/'))
            # Get parent elements of blog links
            for link in blog_links:
                parent = link.parent
                if parent and parent not in articles:
                    articles.append(parent)
        
        # Method 4: Look for any elements containing blog post structure
        if not articles:
            articles = soup.find_all(['div', 'li'], attrs={'data-post-id': True}) or \
                      soup.find_all(['div', 'li'], class_=re.compile(r'entry|post', re.I))
        
        seen_links = set()
        count = 0
        
        for article in articles[:50]:  # Limit to 50 most recent
            link_elem = article.find('a', href=True) if article.name != 'a' else article
            if not link_elem or not link_elem.get('href'):
                continue
                
            article_url = link_elem['href']
            if not article_url.startswith('http'):
                article_url = f"https://deepmind.google{article_url}"
            
            if article_url in seen_links:
                continue
            seen_links.add(article_url)
            
            # Extract title
            title_elem = article.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'title|heading', re.I))
            if not title_elem:
                title_elem = link_elem.find(['h1', 'h2', 'h3', 'h4'])
            if not title_elem:
                title_elem = link_elem
            
            title = title_elem.get_text(strip=True) if title_elem else "Untitled"
            
            # Extract description
            desc_elem = article.find(['p', 'div'], class_=re.compile(r'description|excerpt|summary', re.I))
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # Extract date - try multiple methods
            pub_date = None
            
            # Method 1: Try to extract from article element on listing page
            pub_date = extract_date_from_element(article, article_url)
            # Ensure timezone is set
            if pub_date and pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            
            # Method 2: Always fetch the article page for accurate date (DeepMind blog has dates on article pages)
            try:
                article_response = requests.get(article_url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }, timeout=10)
                if article_response.status_code == 200:
                    article_soup = BeautifulSoup(article_response.content, 'html.parser')
                    
                    # Try multiple selectors for date on article page
                    date_selectors = [
                        ('time', {'datetime': True}),  # <time datetime="...">
                        ('time', {}),  # Any <time> element
                        ('span', {'class': re.compile(r'date|time|published|meta', re.I)}),
                        ('div', {'class': re.compile(r'date|time|published|meta', re.I)}),
                        ('p', {'class': re.compile(r'date|time|published|meta', re.I)}),
                        ('span', {'class': re.compile(r'byline|author', re.I)}),  # Sometimes date is in byline
                    ]
                    
                    for tag, attrs in date_selectors:
                        date_elem = article_soup.find(tag, attrs)
                        if date_elem:
                            # Try datetime attribute first
                            date_str = date_elem.get('datetime') or date_elem.get('data-date') or date_elem.get('title')
                            if date_str:
                                parsed = parse_date_string(date_str)
                                if parsed:
                                    if parsed.tzinfo is None:
                                        parsed = parsed.replace(tzinfo=timezone.utc)
                                    pub_date = parsed
                                    break
                            
                            # Try text content
                            date_text = date_elem.get_text(strip=True)
                            if date_text:
                                # Look for date patterns in text
                                parsed = parse_date_string(date_text)
                                if parsed:
                                    if parsed.tzinfo is None:
                                        parsed = parsed.replace(tzinfo=timezone.utc)
                                    pub_date = parsed
                                    break
                                
                                # Try to extract date from text like "Published: January 15, 2024"
                                date_match = re.search(r'(?:published|posted|date)[:\s]+([^,]+,\s*\d{4})', date_text, re.I)
                                if date_match:
                                    parsed = parse_date_string(date_match.group(1))
                                    if parsed:
                                        if parsed.tzinfo is None:
                                            parsed = parsed.replace(tzinfo=timezone.utc)
                                        pub_date = parsed
                                        break
                    
                    # If still no date, look for structured data (JSON-LD)
                    if not pub_date:
                        scripts = article_soup.find_all('script', type='application/ld+json')
                        for script in scripts:
                            try:
                                data = json.loads(script.string)
                                if isinstance(data, dict):
                                    # Check for datePublished
                                    if 'datePublished' in data:
                                        parsed = parse_date_string(data['datePublished'])
                                        if parsed:
                                            if parsed.tzinfo is None:
                                                parsed = parsed.replace(tzinfo=timezone.utc)
                                            pub_date = parsed
                                            break
                                    # Check nested structures
                                    if '@graph' in data:
                                        for item in data['@graph']:
                                            if isinstance(item, dict) and 'datePublished' in item:
                                                parsed = parse_date_string(item['datePublished'])
                                                if parsed:
                                                    if parsed.tzinfo is None:
                                                        parsed = parsed.replace(tzinfo=timezone.utc)
                                                    pub_date = parsed
                                                    break
                            except:
                                continue
                    
                    # If still no date, try to find date in article metadata or header
                    if not pub_date:
                        # Look in article header or meta tags
                        meta_date = article_soup.find('meta', property='article:published_time') or \
                                   article_soup.find('meta', attrs={'name': re.compile(r'date|published', re.I)})
                        if meta_date:
                            date_str = meta_date.get('content')
                            if date_str:
                                parsed = parse_date_string(date_str)
                                if parsed:
                                    if parsed.tzinfo is None:
                                        parsed = parsed.replace(tzinfo=timezone.utc)
                                    pub_date = parsed
            except Exception as e:
                # If fetching article page fails, continue with date from listing page
                pass
            
            # If still no date, use decreasing time offset for ordering (newest first)
            if not pub_date:
                # Use current time minus some offset based on position
                # Use days instead of hours for better spacing
                offset_days = count * 7  # Each entry is 7 days older
                pub_date = datetime.now(timezone.utc) - timedelta(days=offset_days)
            
            # Final check: ensure timezone is always set
            if pub_date and pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            
            # Create feed entry
            fe = fg.add_entry()
            fe.title(title)
            fe.link(href=article_url)
            fe.description(description)
            fe.pubDate(pub_date)
            
            count += 1
        
        if count == 0:
            # Fallback: try to find any links to blog posts
            all_links = soup.find_all('a', href=re.compile(r'/blog/'))
            for link in all_links[:20]:
                article_url = link['href']
                if not article_url.startswith('http'):
                    article_url = f"https://deepmind.google{article_url}"
                
                if article_url in seen_links:
                    continue
                seen_links.add(article_url)
                
                title = link.get_text(strip=True) or "DeepMind Blog Post"
                
                fe = fg.add_entry()
                fe.title(title)
                fe.link(href=article_url)
                fe.description("")
                # Use decreasing time for ordering
                fe.pubDate(get_fallback_date(count))
                count += 1
        
        # Write RSS feed
        fg.rss_file('feed_deepmind_blog.xml')
        print(f"Generated feed_deepmind_blog.xml with {count} entries")
        
    except Exception as e:
        print(f"Error generating DeepMind Blog feed: {e}")
        raise

if __name__ == "__main__":
    generate_feed()

