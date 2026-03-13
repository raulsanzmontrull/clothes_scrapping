import unittest
from unittest.mock import patch, Mock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/links_getter')))
from get_product_links_from_page import get_product_links_from_page

class TestGetProductLinksFromPage(unittest.TestCase):

    @patch('requests.get')
    def test_get_product_links_from_page(self, mock_get):
        mock_main_page_response = Mock()
        mock_main_page_response.status_code = 200
        mock_main_page_response.text = '''
        <html>
            <a class="ProductItem__ImageWrapper ProductItem__ImageWrapper--withAlternateImage" href="/products/46283-harry-jacket-ss24-navy">Product 1</a>
            <a class="ProductItem__ImageWrapper ProductItem__ImageWrapper--withAlternateImage" href="/products/47123-pasta-tee-ss24-mint">Product 2</a>
            <a class="ProductItem__ImageWrapper ProductItem__ImageWrapper--withAlternateImage" href="/products/47123-pasta-tee-ss24-offwhite">Product 3</a>
        </html>
        '''

        mock_product_response = Mock()
        mock_product_response.status_code = 200

        def side_effect(url, *args, **kwargs):
            if url == "https://en.gb.scalperscompany.com/collections/woman-new-collection-skirts-2060":
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

        result = get_product_links_from_page("https://en.gb.scalperscompany.com/collections/woman-new-collection-skirts-2060", validate=False)
        self.assertEqual(result, expected_urls)

    @patch('requests.get')
    def test_get_product_links_from_page_with_invalid_url(self, mock_get):
        mock_get.return_value = Mock(status_code=404)

        with self.assertRaises(ValueError) as context:
            get_product_links_from_page("http://invalid-url.com")

        self.assertIn("Failed to fetch the provided URL", str(context.exception))

if __name__ == "__main__":
    unittest.main()
