# utils/pdf_utils.py
import io
import logging
from PyPDF2 import PdfReader

# Configure logging
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_file):
    """
    Extract text content from a PDF file.

    Args:
        pdf_file: BytesIO object containing the PDF data

    Returns:
        Extracted text as a string
    """
    try:
        # Create PDF reader object
        pdf_reader = PdfReader(pdf_file)

        # Extract text from each page
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:  # Some pages might not have extractable text
                text += page_text + "\n\n"

        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise Exception(f"Error extracting text from PDF: {str(e)}")