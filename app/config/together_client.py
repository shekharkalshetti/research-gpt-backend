import os
from together import Together

# Get API key from environment variables
together_api_key = os.environ.get("TOGETHER_API_KEY")
if not together_api_key:
    raise ValueError("TOGETHER_API_KEY is required")

# Initialize Together client
together = Together(api_key=together_api_key)
