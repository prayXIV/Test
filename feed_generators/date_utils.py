"""
Utility functions for date parsing
"""

from datetime import datetime, timezone, timedelta
import re

def parse_date_string(date_str):
    """Try to parse a date string in various formats"""
    if not date_str:
        return None
    
    date_str = str(date_str).strip()
    
    # Try ISO format
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        pass
    
    # Try common date formats
    date_formats = [
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%B %d, %Y',  # January 15, 2024
        '%b %d, %Y',  # Jan 15, 2024
        '%d %B %Y',   # 15 January 2024
        '%d %b %Y',   # 15 Jan 2024
        '%m/%d/%Y',   # 01/15/2024
        '%d/%m/%Y',   # 15/01/2024
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    
    return None

def extract_date_from_element(element, url=None):
    """Extract date from HTML element using multiple methods"""
    pub_date = None
    
    # Method 1: Look for time/date elements with various class names
    date_elem = element.find(['time', 'span', 'div', 'p'], class_=re.compile(r'date|time|published|timestamp|meta', re.I))
    if date_elem:
        date_str = date_elem.get('datetime') or date_elem.get('title') or date_elem.get_text(strip=True)
        if date_str:
            pub_date = parse_date_string(date_str)
    
    # Method 2: Look for date in parent or sibling elements
    if not pub_date:
        parent = element.parent if hasattr(element, 'parent') else None
        if parent:
            date_elem = parent.find(['time', 'span', 'div'], class_=re.compile(r'date|time|published', re.I))
            if date_elem:
                date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
                if date_str:
                    pub_date = parse_date_string(date_str)
    
    # Method 3: Try to extract date from URL (e.g., /blog/2024/01/article)
    if not pub_date and url:
        url_date_match = re.search(r'/(\d{4})/(\d{1,2})/', url)
        if url_date_match:
            year, month = url_date_match.groups()
            try:
                pub_date = datetime(int(year), int(month), 1, tzinfo=timezone.utc)
            except:
                pass
    
    # Method 4: Look for any text that looks like a date
    if not pub_date:
        element_text = element.get_text()
        # Look for patterns like "January 15, 2024" or "2024-01-15"
        date_patterns = [
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
            r'(\w+)\s+(\d{1,2}),\s+(\d{4})',  # Month DD, YYYY
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
        ]
        for pattern in date_patterns:
            match = re.search(pattern, element_text)
            if match:
                try:
                    if '-' in match.group(0):
                        year, month, day = match.groups()
                        pub_date = datetime(int(year), int(month), int(day), tzinfo=timezone.utc)
                    elif '/' in match.group(0):
                        month, day, year = match.groups()
                        pub_date = datetime(int(year), int(month), int(day), tzinfo=timezone.utc)
                    else:
                        # Month DD, YYYY format
                        month_names = {
                            'january': 1, 'february': 2, 'march': 3, 'april': 4,
                            'may': 5, 'june': 6, 'july': 7, 'august': 8,
                            'september': 9, 'october': 10, 'november': 11, 'december': 12
                        }
                        month_str, day, year = match.groups()
                        month = month_names.get(month_str.lower(), 1)
                        pub_date = datetime(int(year), month, int(day), tzinfo=timezone.utc)
                    break
                except:
                    continue
    
    # Ensure timezone is set
    if pub_date and pub_date.tzinfo is None:
        pub_date = pub_date.replace(tzinfo=timezone.utc)
    
    return pub_date

def get_fallback_date(offset_hours=0):
    """Get a fallback date with optional offset for ordering"""
    return datetime.now(timezone.utc) - timedelta(hours=offset_hours)

