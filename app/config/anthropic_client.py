import os
from anthropic import Anthropic

# Get API key from environment variables
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
if not anthropic_api_key:
    raise ValueError("ANTHROPIC_API_KEY is required")

# Initialize Anthropic client
anthropic = Anthropic(api_key=anthropic_api_key)
