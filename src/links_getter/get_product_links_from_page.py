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
    product_links = list(filter(None, map(
        lambda x:
            "https://en.gb.scalperscompany.com" + x.get("href")
            if x.get("class") == ['ProductItem__ImageWrapper', 'ProductItem__ImageWrapper--withAlternateImage']
            else None, 
        soup.find_all("a")
    )))
    valid_product_links = list(filter(None, map(
        lambda x: None if requests.get(x).status_code != 200 else x, 
        product_links
    )))

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
