# Clothes Scraping

A web scraping project for extracting product data from the Scalpers e-commerce website. This tool collects product information including names, prices, images, sizes, and colours from clothing collections.

## Overview

This project provides a complete pipeline for scraping clothing product data:

- **Product Links Getter**: Extracts product URLs from collection pages and shop homepages
- **Scraper**: Scrapes detailed product information including metadata, images, prices, sizes, and colours
- **Collection Processor**: Processes all products from a single collection or entire shop

## Features

- Extract product links from collection pages
- Scrape detailed product information (name, SKU, images, prices, sizes, colours)
- Multi-currency price conversion (EUR, GBP, USD)
- Support for scraping entire collections or the full shop

## Project Structure

```
.
├── app/
│   └── modules/
│       ├── get_all_products_from_collection.py
│       └── get_all_products_from_shop.py
├── schema/
│   └── product.py
├── src/
│   ├── links_getter/
│   │   ├── get_all_collection_links.py
│   │   ├── get_all_products_links.py
│   │   └── get_product_links_from_page.py
│   ├── scrapper/
│   │   └── scrap.py
│   └── test/
│       └── get_link_first_product.py
├── tests/
│   └── ...
├── infra/
│   └── get_last_price.sh
├── Dockerfile
├── Makefile
├── pyproject.toml
└── requirements.txt
```

## Installation

```bash
# Using pip
pip install -r requirements.txt

# Using Poetry
poetry install
```

## Usage

### Get All Collections from Shop

```bash
python3 -m src.links_getter.get_all_collection_links
```

### Get Product Links from a Collection

```bash
python3 -m src.links_getter.get_product_links_from_page "https://en.gb.scalperscompany.com/collections/new-in-woman-2001"
```

### Scrape a Single Product

```bash
python3 -m src.scrapper.scrap "https://en.gb.scalperscompany.com/products/65321-sccollar-bomber-jacket-ss26-red"
```

### Scrape All Products from a Collection

```bash
python3 -m app.modules.get_all_products_from_collection "https://en.gb.scalperscompany.com/collections/new-in-woman-2001"
```

### Scrape All Products from Shop

```bash
python3 -m app.modules.get_all_products_from_shop "https://en.gb.scalperscompany.com/"
```

## Important Notes

### Rate Limiting

The website may block requests if you make too many requests too quickly. If you get `429 Too Many Requests` errors:
- Add delays between requests
- Consider using the scripts during off-peak hours
- The scraper validates each product URL which doubles the requests

### Performance

- **Single product**: ~2 seconds
- **Collection**: Depends on number of products (10-100+)
- **Full shop**: Can take hours due to thousands of products

### Saving Output to File

```bash
# Save products from a collection to JSON file
python3 -m app.modules.get_all_products_from_collection "URL" > products.json

# Save all products from shop to JSON file
python3 -m app.modules.get_all_products_from_shop > all_products.json
```

## Output Format

The scraper outputs JSON with the following structure:

```json
{
  "product_url": "https://en.gb.scalperscompany.com/products/40459-bach-dress-aw2324-black",
  "product_name": "MIDI DRESS WITH LUREX PAISLEY",
  "sku": "8445279630145",
  "metadata": [
    "Made of flowing fabric with metallic yarn detailing",
    "Regular fit",
    "V-neck"
  ],
  "images": [
    "https://en.gb.scalperscompany.com/cdn/shop/files/..."
  ],
  "currency": "GBP (£)",
  "date_time_of_conversion": "2024-07-07 12:35:31",
  "price_in_EUR": 94.2,
  "price_in_GBP": 79.9,
  "price_in_USD": 102.24,
  "sizes": ["XS", "S", "M", "L"],
  "colours": ["BLACK"]
}
```

## Running Tests

```bash
# Using Make
make test

# Or directly
python3 -m unittest discover -s tests -v
```

## Docker

```bash
# Build the image
docker build -t clothes-scraper .

# Run the container
docker run clothes-scraper
```

## Makefile Commands

```bash
# Local development (without Docker)
make scrape-product url="URL"           # Scrape single product
make scrape-collection-links url="URL"  # Get product links from collection
make scrape-collections                # Get all collections from shop
make scrape-first-product              # Get first product link
make scrape-collection-products url="URL" # Scrape all products from collection
make scrape-shop-products              # Scrape all products from shop
make test                              # Run all tests

# Docker commands
make build                             # Build Docker image
make up                                # Start container
make run url="URL"                     # Run scraper in container
make run_tests                         # Run tests in container
```

## Requirements

- Python 3.8+
- BeautifulSoup4
- Requests
- Pydantic

See `requirements.txt` for full dependencies.
