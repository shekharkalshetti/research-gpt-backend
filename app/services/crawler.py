import requests
import os
from app.utils.errors import APIError


def crawl_papers(urls, api_key=None, depth=1, return_format="markdown"):
    """
    Crawl paper URLs using the Spider API

    Args:
        urls (list): List of URLs to crawl
        api_key (str, optional): Spider API key. If not provided, 
                               it will be fetched from environment variables
        depth (int): Crawl depth (-1 for unlimited)
        return_format (str): Return format for the crawled content (default: "markdown")

    Returns:
        list: The crawled content for each URL

    Raises:
        APIError: If there's an error with the crawling request
    """
    if api_key is None:
        api_key = os.getenv("SPIDER_API_KEY")
        if not api_key:
            raise APIError(
                "Spider API key not found in environment variables", 500)

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }

    crawled_content = []

    for url in urls:
        # Prepare the request payload
        json_data = {
            "limit": 1,
            "return_format": return_format,
            "depth": depth,
            "url": url
        }

        try:
            response = requests.post(
                'https://api.spider.cloud/crawl',
                headers=headers,
                json=json_data
            )

            response_data = response.json()
            if isinstance(response_data, list) and len(response_data) > 0:
                # Extract the content from the first item in the response
                crawled_content.append({
                    "url": url,
                    "content": response_data[0].get("content", ""),
                    "status": response_data[0].get("status"),
                    "error": response_data[0].get("error")
                })
            else:
                crawled_content.append({
                    "url": url,
                    "content": "",
                    "status": None,
                    "error": "Invalid response format"
                })
        except requests.exceptions.RequestException as e:
            crawled_content.append({
                "url": url,
                "content": "",
                "status": None,
                "error": str(e)
            })

    return crawled_content
