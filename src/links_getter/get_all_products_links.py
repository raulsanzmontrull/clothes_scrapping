"""
Module for extracting all product links from a shop's homepage.
"""

import re
import requests
from bs4 import BeautifulSoup

def get_valid_product_links(url="https://en.gb.scalperscompany.com"):
    """
    Extract all valid product URLs from a shop homepage.
    
    Args:
        url: Base URL of the shop (default: Scalpers homepage)
    
    Returns:
        Sorted list of valid product URLs
    """
    valid_urls = []
    
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch the main page. Status code: {response.status_code}")
    soup = BeautifulSoup(response.text, 'html.parser')
    a_href_list = list(map(lambda x: x.get("href"), soup.find_all("a")))
    products_list = [href for href in a_href_list if href and href.startswith("/products")]

    for product_url in products_list:
        full_url = url + product_url if product_url.startswith('/') else url + '/' + product_url
        product_response = requests.get(full_url)
        if product_response.status_code == 200:
            valid_urls.append(full_url)
    
    return sorted(list(set(valid_urls)))

if __name__ == "__main__":
    urls = get_valid_product_links()  # You can pass a custom URL here if needed
    if urls:
        for valid_url in urls:
            print(valid_url)
    else:
        raise ValueError("No valid product URLs found")

