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

### Scrape a Single Collection

```bash
python -m app.modules.get_all_products_from_collection "https://en.gb.scalperscompany.com/collections/woman-new-collection-skirts-2060"
```

### Scrape All Products from a Shop

```bash
python -m app.modules.get_all_products_from_shop "https://en.gb.scalperscompany.com/"
```

### Scrape a Single Product

```bash
python -m src.scrapper.scrap "https://en.gb.scalperscompany.com/products/bbcstudio24-50505-strapless-linen-dress-ss24-red"
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
pytest tests/
```

## Docker

```bash
# Build the image
docker build -t clothes-scraper .

# Run the container
docker run clothes-scraper
```

## Requirements

- Python 3.8+
- BeautifulSoup4
- Requests
- Pydantic

See `requirements.txt` for full dependencies.
