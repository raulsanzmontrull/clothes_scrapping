import unittest
from unittest.mock import patch, Mock
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app/modules')))

from get_all_products_from_collection import get_all_product_details

class TestGetAllProductDetails(unittest.TestCase):

    @patch('get_all_products_from_collection.get_product_links_from_page')
    def test_get_all_product_details(self, mock_get_product_links_from_page):
        mock_collection_url = "https://en.gb.scalperscompany.com/collections/women-new-collection"
        mock_product_links = [
            "https://en.gb.scalperscompany.com/products/12345-product-one",
            "https://en.gb.scalperscompany.com/products/67890-product-two"
        ]
        
        mock_get_product_links_from_page.return_value = mock_product_links

        result = get_all_product_details(mock_collection_url, validate_links=False)

        self.assertEqual(len(result), 2)
        self.assertIn('collection_url', result[0])
        self.assertEqual(result[0]['collection_url'], mock_collection_url)

if __name__ == '__main__':
    unittest.main()
