"""
Module for scraping all products from a single collection.
Uses concurrent processing for faster scraping.
"""

import sys
import os
import json
import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.links_getter.get_product_links_from_page import get_product_links_from_page
from src.scrapper.scrap import scrape_product
from src.utils.concurrent import ConcurrentScraper


def scrape_single_product(product_url: str, collection_url: str = None) -> dict:
    """
    Scrape a single product and add collection URL.
    
    Args:
        product_url: URL of the product
        collection_url: Optional collection URL to tag the product with
        
    Returns:
        Product details dictionary
    """
    try:
        product_details = scrape_product(product_url)
        if isinstance(product_details, str):
            product_details = json.loads(product_details)
        if collection_url:
            product_details['collection_url'] = collection_url
        return product_details
    except Exception as e:
        return {'url': product_url, 'error': str(e), 'collection_url': collection_url}


def get_all_product_details(collection_url: str, max_workers: int = 5, 
                            validate_links: bool = True) -> list:
    """
    Scrape detailed information for all products in a collection.
    Uses concurrent processing for faster scraping.
    
    Args:
        collection_url: URL of the product collection
        max_workers: Number of concurrent threads (default: 5)
        validate_links: Whether to validate product URLs before scraping
        
    Returns:
        List of product detail dictionaries
    """
    print(f"Getting product links from collection...")
    product_links = get_product_links_from_page(collection_url, validate=validate_links)
    
    if not product_links:
        print("No product links found")
        return []
    
    print(f"Scraping {len(product_links)} products with {max_workers} workers...")
    
    # Use concurrent scraper for parallel processing
    with ConcurrentScraper(max_workers=max_workers, timeout=30) as scraper:
        # First fetch all HTML content concurrently
        fetch_results = scraper.fetch_multiple(product_links)
        
        # Then scrape each successful response
        all_product_details = []
        for i, result in enumerate(fetch_results, 1):
            if result['status_code'] == 200 and result['content']:
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(result['content'], 'html.parser')
                    
                    # Import and use extract_data for each field
                    from src.scrapper.scrap import (
                        extract_data, class_to_tag, class_to_key, 
                        split_currency_amount
                    )
                    
                    # Extract product name first
                    product_name = ""
                    title_elem = soup.find('h1', class_='title-h3')
                    if not title_elem:
                        title_elem = soup.find('h1', class_='ProductMeta__Title')
                    if title_elem:
                        product_name = title_elem.get_text(strip=True)
                    
                    data_dict = {"product_url": result['url']}
                    
                    # Extract each field
                    for class_name in class_to_tag:
                        data = extract_data(soup, class_name, result['url'])
                        if data and class_name == "price":
                            data_dict_prices = split_currency_amount(data)
                            data_dict.update(data_dict_prices)
                            continue
                        if data:
                            data_dict[class_to_key[class_name]] = data
                    
                    data_dict['collection_url'] = collection_url
                    all_product_details.append(data_dict)
                    
                except Exception as e:
                    all_product_details.append({
                        'url': result['url'], 
                        'error': str(e),
                        'collection_url': collection_url
                    })
            else:
                all_product_details.append({
                    'url': result['url'], 
                    'error': result.get('error', 'Failed to fetch'),
                    'collection_url': collection_url
                })
            
            if i % 10 == 0:
                print(f"Progress: {i}/{len(product_links)}")
    
    print(f"Completed scraping {len(all_product_details)} products")
    return all_product_details


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape product details from a collection URL.')
    parser.add_argument('url', type=str, nargs='?', 
                       default='https://en.gb.scalperscompany.com/collections/women-new-collection', 
                       help='The collection URL to scrape')
    parser.add_argument('--workers', type=int, default=5, 
                       help='Number of concurrent workers (default: 5)')
    parser.add_argument('--no-validate', action='store_true', 
                       help='Skip URL validation')

    args = parser.parse_args()
    collection_url = args.url

    product_details = get_all_product_details(
        collection_url, 
        max_workers=args.workers,
        validate_links=not args.no_validate
    )
    
    for details in product_details:
        print(json.dumps(details, default=str))
