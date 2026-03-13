"""
Module for extracting product links from a collection page.
"""

import re
import requests
from bs4 import BeautifulSoup
import argparse


def get_product_links_from_page(url):
    """
    Extract valid product URLs from a collection page.
    
    Args:
        url: URL of the collection page
    
    Returns:
        Sorted list of valid product URLs
    """
    valid_urls = []
    
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch the provided URL. Status code: {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Try new website structure first - look for product links in various ways
    # Method 1: Look for links with /products/ in href
    all_links = soup.find_all("a")
    product_links = []
    
    for link in all_links:
        href = link.get("href")
        if href and '/products/' in href:
            # Build full URL
            if href.startswith('/'):
                full_url = "https://en.gb.scalperscompany.com" + href
            elif href.startswith('http'):
                full_url = href
            else:
                full_url = "https://en.gb.scalperscompany.com/" + href
            
            # Clean URL (remove query params)
            if '?' in full_url:
                full_url = full_url.split('?')[0]
            
            if full_url not in product_links:
                product_links.append(full_url)
    
    # Verify links are valid (status 200)
    valid_product_links = []
    for product_url in product_links:
        try:
            product_response = requests.get(product_url, timeout=10)
            if product_response.status_code == 200:
                valid_product_links.append(product_url)
        except:
            continue

    return sorted(list(set(valid_product_links)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape product data from a URL.')
    parser.add_argument('url', type=str, help='The URL of the product page to scrape')

    args = parser.parse_args()
    
    urls = get_product_links_from_page(args.url)
    if urls:
        for valid_url in urls:
            print(valid_url)
    else:
        raise ValueError("No valid product URLs found")
