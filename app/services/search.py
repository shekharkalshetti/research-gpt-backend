import requests
import json
import os
from app.utils.errors import APIError


def search_papers(query, region="in", api_key=None):
    """
    Search for research papers using Google Serper API

    Args:
        query (str): The search query
        region (str): The region for the search (default: "in")
        api_key (str, optional): Google Serper API key. If not provided, 
                                it will be fetched from environment variables

    Returns:
        dict: The search results response

    Raises:
        APIError: If there's an error with the search request
    """
    if api_key is None:
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            raise APIError(
                "Google Serper API key not found in environment variables", 500)

    url = "https://google.serper.dev/scholar"

    payload = json.dumps({
        "q": query,
        "gl": region
    })

    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()  # Raise exception for non-200 status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        raise APIError(f"Error searching papers: {str(e)}", 500)
    except json.JSONDecodeError:
        raise APIError("Error parsing search results", 500)
