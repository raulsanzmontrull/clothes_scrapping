import unittest
from unittest.mock import patch, Mock
import sys
import os

# Import the function from src/get_all_products_links.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/links_getter')))
from get_all_products_links import get_valid_product_links

class TestGetValidProductLinks(unittest.TestCase):

    @patch('requests.get')
    def test_get_valid_product_links(self, mock_get):
        # Mock response for the main page
        mock_main_page_response = Mock()
        mock_main_page_response.status_code = 200
        mock_main_page_response.text = '''
        <html>
            <a href="/products/46283-harry-jacket-ss24-navy">Product 1</a>
            <a href="/products/47123-pasta-tee-ss24-mint">Product 2</a>
            <a href="/products/47123-pasta-tee-ss24-offwhite">Product 3</a>
        </html>
        '''
        
        # Mock response for product pages
        mock_product_response = Mock()
        mock_product_response.status_code = 200

        def side_effect(url, *args, **kwargs):
            if url == "https://en.gb.scalperscompany.com":
                return mock_main_page_response
            elif url in [
                "https://en.gb.scalperscompany.com/products/46283-harry-jacket-ss24-navy",
                "https://en.gb.scalperscompany.com/products/47123-pasta-tee-ss24-mint",
                "https://en.gb.scalperscompany.com/products/47123-pasta-tee-ss24-offwhite"
            ]:
                return mock_product_response
            return Mock(status_code=404)

        mock_get.side_effect = side_effect

        expected_urls = [
            "https://en.gb.scalperscompany.com/products/46283-harry-jacket-ss24-navy",
            "https://en.gb.scalperscompany.com/products/47123-pasta-tee-ss24-mint",
            "https://en.gb.scalperscompany.com/products/47123-pasta-tee-ss24-offwhite"
        ]

        result = get_valid_product_links()
        self.assertEqual(result, expected_urls)

    @patch('requests.get')
    def test_get_valid_product_links_with_custom_url(self, mock_get):
        custom_url = "http://custom-url.com"
        mock_main_page_response = Mock()
        mock_main_page_response.status_code = 200
        mock_main_page_response.text = '''
        <html>
            <a href="/products/46283-harry-jacket-ss24-navy">Product 1</a>
            <a href="/products/47123-pasta-tee-ss24-mint">Product 2</a>
            <a href="/products/47123-pasta-tee-ss24-offwhite">Product 3</a>
        </html>
        '''

        mock_product_response = Mock()
        mock_product_response.status_code = 200

        def side_effect(url, *args, **kwargs):
            if url == custom_url:
                return mock_main_page_response
            elif url in [
                custom_url + "/products/46283-harry-jacket-ss24-navy",
                custom_url + "/products/47123-pasta-tee-ss24-mint",
                custom_url + "/products/47123-pasta-tee-ss24-offwhite"
            ]:
                return mock_product_response
            return Mock(status_code=404)

        mock_get.side_effect = side_effect

        expected_urls = [
            custom_url + "/products/46283-harry-jacket-ss24-navy",
            custom_url + "/products/47123-pasta-tee-ss24-mint",
            custom_url + "/products/47123-pasta-tee-ss24-offwhite"
        ]

        result = get_valid_product_links(custom_url)
        self.assertEqual(result, expected_urls)

    @patch('requests.get')
    def test_get_valid_product_links_with_invalid_url(self, mock_get):
        mock_get.return_value = Mock(status_code=404)

        with self.assertRaises(ValueError) as context:
            get_valid_product_links("http://invalid-url.com")

        self.assertIn("Failed to fetch the main page", str(context.exception))

    @patch('requests.get')
    def test_main_with_invalid_url(self, mock_get):
        mock_get.return_value = Mock(status_code=404)

        with self.assertRaises(ValueError) as context:
            get_valid_product_links("http://invalid-url.com")

        self.assertIn("Failed to fetch the main page", str(context.exception))

if __name__ == "__main__":
    unittest.main()

