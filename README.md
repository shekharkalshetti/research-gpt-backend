# Research Agent

A Flask-based research agent that searches for academic papers, extracts abstracts, and generates concise responses based on research findings.

## Features

- Search for research papers using Google Scholar via Serper API
- Crawl paper websites using Spider API
- Extract abstracts from crawled content using Claude's assistance
- Generate concise responses using an LLM based on the extracted abstracts

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/research-agent.git
cd research-agent
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables:
   Create a `.env` file in the root directory with the following variables:

```
SERPER_API_KEY=your_google_serper_api_key
SPIDER_API_KEY=your_spider_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

## Usage

1. Start the Flask server:

```bash
python app.py
```

2. The API will be available at `http://localhost:5000`.

## API Endpoints

### Main Research Endpoint

```
POST /api/research
```

Request body:

```json
{
  "query": "Which is better, RAG or Graph RAG?"
}
```

This endpoint orchestrates the entire research process and returns a comprehensive response.

### Individual Endpoints

#### Search Papers

```
POST /api/search
```

Request body:

```json
{
  "query": "Which is better, RAG or Graph RAG?"
}
```

#### Crawl Paper URLs

```
POST /api/crawl
```

Request body:

```json
{
  "urls": [
    "https://arxiv.org/abs/2404.16130",
    "https://arxiv.org/abs/2405.20139"
  ]
}
```

#### Extract Abstracts

```
POST /api/extract
```

Request body:

```json
{
  "content": [
    {
      "url": "https://arxiv.org/abs/2404.16130",
      "content": "...markdown content..."
    },
    {
      "url": "https://arxiv.org/abs/2405.20139",
      "content": "...markdown content..."
    }
  ]
}
```

#### Generate Response

```
POST /api/generate
```

Request body:

```json
{
  "query": "Which is better, RAG or Graph RAG?",
  "abstracts": ["Abstract 1 content...", "Abstract 2 content..."]
}
```

## Project Structure

```
.
├── app.py                      # Application entry point
├── requirements.txt            # Project dependencies
├── .env                        # Environment variables (create this file)
├── app/
│   ├── __init__.py            # Flask app factory
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py          # API routes
│   ├── config/
│   │   ├── __init__.py
│   │   └── anthropic_client.py # Anthropic client configuration
│   ├── services/
│   │   ├── __init__.py
│   │   ├── search_service.py  # Google Serper API integration
│   │   ├── crawler_service.py # Spider API integration
│   │   ├── processor_service.py # Abstract extraction using LLM
│   │   └── llm_service.py     # LLM integration for response generation
│   └── utils/
│       ├── __init__.py
│       └── errors.py          # Error handling
```

## License

[MIT License](LICENSE)
