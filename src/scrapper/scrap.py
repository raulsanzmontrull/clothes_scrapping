"""
Product scraping module for extracting detailed information from e-commerce product pages.
Uses BeautifulSoup to parse HTML and extract product metadata, images, prices, sizes, and colors.
"""

import re
import requests
from bs4 import BeautifulSoup
import argparse
import json
import subprocess
from datetime import datetime


# Mapping of CSS class names to HTML tags for data extraction
class_to_tag = {
    'ProductMeta__Title': 'h1',
    'ProductMeta__SkuNumber': 'span',
    'ProductMeta__Description': 'div',
    'img': 'img',
    'ProductMeta__Price': 'span',
    'sizes': 'option',
    'colours': 'option'
}


# Mapping of CSS class names to output dictionary keys
class_to_key = {
    'ProductMeta__Title': 'product_name',
    'ProductMeta__SkuNumber': 'sku',
    'ProductMeta__Description': 'metadata',
    'img': 'images',
    'ProductMeta__Price': 'price',
    'sizes': 'sizes',
    'colours': 'colours'
}

google_finance_url = "https://www.google.com/finance/quote/"


def symbol_to_code(symbol):
    """
    Convert currency symbols to ISO currency codes.
    
    Args:
        symbol: Currency symbol (e.g., '€', '$', '£')
    
    Returns:
        ISO currency code (e.g., 'EUR', 'USD', 'GBP')
    """
    currency_map = {
        "€": "EUR",
        "$": "USD",
        "£": "GBP",
        "¥": "JPY",
        "₹": "INR",
        "CHF": "CHF",
        "₩": "KRW",
        "C$": "CAD",
        "A$": "AUD",
        "NZ$": "NZD",
        "HK$": "HKD",
        "kr": "SEK",
        "R$": "BRL",
        "₽": "RUB",
        "₪": "ILS",
        "₫": "VND",
        "₺": "TRY",
        "lei": "RON",
        "₦": "NGN",
        "฿": "THB",
        "₵": "GHS",
        "₭": "LAK",
        "MK": "MWK",
        "P": "PHP"
    }
    
    return currency_map.get(symbol, symbol)


def get_last_price(url):
    """
    Fetch the latest currency exchange rate using an external bash script.
    
    Args:
        url: Google Finance URL for currency pair conversion
    
    Returns:
        Exchange rate as float, or None if the request fails
    """
    script_path = './infra/get_last_price.sh'
    
    result = subprocess.run(['bash', script_path, url], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Error occurred:")
        print(result.stderr)
        return None
    
    try:
        price = float(result.stdout.strip())
    except ValueError:
        print("Failed to convert the output to float")
        return None

    return price


def split_currency_amount(s):
    """
    Parse a price string and convert to multiple currencies.
    
    Args:
        s: Price string (e.g., '£79.99', '€94.20')
    
    Returns:
        Dictionary containing currency code, converted prices, and conversion timestamp
    """
    currency = ''.join(filter(
        lambda char: not char.isdigit() and char != '.',
        s
    )).replace(" ", "")
    code_currency = symbol_to_code(currency)
    amount = float(''.join(filter(
        lambda char: char.isdigit() or char == '.',
        s
    )))
    
    target_currencies = ["EUR", "GBP", "USD"]
    
    currency_dict = {
        'currency': code_currency + " (" + currency + ")",
        'date_time_of_conversion': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    add_price = lambda target_currency: (
        f"price_in_{target_currency}", 
        round(amount, 2) if code_currency == target_currency else round(amount * get_last_price(google_finance_url + code_currency + "-" + target_currency), 2)
    )
    
    currency_dict.update(dict(map(add_price, target_currencies)))
    return currency_dict

size_order = ["XXXS", "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"]
size_index = dict(map(lambda x: (x[1], x[0]), enumerate(size_order)))
size_pattern = re.compile(r'\b(?:XXXS|XXS|XS|S|M|L|XL|XXL|XXXL)\b')


def sort_sizes(sizes):
    """
    Sort sizes according to standard clothing size order.
    
    Args:
        sizes: List of size strings
    
    Returns:
        Sorted list of sizes
    """
    size_index = dict(map(
        lambda x: (x[1], x[0]),
        enumerate(size_order)
    ))
    return sorted(
        sizes, key=lambda size: size_index.get(size, len(size_order))
    )


def extract_images(soup):
    """
    Extract product images from the page HTML.
    
    Args:
        soup: BeautifulSoup object of the product page
    
    Returns:
        List of image URLs
    """
    list_items = soup.find_all('img')
    product_name = soup.find('h1', class_='ProductMeta__Title').text.strip()
    matching_images_0 = list(filter(None, map(
        lambda x: x.get('data-original-src')
            if x.get('alt') == product_name
            else '', 
        list_items
    )))
    matching_images_1 = list(filter(None, map(
        lambda x: x.get('src')
            if x.get('alt') == product_name
            else '', 
        list_items
    )))
    matching_images = matching_images_0 + matching_images_1
    return list(map(lambda x: 'https:' + x, matching_images))


def extract_sizes(soup):
    """
    Extract available sizes from the product page.
    
    Args:
        soup: BeautifulSoup object of the product page
    
    Returns:
        List of available sizes, sorted by standard order
    """
    options = soup.find_all('option')
    sizes = filter(None, map(
        lambda x: size_pattern.search(x.text.strip()).group(0)
            if size_pattern.search(x.text.strip())
            else '',
            options
        ))
    return sort_sizes(list(set(sizes)))


def extract_colours(soup):
    """
    Extract available colours from the product page.
    
    Args:
        soup: BeautifulSoup object of the product page
    
    Returns:
        List of available colours
    """
    options = soup.find_all('option')
    colours = filter(None, map(
        lambda x: x.text.split(' - ')[0].strip().split('/')[0].strip()
            if size_pattern.search(x.text.strip())
            else '',
            options
        ))
    return list(set(colours))


def extract_list_items(element):
    """
    Extract list items from an HTML element.
    
    Args:
        element: BeautifulSoup element containing list items
    
    Returns:
        List of text content from list items
    """
    return list(map(
        lambda item: item.get_text(strip=True),
        element.find_all('li')
    ))


def extract_data(soup, class_name):
    """
    Extract data from the page using CSS class names.
    
    Args:
        soup: BeautifulSoup object of the product page
        class_name: CSS class name to search for
    
    Returns:
        Extracted data (string, list, or empty string)
    """
    tag_name = class_to_tag.get(class_name)

    special_cases = {
        'img': lambda: extract_images(soup),
        'sizes': lambda: extract_sizes(soup),
        'colours': lambda: extract_colours(soup)
    }
    
    if class_name in special_cases:
        return special_cases[class_name]()

    element = soup.find(tag_name, class_=class_name)

    if element:
        try:
            list_items = extract_list_items(element)
            return list_items if list_items else element.get_text(strip=True)
        except Exception:
            return element.get_text(strip=True)
    return ""


def scrape_product(url):
    """
    Scrape complete product information from a product page.
    
    Args:
        url: URL of the product page
    
    Returns:
        JSON string containing product details
    """
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to fetch the webpage. Status code: {response.status_code}")
        return {}

    soup = BeautifulSoup(response.text, 'html.parser')
    data_dict = {"product_url": url}

    details_div = soup.select_one('.Collapsible.Collapsible--large .Collapsible__Content')

    for class_name in class_to_tag:
        data = extract_data(soup, class_name)
        if data and class_name == "ProductMeta__Price":
            update_data_dict = lambda d, u: d.update(u)
            data_dict_prices = split_currency_amount(data)
            for key, value in data_dict_prices.items():
                update_data_dict(data_dict, {key: value})
            continue
        if data:
            data_dict[class_to_key[class_name]] = data

    return json.dumps(data_dict)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape product data from a URL.')
    parser.add_argument('url', type=str, help='The URL of the product page to scrape')

    args = parser.parse_args()

    product_data = scrape_product(args.url)
    print(product_data)
