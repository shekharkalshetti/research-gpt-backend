from flask import Blueprint, request, jsonify
from app.services.search import search_papers
from app.services.crawler import crawl_papers
from app.services.abstract_extraction import extract_abstracts
from app.services.llm_service import generate_response
from app.utils.errors import APIError

research_api = Blueprint("research_api", __name__, url_prefix="/api")


@research_api.route("/research", methods=["POST"])
def research():
    """
    Main endpoint that orchestrates the entire research process:
    1. Searches for papers using Google Serper API
    2. Crawls the first 5 paper links using Spider API
    3. Extracts abstracts from the crawled content using LLM
    4. Generates a response using an LLM based on the abstracts and user query
    """
    data = request.json
    if not data or "query" not in data:
        raise APIError("Query is required", 400)

    user_query = data["query"]

    # Step 1: Search for papers
    search_results = search_papers(user_query)
    if not search_results or not search_results.get("organic"):
        raise APIError("No search results found", 404)

    # Step 2: Crawl the first 5 paper links
    paper_links = [result.get("link")
                   for result in search_results["organic"][:5]]
    cited_by = [result.get("citedBy")
                for result in search_results["organic"][:5]]
    year = [result.get("year") for result in search_results["organic"][:5]]
    publicationInfo = [result.get("publicationInfo")
                       for result in search_results["organic"][:5]]

    crawled_content = crawl_papers(paper_links)

    # Step 3: Extract abstracts from the crawled content
    abstracts = extract_abstracts(crawled_content)

    # Step 4: Generate response using LLM
    response = generate_response(user_query, abstracts)

    return jsonify({
        "query": user_query,
        "papers": [
            {
                "title": search_results["organic"][i]["title"],
                "citedBy": cited_by[i],
                "year": year[i],
                "publicationInfo": publicationInfo[i],
                "link": paper_links[i],
                "abstract": abstracts[i] if i < len(abstracts) else None,
                "pdfUrl": search_results["organic"][i].get("pdfUrl", None)
            } for i in range(min(len(paper_links), len(abstracts)))
        ],
        "response": response
    })
