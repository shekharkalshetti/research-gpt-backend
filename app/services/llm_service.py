from app.config.anthropic_client import anthropic
from app.utils.errors import APIError


def generate_response(query, abstracts, model="claude-3-5-sonnet-20241022", max_tokens=4000):
    """
    Generate a response using Anthropic's Claude based on abstracts and the user query

    Args:
        query (str): The user's query
        abstracts (list): List of abstracts from research papers
        model (str): The model to use for generation
        max_tokens (int): Maximum number of tokens in the response

    Returns:
        str: The generated response

    Raises:
        APIError: If there's an error with the LLM request
    """
    # Filter out empty abstracts
    valid_abstracts = [abstract for abstract in abstracts if abstract]

    if not valid_abstracts:
        raise APIError("No valid abstracts to generate a response from", 400)

    # Prepare the context with abstracts
    context = "\n\n".join(
        [f"Abstract {i+1}:\n{abstract}" for i, abstract in enumerate(valid_abstracts)])

    # Prepare the system prompt for Claude
    system_prompt = (
        "You are a research assistant generating structured, markdown-formatted responses based strictly on the provided research abstracts. "
        "Your tone must be confident and assertive. Avoid vague or hedging phrases. "
        "Start with one bolded sentence that clearly summarizes the main conclusion. Then use markdown headers and bullet points to structure the rest of the response clearly. "
        "Do NOT start the answer with 'Based on the provided abstracts' or similar phrasing. "
        "Focus on directly answering the query with clarity and precision using only the given abstracts."
    )

    user_prompt = (
        "Using ONLY the information in the abstracts below, generate a scientifically accurate response. "
        "Follow these critical guidelines:\n"
        "1. STATE ONLY FACTS explicitly mentioned in the abstracts - do not infer or extrapolate\n"
        "2. PRESERVE scientific terminology and statistical measures exactly as stated\n"
        "3. ACKNOWLEDGE any limitations or conflicting evidence from the abstracts\n"
        "4. INDICATE uncertainty where the abstracts show conflicting or incomplete evidence\n"
        "5. DO NOT fill sections if the abstracts lack the necessary information\n\n"
        f"Query: {query}\n\n"
        "Abstracts:\n"
        f"{context}\n\n"
        "Markdown Template:\n\n"
        """
        ## **Answer Summary**

        **[A direct, factual answer based solely on abstract content. If the answer is unclear or incomplete based on abstracts, state this.]**

        ---

        ## 🔍 **Key Findings**
        - 🔑 **[Specific finding with numbers/statistics if available]**  
        • *Evidence: [Quote or paraphrase from abstract]*
        - 📌 **[Another specific finding from the abstracts]**  
        • *Evidence: [Quote or paraphrase from abstract]*
        - 💡 **[Additional finding if available in abstracts]**  
        • *Evidence: [Quote or paraphrase from abstract]*

        ---

        ## 📘 **Evidence Directly from Abstracts**

        ### ✓ Supporting Evidence:
        - **Abstract 1**: "[Direct quote or paraphrase]"  
        - *Key metrics: [Specific numbers/statistics]*
        - *Study design: [If mentioned]*

        - **Abstract 2**: "[Direct quote or paraphrase]"  
        - *Key metrics: [Specific numbers/statistics]*
        - *Study design: [If mentioned]*

        ### ⚠️ Conflicting Evidence (if any):
        - *[Mention any contradictions between abstracts, with sources]*

        ### 🔍 Evidence Gaps:
        - *[Explicitly state what information is not available in the abstracts]*

        ---

        ## 📊 **Scientific Details**

        | Aspect | Finding | Source |
        |--------|---------|--------|
        | [Specific measure] | [Value from abstract] | [Abstract #] |
        | [Research design] | [Type mentioned] | [Abstract #] |
        | [Sample size] | [Number if available] | [Abstract #] |

        ---

        ## 📈 **Implications Based Strictly on Abstracts**
        - 🧠 **Scientific relevance**: [What the abstracts actually state about significance]  
        - 🔬 **Study limitations**: [Limitations explicitly mentioned in abstracts]  
        - ❓ **Areas requiring further research**: [Gaps noted in the abstracts]  

        ---

        ## 📎 **Conclusion**
        **[Reiterate only what can be conclusively stated based on the abstracts. Clearly indicate if the abstracts don't provide sufficient information to answer the query fully.]**

        *Note: This summary is based exclusively on the provided abstracts and may not represent the complete scientific understanding of this topic.*
    """
    )

    try:
        # Make request to Anthropic API using the SDK
        message = anthropic.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=0.3,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        return message.content[0].text

    except Exception as e:
        raise APIError(f"Error generating response: {str(e)}", 500)


def extract_abstract_with_llm(content, url, model="claude-3-5-sonnet-20241022"):
    """
    Use Claude to extract and summarize the abstract from a research paper

    Args:
        content (str): The markdown content of the paper
        url (str): The URL of the paper
        model (str): The model to use for extraction

    Returns:
        str: The extracted abstract

    Raises:
        APIError: If there's an error with the LLM request
    """
    # Only use the first 30,000 characters of content to avoid token limits
    content_to_analyze = content[:30000] if content else ""

    if not content_to_analyze:
        return ""

    system_prompt = """You are an assistant specialized in extracting abstracts from research papers.
        Your task is to identify and extract the abstract from the given paper content.
        If you can't find a clear abstract, summarize the paper's main contributions in 200 words or less.
        Focus on extracting exactly what's in the paper, not adding new information."""

    user_prompt = (
        f"Extract the abstract from the following research paper content from {url}. "
        "If there's no clear abstract section, provide a brief summary (200 words max) "
        "of the paper's main contributions and findings:\n\n"
        f"{content_to_analyze}"
    )

    try:
        # Make request to Anthropic API using the SDK
        message = anthropic.messages.create(
            model=model,
            max_tokens=400,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        return message.content[0].text

    except Exception as e:
        raise APIError(f"Error extracting abstract: {str(e)}", 500)
