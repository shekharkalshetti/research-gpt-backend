from app.services.llm_service import extract_abstract_with_llm
from app.utils.errors import APIError


def extract_abstracts(crawled_content):
    """
    Extract abstracts from the crawled content of research papers using LLM

    Args:
        crawled_content (list): List of dictionaries containing crawled content

    Returns:
        list: Extracted abstracts for each paper

    Raises:
        APIError: If there's an error extracting abstracts
    """
    abstracts = []

    for content_item in crawled_content:
        if not content_item or not content_item.get("content"):
            abstracts.append("")
            continue

        raw_content = content_item["content"]
        url = content_item["url"]

        # Use LLM to extract abstract
        try:
            abstract = extract_abstract_with_llm(raw_content, url)
        except APIError as e:
            # Log the error but continue processing other papers
            print(f"Error extracting abstract for {url}: {str(e)}")
            abstract = ""

        abstracts.append(abstract)

    return abstracts
