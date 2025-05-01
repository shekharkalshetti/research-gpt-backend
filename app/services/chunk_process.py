import json
import os
import re
import gc
import tempfile
import requests
from PyPDF2 import PdfReader
from app.config.anthropic_client import anthropic
from app.config.together_client import together
from app.utils.errors import APIError


def download_pdf(pdf_url):
    """
    Download a PDF from a URL to a temporary file

    Args:
        pdf_url (str): URL of the PDF to download

    Returns:
        str: Path to the downloaded temporary PDF file

    Raises:
        APIError: If there's an error downloading the PDF
    """
    try:
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_path = temp_file.name
        temp_file.close()

        # Download the PDF
        print(f"Downloading PDF from {pdf_url}")
        response = requests.get(pdf_url, stream=True, timeout=60)
        response.raise_for_status()

        # Write the content to the temporary file
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return temp_path

    except Exception as e:
        raise APIError(f"Error downloading PDF: {str(e)}", 500)


def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file

    Args:
        pdf_path (str): Path to the PDF file

    Returns:
        str: Extracted text from the PDF

    Raises:
        APIError: If there's an error extracting text from the PDF
    """
    try:
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        print(f"Extracting text from {total_pages} pages...")

        # Extract all text
        all_text = []
        for i in range(total_pages):
            print(f"  Page {i+1}/{total_pages}", end="\r")
            page = reader.pages[i]
            text = page.extract_text()
            if text:
                all_text.append(text)

        print("\nCleaning and joining text...")
        full_text = " ".join(all_text)

        # Basic cleaning
        full_text = re.sub(r'\s+', ' ', full_text).strip()

        # Clear memory
        all_text = None
        reader = None
        gc.collect()

        return full_text

    except Exception as e:
        raise APIError(f"Error extracting PDF text: {str(e)}", 500)


def chunk_text(text, min_chunks=8, max_chunks=12):
    """
    Split text into a target number of chunks, favoring natural breaks

    Args:
        text (str): Text to chunk
        min_chunks (int): Minimum number of chunks to create
        max_chunks (int): Maximum number of chunks to create

    Returns:
        list: List of text chunks
    """
    if not text:
        return []

    # Determine ideal chunk size based on target chunk count
    text_length = len(text)
    print(f"Text length: {text_length} characters")

    # Target chunk size based on desired chunk count
    target_size = text_length // max(min_chunks, 1)

    # But don't make chunks larger than 10,000 chars (approx 2000-3000 tokens)
    chunk_size = min(target_size, 10000)
    print(f"Chunking text into roughly {min_chunks}-{max_chunks} chunks...")

    chunks = []
    pos = 0

    while pos < text_length:
        # Determine end of this chunk
        end = min(pos + chunk_size, text_length)

        # Find natural breaks if not at the end
        if end < text_length:
            # Try to find paragraph breaks first
            paragraph_break = text.rfind('\n\n', pos, end)

            # Then try sentence breaks
            sentence_breaks = [
                text.rfind('. ', pos, end),
                text.rfind('? ', pos, end),
                text.rfind('! ', pos, end),
                text.rfind('.\n', pos, end),
            ]

            # Use the best break we can find
            best_break = -1
            if paragraph_break > pos + (chunk_size // 2):
                best_break = paragraph_break + 2
            else:
                # Find the best sentence break
                for brk in sentence_breaks:
                    if brk > pos + (chunk_size // 3) and brk > best_break:
                        best_break = brk + 2

            if best_break > 0:
                end = best_break

        # Extract the chunk
        chunk = text[pos:end].strip()
        if chunk:
            chunks.append(chunk)
            print(f"  Created chunk {len(chunks)}: {len(chunk)} chars")

        # Move to next chunk position
        pos = end

    print(f"Text divided into {len(chunks)} chunks")
    return chunks


def summarize_chunk(chunk, chunk_index, total_chunks, model="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"):
    """
    Summarize a single chunk of text using Together's Qwen 2.5

    Args:
        chunk (str): Text chunk to summarize
        chunk_index (int): Index of the current chunk
        total_chunks (int): Total number of chunks
        model (str): Together model to use

    Returns:
        str: Summarized chunk

    Raises:
        APIError: If there's an error summarizing the chunk
    """
    try:
        # Limit chunk size if needed
        if len(chunk) > 20000:
            chunk = chunk[:20000] + "..."

        system_prompt = (
            "You are an expert research paper analyzer. Summarize this section of an academic paper clearly and concisely. "
            "Focus on extracting the key information, methods, findings, and conclusions from this section."
        )

        user_prompt = f"Summarize this text section (part {chunk_index+1}/{total_chunks}) of a research paper:\n\n{chunk}"

        print(
            f"  Summarizing chunk {chunk_index+1}/{total_chunks} ({len(chunk)} chars)")

        # Make request to Together API
        response = together.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )

        summary = response.choices[0].message.content
        print(f"  Completed chunk {chunk_index+1} summarization\n")
        return summary

    except Exception as e:
        print(f"  Error summarizing chunk {chunk_index+1}: {str(e)}")
        return f"Error summarizing this section: {str(e)}"


def create_complete_analysis(summaries, model="Qwen/Qwen2.5-72B-Instruct-Turbo"):
    """
    Create a comprehensive analysis of the paper from all chunk summaries using Together's Qwen 2.5

    Args:
        summaries (list): List of summarized chunks
        model (str): Together model to use

    Returns:
        dict: Complete paper analysis with summary, key findings, objectives, 
              methods, results, conclusion, and key concepts

    Raises:
        APIError: If there's an error creating the final analysis
    """
    try:
        if not summaries:
            raise APIError("No summaries generated from the paper", 400)

        print("\nCreating comprehensive paper analysis...")

        # Join all summaries, limiting size if needed
        all_summaries_text = ""
        for i, summary in enumerate(summaries):
            if len(summary) > 2000:
                summary = summary[:2000] + "..."
            all_summaries_text += f"Section {i+1}: {summary}\n\n"

        # Limit total size for API if needed
        if len(all_summaries_text) > 25000:
            all_summaries_text = all_summaries_text[:25000] + "..."

        system_prompt = (
            "You are an expert research paper analyst. Create a comprehensive analysis of this research paper "
            "from the provided section summaries. Your analysis must include the following components:\n\n"
            "1. A 150-word executive summary of the entire paper\n"
            "2. 5 key findings as distinct bullet points\n"
            "3. 1-5 main research objectives as distinct bullet points\n"
            "4. Methods used as distinct bullet points\n"
            "5. Important results as distinct bullet points\n"
            "6. Conclusion (1-2 paragraphs)\n"
            "7. Key concepts addressed in the paper as bullet points\n\n"
            "IMPORTANT: Format your response as structured JSON with the following keys:\n"
            "{\n"
            "  \"summary\": \"Executive summary text here\",\n"
            "  \"key_findings\": [\"Finding 1\", \"Finding 2\", ...],\n"
            "  \"objectives\": [\"Objective 1\", \"Objective 2\", ...],\n"
            "  \"methods\": [\"Method 1\", \"Method 2\", ...],\n"
            "  \"results\": [\"Result 1\", \"Result 2\", ...],\n"
            "  \"conclusion\": \"Conclusion text here\",\n"
            "  \"key_concepts\": [\"Concept 1\", \"Concept 2\", ...]\n"
            "}\n\n"
            "Base your analysis solely on the information provided in the summaries. Each field must be filled. "
            "Make sure to format all lists as proper JSON arrays. "
            "IMPORTANT: Do not repeat the same information across different sections. Each section should contain distinct points."
        )

        user_prompt = f"Create a comprehensive analysis of this research paper from these section summaries:\n\n{all_summaries_text}"

        # Make request to Together API
        response = together.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=1200
        )

        response_text = response.choices[0].message.content

        # Extract JSON from the response (in case there's text around it)
        json_match = re.search(r'(\{[\s\S]*\})', response_text)
        if not json_match:
            raise APIError(
                "Could not extract structured data from the analysis", 500)

        json_str = json_match.group(1)

        try:
            analysis = json.loads(json_str)

            # Validate that all required fields are present
            required_fields = ["summary", "key_findings", "objectives",
                               "methods", "results", "conclusion", "key_concepts"]
            for field in required_fields:
                if field not in analysis:
                    analysis[field] = f"{field.replace('_', ' ').capitalize()} not provided"

            return analysis

        except json.JSONDecodeError:
            # If JSON parsing fails, create a backup analysis with error information
            print(f"Failed to parse JSON. Raw response:\n{response_text}")
            raise APIError("Failed to parse the structured analysis data", 500)

    except Exception as e:
        raise APIError(f"Error creating paper analysis: {str(e)}", 500)


def analyze_paper(pdf_url):
    """
    Analyze a research paper from its PDF URL

    Args:
        pdf_url (str): URL of the PDF to analyze

    Returns:
        dict: Complete paper analysis

    Raises:
        APIError: If there's an error analyzing the paper
    """
    temp_path = None
    try:
        # Download the PDF
        temp_path = download_pdf(pdf_url)

        # Extract text from the PDF
        text = extract_text_from_pdf(temp_path)
        if not text:
            raise APIError("Failed to extract text from PDF", 500)

        # Chunk the text
        chunks = chunk_text(text)

        # Free memory
        text = None
        gc.collect()

        if not chunks:
            raise APIError("No valid text chunks extracted from PDF", 500)

        # Summarize each chunk
        print("\nSummarizing chunks...")
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            summary = summarize_chunk(chunk, i, len(chunks))
            if summary:
                chunk_summaries.append(summary)

        # Free memory
        chunks = None
        gc.collect()

        if not chunk_summaries:
            raise APIError("Failed to generate any chunk summaries", 500)

        # Create the final comprehensive analysis
        analysis = create_complete_analysis(chunk_summaries)

        return analysis

    finally:
        # Clean up the temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as e:
                print(f"Error removing temporary file: {str(e)}")
