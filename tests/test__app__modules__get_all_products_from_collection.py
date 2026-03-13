import unittest
from unittest.mock import patch, Mock, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app/modules')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/links_getter')))

from get_product_links_from_page import extract_product_links_from_html


class TestGetAllProductDetails(unittest.TestCase):

    def test_extract_product_links_from_html(self):
        """Test that HTML extraction works correctly."""
        html = '''
        <html>
            <a href="/products/product-1">Product 1</a>
            <a href="/products/product-2">Product 2</a>
            <a href="/collections/some-collection">Collection</a>
        </html>
        '''
        result = extract_product_links_from_html(html, "https://example.com")
        self.assertEqual(len(result), 2)
        self.assertIn("https://example.com/products/product-1", result)
        self.assertIn("https://example.com/products/product-2", result)

    def test_extract_product_links_handles_query_params(self):
        """Test that query parameters are removed from URLs."""
        html = '''
        <html>
            <a href="/products/product-1?variant=123">Product 1</a>
        </html>
        '''
        result = extract_product_links_from_html(html, "https://example.com")
        self.assertEqual(len(result), 1)
        self.assertNotIn('?', result[0])
        self.assertIn("https://example.com/products/product-1", result)

    def test_extract_product_links_handles_relative_paths(self):
        """Test various href formats."""
        html = '''
        <html>
            <a href="/products/relative">Relative</a>
            <a href="https://other.com/products/absolute">Absolute</a>
        </html>
        '''
        result = extract_product_links_from_html(html, "https://example.com")
        self.assertEqual(len(result), 2)
        self.assertIn("https://example.com/products/relative", result)
        self.assertIn("https://other.com/products/absolute", result)


if __name__ == '__main__':
    unittest.main()
