"""
Module for scraping all products from a single collection.
"""

import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.links_getter.get_product_links_from_page import get_product_links_from_page
from src.scrapper.scrap import scrape_product


def get_all_product_details(collection_url):
    """
    Scrape detailed information for all products in a collection.
    
    Args:
        collection_url: URL of the product collection
    
    Returns:
        List of product detail dictionaries
    """
    product_links = get_product_links_from_page(collection_url)
    all_product_details = []

    for product_url in product_links:
        product_details = scrape_product(product_url)
        if isinstance(product_details, str):
            product_details = json.loads(product_details)
        product_details['collection_url'] = collection_url
        all_product_details.append(product_details)

    return all_product_details


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Scrape product details from a collection URL.')
    parser.add_argument('url', type=str, nargs='?', default='https://en.gb.scalperscompany.com/collections/women-new-collection', help='The collection URL to scrape')

    args = parser.parse_args()
    collection_url = args.url

    product_details = get_all_product_details(collection_url)
    
    list(map(lambda details: print(details), product_details))
