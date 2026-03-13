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


# Mapping of CSS class names to HTML tags for data extraction (new website structure)
class_to_tag = {
    'title-h3': 'h1',
    'sku': 'span',
    'description': 'div',
    'img': 'img',
    'price': 'span',
    'sizes': 'option',
    'colours': 'option'
}


# Mapping of CSS class names to output dictionary keys
class_to_key = {
    'title-h3': 'product_name',
    'sku': 'sku',
    'description': 'metadata',
    'img': 'images',
    'price': 'price',
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


def extract_images(soup, product_name="", url=""):
    """
    Extract product images from the page HTML.
    
    Args:
        soup: BeautifulSoup object of the product page
        product_name: Name of the product to filter images
    
    Returns:
        List of image URLs
    """
    images = []
    seen = set()
    
    # Extract product code from URL if available
    product_code = ""
    if url:
        url_match = re.search(r'/products/[a-z0-9-]+-(\d+)(?:\?|$)', url)
        if url_match:
            product_code = url_match.group(1)
    
    # If we don't have product_name yet, try to get it from h1
    if not product_name:
        title_elem = soup.find('h1', class_='ProductMeta__Title')
        if title_elem:
            product_name = title_elem.get_text(strip=True)
    
    # Helper function to check if image is relevant
    def is_relevant_image(src):
        if not src or 'cdn/shop/files' not in src:
            return False
        # Must have product code pattern: ####-COLOR-P-# or ####-COLOR-S-#
        if product_code and product_code in src:
            return True
        # Fallback: match by alt text
        if product_name:
            alt = ''
            # Find the img element with this src to check alt
            for img in soup.find_all('img'):
                if img.get('src') == src or img.get('data-original-src') == src:
                    alt = img.get('alt', '').strip()
                    break
            if alt == product_name:
                return True
        return False
    
    # First: get images from data-original-src (these are the primary images)
    old_images = soup.find_all('img', {'data-original-src': True})
    for img in old_images:
        src = img.get('data-original-src')
        if is_relevant_image(src):
            src = re.sub(r'_\{width\}x\.jpg', '.jpg', src)
            src_clean = src.split('?')[0]
            if src_clean not in seen:
                seen.add(src_clean)
                images.append('https:' + src if src.startswith('//') else src)
    
    # Second: also get images from src attribute (includes _250x, _800x variants)
    # Only for product images matching the product code or alt text
    all_imgs = soup.find_all('img')
    for img in all_imgs:
        src = img.get('src')
        if not src:
            continue
        
        if is_relevant_image(src):
            # Clean up
            src = re.sub(r'_\{width\}x\.jpg', '.jpg', src)
            src_clean = src.split('?')[0]
            
            if src_clean not in seen:
                seen.add(src_clean)
                full_url = 'https:' + src if src.startswith('//') else src
                images.append(full_url)
    
    return images[:20] if images else []


def extract_sizes(soup):
    """
    Extract available sizes from the product page.
    
    Args:
        soup: BeautifulSoup object of the product page
    
    Returns:
        List of available sizes, sorted by standard order
    """
    sizes = []
    
    # Try old website structure first
    options = soup.find_all('option')
    for opt in options:
        text = opt.text.strip()
        match = size_pattern.search(text.upper())
        if match:
            size = match.group(0)
            if size:
                sizes.append(size)
    
    if sizes:
        return sort_sizes(list(set(sizes)))
    
    # Try new website structure - look for size options in form inputs or labels
    size_elements = soup.find_all(['input', 'label', 'button'], 
                                   {'class': lambda x: x and 'size' in x.lower() if x else False})
    
    for elem in size_elements:
        text = elem.get('value') or elem.text.strip()
        match = size_pattern.search(text.upper())
        if match:
            size = match.group(0)
            if size:
                sizes.append(size)
    
    # Fallback: look for size in data attributes
    if not sizes:
        all_options = soup.find_all('option')
        for opt in all_options:
            text = opt.text.strip()
            match = size_pattern.search(text.upper())
            if match:
                size = match.group(0)
                if size:
                    sizes.append(size)
    
    return sort_sizes(list(set(sizes)))


def extract_colours(soup):
    """
    Extract available colours from the product page.
    
    Args:
        soup: BeautifulSoup object of the product page
    
    Returns:
        List of available colours
    """
    colours = []
    
    # Try old website structure first (format: "COLOR - Size")
    options = soup.find_all('option')
    for opt in options:
        text = opt.text.strip()
        match = size_pattern.search(text.upper())
        if match:
            # Extract colour from the beginning
            color_part = text.split('-')[0].strip().split('/')[0].strip()
            if color_part and color_part.upper() not in [s.upper() for s in size_order]:
                colours.append(color_part.upper())
    
    if colours:
        return list(set(colours))
    
    # Try new website structure - look for color options
    color_elements = soup.find_all(['input', 'label', 'button'], 
                                    {'class': lambda x: x and ('color' in x.lower() or 'colour' in x.lower()) if x else False})
    
    size_list = extract_sizes(soup)  # Get sizes to avoid including them as colours
    
    for elem in color_elements:
        value = elem.get('value') or elem.get('data-color') or elem.text.strip()
        if value and value.upper() not in [s.upper() for s in size_list]:
            color_match = re.match(r'^([A-Z]+)', value.upper())
            if color_match:
                colours.append(color_match.group(1))
    
    # Fallback: look for color swatches or color names
    if not colours:
        color_elements = soup.find_all(['span', 'div', 'li'], 
                                       {'class': lambda x: x and ('color' in x.lower() or 'swatch' in x.lower()) if x else False})
        for elem in color_elements:
            text = elem.text.strip()
            color_match = re.match(r'^([A-Z]+)', text.upper())
            if color_match and len(color_match.group(1)) > 1:
                colours.append(color_match.group(1))

    return list(set(colours))
    
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


def extract_data(soup, class_name, url=""):
    """
    Extract data from the page using CSS class names.
    Supports both old and new website structures.
    
    Args:
        soup: BeautifulSoup object of the product page
        class_name: CSS class name to search for
        url: URL of the product page (for SKU extraction)
    
    Returns:
        Extracted data (string, list, or empty string)
    """
    tag_name = class_to_tag.get(class_name)

    # First, extract product name to use for filtering other data
    product_name = ""
    # Try old structure first
    title_elem = soup.find('h1', class_='ProductMeta__Title')
    if not title_elem:
        # Try new structure
        title_elem = soup.find('h1', class_='title-h3')
    if not title_elem:
        title_elem = soup.find('h1', class_=lambda x: x and 'title' in x.lower() if x else False)
    if title_elem:
        product_name = title_elem.get_text(strip=True)

    special_cases = {
        'img': lambda: extract_images(soup, product_name, url),
        'sizes': lambda: extract_sizes(soup),
        'colours': lambda: extract_colours(soup)
    }
    
    if class_name in special_cases:
        return special_cases[class_name]()

    # Handle special class names with different selectors
    if class_name == 'title-h3':
        # Try new structure first, then old
        element = soup.find('h1', class_='title-h3')
        if not element:
            element = soup.find('h1', class_='ProductMeta__Title')
        if not element:
            element = soup.find('h1', class_=lambda x: x and 'title' in x.lower() if x else False)
        if element:
            return element.get_text(strip=True)
        return ""
    
    if class_name == 'price':
        # Try new structure first - look for price in various elements
        price_elem = soup.find(class_=lambda x: x and 'price' in x.lower() if x else False)
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            # Extract price value
            price_match = re.search(r'[\£\€\$\¥]\s*[\d,]+\.?\d*', price_text)
            if price_match:
                return price_match.group(0)
            # Try to find any price value
            price_match = re.search(r'[\£\€\$\¥][\d,]+\.?\d*', price_text)
            if price_match:
                return price_match.group(0)
        
        # Try old structure
        price_elem = soup.find('span', class_='ProductMeta__Price')
        if price_elem:
            return price_elem.get_text(strip=True)
        
        return ""
    
    if class_name == 'sku':
        # Try new: extract from URL first
        url_match = re.search(r'/products/[a-z0-9-]+-(\d+)(?:\?|$)', url)
        if url_match:
            return url_match.group(1)
        url_match = re.search(r'/products/(\d+)', url)
        if url_match:
            return url_match.group(1)
        
        # Try old: look for SKU in page
        sku_elem = soup.find('span', class_='ProductMeta__SkuNumber')
        if sku_elem:
            return sku_elem.get_text(strip=True)
        
        # Try new: look for SKU in page
        sku_elem = soup.find(class_=lambda x: x and 'sku' in x.lower() if x else False)
        if sku_elem:
            return sku_elem.get_text(strip=True)
        return ""
    
    if class_name == 'description':
        # Try old structure first
        desc_elem = soup.find('div', class_='ProductMeta__Description')
        if desc_elem:
            text = desc_elem.get_text(strip=True)
            if text:
                return text
        
        # Try new structure - look for product description in various elements
        desc_selectors = [
            {'class': lambda x: x and 'description' in x.lower() if x else False},
            {'class': lambda x: x and 'detail' in x.lower() if x else False},
        ]
        
        for selector in desc_selectors:
            desc_elem = soup.find(**selector)
            if desc_elem:
                text = desc_elem.get_text(strip=True)
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                if lines and len(lines[0]) > 10:
                    return lines
        
        # Try looking for product info in structured data
        script_tags = soup.find_all('script', {'type': 'application/ld+json'})
        for script in script_tags:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if data.get('@type') == 'Product':
                        desc = data.get('description')
                        if desc:
                            return desc
            except:
                pass
        
        return ""

    # Default: try finding by class name
    element = soup.find(tag_name, class_=class_name)
    
    # Try old class names if not found
    if not element and class_name == 'ProductMeta__Title':
        element = soup.find('h1', class_='ProductMeta__Title')

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

    for class_name in class_to_tag:
        data = extract_data(soup, class_name, url)
        if data and class_name == "price":
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
