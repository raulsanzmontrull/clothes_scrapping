"""
Module for extracting product links from a collection page.
Uses concurrent processing for faster URL validation.
"""

import requests
from bs4 import BeautifulSoup
import argparse
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.utils.concurrent import ConcurrentScraper


BASE_URL = "https://en.gb.scalperscompany.com"


def extract_product_links_from_html(html: str, base_url: str = BASE_URL) -> list:
    """
    Extract product links from HTML content.
    
    Args:
        html: HTML content string
        base_url: Base URL for building full URLs
        
    Returns:
        List of unique product URLs
    """
    soup = BeautifulSoup(html, 'html.parser')
    all_links = soup.find_all("a")
    product_links = []
    
    for link in all_links:
        href = link.get("href")
        if href and '/products/' in href:
            if href.startswith('/'):
                full_url = base_url + href
            elif href.startswith('http'):
                full_url = href
            else:
                full_url = base_url + "/" + href
            
            if '?' in full_url:
                full_url = full_url.split('?')[0]
            
            if full_url not in product_links:
                product_links.append(full_url)
    
    return product_links


def get_product_links_from_page(url: str, max_workers: int = 10, validate: bool = True,
                                 _session: requests.Session = None) -> list:
    """
    Extract valid product URLs from a collection page.
    
    Args:
        url: URL of the collection page
        max_workers: Number of concurrent threads for validation
        validate: Whether to validate URLs (check status 200)
        _session: Optional session for testing purposes
    
    Returns:
        Sorted list of valid product URLs
    """
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch the provided URL. Status code: {response.status_code}")
    
    product_links = extract_product_links_from_html(response.text)
    
    if not validate:
        return sorted(list(set(product_links)))
    
    print(f"Found {len(product_links)} product links, validating with {max_workers} workers...")
    
    # Use provided session or create new one
    if _session:
        scraper = ConcurrentScraper(max_workers=max_workers, timeout=10)
        scraper.session = _session
        results = scraper.fetch_multiple(product_links)
    else:
        with ConcurrentScraper(max_workers=max_workers, timeout=10) as scraper:
            results = scraper.fetch_multiple(product_links)
    
    valid_product_links = [
        r['url'] for r in results 
        if r['status_code'] == 200
    ]
    
    print(f"Validated {len(valid_product_links)}/{len(product_links)} URLs")
    
    return sorted(list(set(valid_product_links)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape product links from a collection page.')
    parser.add_argument('url', type=str, help='The URL of the collection page')
    parser.add_argument('--workers', type=int, default=10, help='Number of concurrent workers (default: 10)')
    parser.add_argument('--no-validate', action='store_true', help='Skip URL validation (faster but may include invalid URLs)')
    
    args = parser.parse_args()
    
    urls = get_product_links_from_page(args.url, max_workers=args.workers, validate=not args.no_validate)
    if urls:
        for valid_url in urls:
            print(valid_url)
    else:
        raise ValueError("No valid product URLs found")
