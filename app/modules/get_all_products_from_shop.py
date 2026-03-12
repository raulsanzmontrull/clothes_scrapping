"""
Module for scraping all products from all collections in a shop.
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.modules.get_all_products_from_collection import get_all_product_details
from src.links_getter.get_all_collection_links import get_collection_from_shop


def get_all_products_recursively(collection_url="https://en.gb.scalperscompany.com/"):
    """
    Scrape all products from all collections in a shop.
    
    Args:
        collection_url: Base URL of the shop
    
    Returns:
        List of all product details from all collections
    """
    product_links = get_collection_from_shop(collection_url)
    all_product_details = []

    for product_url in product_links:
        details = get_all_product_details(product_url)
        all_product_details.extend(details)

    return all_product_details


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape all product details from a shop URL.")
    parser.add_argument(
        'url',
        type=str,
        nargs='?',
        default="https://en.gb.scalperscompany.com/",
        help='The shop URL to scrape'
    )
    
    args = parser.parse_args()
    collection_url = args.url

    all_details = get_all_products_recursively(collection_url)

    list(map(lambda details: print(details), all_details))
