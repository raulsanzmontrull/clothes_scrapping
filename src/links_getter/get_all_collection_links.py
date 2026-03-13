"""
Module for extracting collection links from a shop homepage.
"""

import requests
from bs4 import BeautifulSoup
import argparse


def get_collection_from_shop(url="https://en.gb.scalperscompany.com"):
    """
    Extract all valid collection URLs from a shop homepage.
    
    Args:
        url: Base URL of the shop (default: Scalpers homepage)
    
    Returns:
        Sorted list of valid collection URLs
    """
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch the provided URL. Status code: {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    pre_collection_urls = list(set(list(filter(None, map(
        lambda x:
          x.get("href"),
          soup.find_all("a")
    )))))
    collection_urls = list(filter(None, map(
        lambda x: 
          url.rstrip('/') + x if x.startswith("/collections/") else None, 
          pre_collection_urls
    )))
    valid_collection_urls = list(filter(None, map(
        lambda x: 
          None if requests.get(x).status_code != 200 else x, 
          collection_urls
    )))

    return sorted(list(set(valid_collection_urls)))
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape product data from a URL.')
    parser.add_argument('url', type=str, nargs='?', default='https://en.gb.scalperscompany.com', help='The URL of the product page to scrape')

    args = parser.parse_args()
    
    urls = get_collection_from_shop(args.url)
    if urls:
        for valid_url in urls:
            print(valid_url)
    else:
        raise ValueError("No valid product URLs found")
