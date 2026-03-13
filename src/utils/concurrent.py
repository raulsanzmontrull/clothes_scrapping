"""
Concurrent processing utilities for faster web scraping.
Provides both ThreadPoolExecutor and asyncio-based solutions.
"""

import asyncio
import aiohttp
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Callable, Optional


DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}


class ConcurrentScraper:
    """
    Thread-based concurrent scraper using ThreadPoolExecutor.
    Uses requests.Session() for connection pooling.
    """
    
    def __init__(self, max_workers: int = 10, timeout: int = 30, headers: Dict[str, str] = None):
        """
        Initialize concurrent scraper.
        
        Args:
            max_workers: Maximum number of concurrent threads
            timeout: Request timeout in seconds
            headers: Optional custom headers (merged with defaults)
        """
        self.max_workers = max_workers
        self.timeout = timeout
        self.session = None
        self.headers = {**DEFAULT_HEADERS, **(headers or {})}
    
    def __enter__(self):
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()
    
    def fetch_url(self, url: str) -> Dict[str, Any]:
        """
        Fetch a single URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Dict with url, status_code, content, and error
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            return {
                'url': url,
                'status_code': response.status_code,
                'content': response.text if response.status_code == 200 else None,
                'error': None
            }
        except Exception as e:
            return {
                'url': url,
                'status_code': None,
                'content': None,
                'error': str(e)
            }
    
    def fetch_multiple(self, urls: List[str], 
                      progress_callback: Optional[Callable[[int, int], None]] = None) -> List[Dict[str, Any]]:
        """
        Fetch multiple URLs concurrently.
        
        Args:
            urls: List of URLs to fetch
            progress_callback: Optional callback(completed, total) for progress
            
        Returns:
            List of result dicts
        """
        results = []
        total = len(urls)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self.fetch_url, url): url for url in urls}
            
            for future in as_completed(future_to_url):
                result = future.result()
                results.append(result)
                
                if progress_callback:
                    progress_callback(len(results), total)
        
        return results
    
    def scrape_multiple(self, urls: List[str], 
                       scraper_func: Callable[[str, str], Any],
                       progress_callback: Optional[Callable[[int, int], None]] = None) -> List[Any]:
        """
        Scrape multiple URLs using a custom scraper function.
        
        Args:
            urls: List of URLs to scrape
            scraper_func: Function(url, html_content) -> result
            progress_callback: Optional callback(completed, total) for progress
            
        Returns:
            List of scraped results
        """
        results = []
        total = len(urls)
        
        # First fetch all HTML content concurrently
        fetch_results = self.fetch_multiple(urls)
        
        # Then apply scraper function to each successful response
        for result in fetch_results:
            if result['status_code'] == 200 and result['content']:
                try:
                    scraped = scraper_func(result['url'], result['content'])
                    results.append(scraped)
                except Exception as e:
                    results.append({'url': result['url'], 'error': str(e)})
            else:
                results.append({'url': result['url'], 'error': result.get('error', 'Failed to fetch')})
            
            if progress_callback:
                progress_callback(len(results), total)
        
        return results


class AsyncScraper:
    """
    Async scraper using aiohttp for high-performance concurrent scraping.
    """
    
    def __init__(self, max_concurrent: int = 20, timeout: int = 30, headers: Dict[str, str] = None):
        """
        Initialize async scraper.
        
        Args:
            max_concurrent: Maximum number of concurrent requests
            timeout: Request timeout in seconds
            headers: Optional custom headers (merged with defaults)
        """
        self.max_concurrent = max_concurrent
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.semaphore = None
        self.session = None
        self.headers = {**DEFAULT_HEADERS, **(headers or {})}
    
    async def __aenter__(self):
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        self.session = aiohttp.ClientSession(timeout=self.timeout, headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_url(self, url: str) -> Dict[str, Any]:
        """
        Fetch a single URL asynchronously.
        
        Args:
            url: URL to fetch
            
        Returns:
            Dict with url, status_code, content, and error
        """
        async with self.semaphore:
            try:
                async with self.session.get(url) as response:
                    content = await response.text() if response.status == 200 else None
                    return {
                        'url': url,
                        'status_code': response.status,
                        'content': content,
                        'error': None
                    }
            except asyncio.TimeoutError:
                return {
                    'url': url,
                    'status_code': None,
                    'content': None,
                    'error': 'Timeout'
                }
            except Exception as e:
                return {
                    'url': url,
                    'status_code': None,
                    'content': None,
                    'error': str(e)
                }
    
    async def fetch_multiple_async(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch multiple URLs concurrently.
        
        Args:
            urls: List of URLs to fetch
            
        Returns:
            List of result dicts
        """
        tasks = [self.fetch_url(url) for url in urls]
        return await asyncio.gather(*tasks)
    
    def fetch_multiple(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch multiple URLs (sync wrapper).
        
        Args:
            urls: List of URLs to fetch
            
        Returns:
            List of result dicts
        """
        return asyncio.run(self.fetch_multiple_async(urls))
    
    async def scrape_multiple_async(self, urls: List[str], 
                                    scraper_func: Callable[[str, str], Any]) -> List[Any]:
        """
        Scrape multiple URLs asynchronously.
        
        Args:
            urls: List of URLs to scrape
            scraper_func: Async function(url, html_content) -> result
            
        Returns:
            List of scraped results
        """
        fetch_results = await self.fetch_multiple_async(urls)
        
        results = []
        for result in fetch_results:
            if result['status_code'] == 200 and result['content']:
                try:
                    if asyncio.iscoroutinefunction(scraper_func):
                        scraped = await scraper_func(result['url'], result['content'])
                    else:
                        scraped = scraper_func(result['url'], result['content'])
                    results.append(scraped)
                except Exception as e:
                    results.append({'url': result['url'], 'error': str(e)})
            else:
                results.append({'url': result['url'], 'error': result.get('error', 'Failed to fetch')})
        
        return results
    
    def scrape_multiple(self, urls: List[str], 
                        scraper_func: Callable[[str, str], Any]) -> List[Any]:
        """
        Scrape multiple URLs (sync wrapper).
        
        Args:
            urls: List of URLs to scrape
            scraper_func: Function(url, html_content) -> result
            
        Returns:
            List of scraped results
        """
        return asyncio.run(self.scrape_multiple_async(urls, scraper_func))


def parallel_map(func: Callable, items: List[Any], max_workers: int = 10) -> List[Any]:
    """
    Simple parallel map using ThreadPoolExecutor.
    
    Args:
        func: Function to apply to each item
        items: List of items to process
        max_workers: Maximum concurrent threads
        
    Returns:
        List of results
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(func, items))


def parallel_fetch(urls: List[str], max_workers: int = 10, timeout: int = 30) -> List[Dict[str, Any]]:
    """
    Convenience function to fetch multiple URLs concurrently.
    
    Args:
        urls: List of URLs to fetch
        max_workers: Maximum concurrent threads
        timeout: Request timeout in seconds
        
    Returns:
        List of result dicts
    """
    with ConcurrentScraper(max_workers=max_workers, timeout=timeout) as scraper:
        return scraper.fetch_multiple(urls)


async def async_fetch(urls: List[str], max_concurrent: int = 20, timeout: int = 30) -> List[Dict[str, Any]]:
    """
    Convenience async function to fetch multiple URLs.
    
    Args:
        urls: List of URLs to fetch
        max_concurrent: Maximum concurrent requests
        timeout: Request timeout in seconds
        
    Returns:
        List of result dicts
    """
    async with AsyncScraper(max_concurrent=max_concurrent, timeout=timeout) as scraper:
        return await scraper.fetch_multiple_async(urls)
