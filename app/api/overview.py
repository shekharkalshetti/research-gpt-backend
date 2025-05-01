from flask import Blueprint, request, jsonify
from app.services.chunk_process import analyze_paper
from app.utils.errors import APIError

overview_api = Blueprint("overview_api", __name__, url_prefix="/api")


@overview_api.route("/overview", methods=["POST"])
def analyze_paper_route():
    """
    Analyze a research paper from its PDF URL
    """
    data = request.json
    if not data or "pdf_url" not in data:
        raise APIError("PDF URL is required", 400)

    pdf_url = data["pdf_url"]

    # Analyze the paper
    analysis = analyze_paper(pdf_url)

    return jsonify({
        "pdf_url": pdf_url,
        "analysis": analysis
    })
