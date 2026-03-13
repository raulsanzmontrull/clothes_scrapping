"""
Utility module for extracting the first valid product link from a shop.
"""

import requests
from bs4 import BeautifulSoup


def get_first_product_link():
    """
    Get the first valid product URL from the shop homepage.
    
    Returns:
        First valid product URL or error message
    """
    url_to_shop = "https://en.gb.scalperscompany.com"
    response = requests.get(url_to_shop)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        a_href_list = list(map(lambda x: x.get("href"), soup.find_all("a")))
        products_list = [href for href in a_href_list if href and href.startswith("/products")]

        if products_list:
            for product_url in products_list:
                full_url = url_to_shop + product_url if product_url.startswith('/') else url_to_shop + '/' + product_url
                product_response = requests.get(full_url)
                if product_response.status_code == 200:
                    print(full_url)
                    break
            else:
                print("No products found")
    else:
        print(f"Failed to fetch the main page. Status code: {response.status_code}")


if __name__ == "__main__":
    get_first_product_link()

