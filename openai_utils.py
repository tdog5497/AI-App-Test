# utils/openai_utils.py
import os
import json
import logging
import re
from openai import OpenAI
from openai import APIError, RateLimitError, AuthenticationError

# Configure logging
logger = logging.getLogger(__name__)

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
MODEL = "gpt-4o"

# Initialize OpenAI client with a function to get the key
def get_api_key():
    return os.environ.get("OPENAI_API_KEY")

OPENAI_API_KEY = get_api_key()
client = OpenAI(api_key=OPENAI_API_KEY)

def check_api_key(test_with_api_call=False):
    """
    Checks if the API key is present and valid.
    Returns True if the key is valid, raises an exception otherwise.

    Args:
        test_with_api_call: If True, make an actual API call to verify the key.
                           Set to True when updating the key to ensure it works correctly.
    """
    # Get the current API key
    api_key = get_api_key()
    if not api_key:
        logger.error("OpenAI API key is missing")
        raise AuthenticationError("OpenAI API key is missing. Please set the OPENAI_API_KEY environment variable.")

    # Update the client with the current API key
    global client
    client.api_key = api_key

    # If we don't need to do an API call test, just return here
    # This is useful during startup to avoid unnecessary API calls
    if not test_with_api_call:
        return True

    # If we get here, we need to verify the key with an actual API call
    try:
        # Make a minimal API call to validate the key
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        logger.info("API key verification successful")
        return True
    except AuthenticationError as e:
        logger.error(f"API key verification failed: {str(e)}")
        raise
    except RateLimitError as e:
        logger.error(f"API rate limit exceeded: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"API verification error: {str(e)}")
        raise

async def generate_summary(text):
    """
    Generate a summary of the provided text using OpenAI GPT.

    Args:
        text: The text to summarize

    Returns:
        A string containing the summary
    """
    try:
        # Truncate text if it's too long (token limit considerations)
        max_length = 4000
        if len(text) > max_length:
            text = text[:max_length] + "..."

        # Create a chat completion with the OpenAI API
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful study assistant. Create a concise but comprehensive summary of the following notes."},
                {"role": "user", "content": text}
            ],
            max_tokens=1000,
            temperature=0.5
        )

        # Extract the summary text from the response
        summary = response.choices[0].message.content.strip()
        return summary

    except Exception as e:
        logger.error(f"API error generating summary: {str(e)}")
        raise

async def generate_flashcards(text):
    """
    Generate flashcards (question-answer pairs) from the provided text using OpenAI GPT.

    Args:
        text: The text to create flashcards from

    Returns:
        A list of dictionaries, each containing a question and answer
    """
    try:
        # Truncate text if it's too long
        max_length = 4000
        if len(text) > max_length:
            text = text[:max_length] + "..."

        # Create a chat completion with the OpenAI API
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful study assistant. Create 5-10 flashcards (question-answer pairs) based on the following notes. Format your response as a JSON array of objects with 'question' and 'answer' fields."},
                {"role": "user", "content": text}
            ],
            max_tokens=1500,
            temperature=0.7
        )

        # Extract and parse the flashcards from the response
        content = response.choices[0].message.content.strip()

        # Simple parsing of the JSON-like content
        # Try to extract JSON if it's embedded in text
        json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)

        try:
            flashcards = json.loads(content)
            # Validate the structure
            for card in flashcards:
                if not isinstance(card, dict) or 'question' not in card or 'answer' not in card:
                    raise ValueError("Invalid flashcard format")
            return flashcards
        except json.JSONDecodeError:
            # If JSON parsing fails, try to format it manually
            cards = []
            qa_pairs = re.findall(r'Q(?:uestion)?:?\s*(.*?)\s*A(?:nswer)?:?\s*(.*?)(?=Q(?:uestion)?:?|\Z)', 
                                  content, re.DOTALL | re.IGNORECASE)

            for q, a in qa_pairs:
                cards.append({"question": q.strip(), "answer": a.strip()})

            if cards:
                return cards
            else:
                # Last resort: create a simple structure from the text
                lines = content.split('\n')
                cards = []
                for i in range(0, len(lines) - 1, 2):
                    if i+1 < len(lines):
                        cards.append({
                            "question": lines[i].strip().lstrip('0123456789.- '),
                            "answer": lines[i+1].strip()
                        })
                return cards

    except Exception as e:
        logger.error(f"API error generating flashcards: {str(e)}")
        raise

async def answer_question(question, context=""):
    """
    Have a conversation with the AI assistant about study materials.

    Args:
        question: The user's question
        context: Optional context from their notes

    Returns:
        The assistant's response
    """
    try:
        messages = [
            {"role": "system", "content": "You are a helpful study assistant. Answer the student's question based on their notes if relevant."}
        ]

        # Add context if available
        if context:
            max_context_length = 2000
            if len(context) > max_context_length:
                context = context[:max_context_length] + "..."
            messages.append({"role": "user", "content": f"Here are my notes: {context}"})

        # Add the user's question
        messages.append({"role": "user", "content": question})

        # Create a chat completion with the OpenAI API
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=800,
            temperature=0.7
        )

        # Extract the assistant's response
        answer = response.choices[0].message.content.strip()
        return answer

    except Exception as e:
        logger.error(f"API error answering question: {str(e)}")
        raise