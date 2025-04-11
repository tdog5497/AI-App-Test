import uuid
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

class DataStore:
    """
    Simple in-memory data store for the application.
    In a production environment, this would be replaced with a proper database.
    """
    
    def __init__(self):
        self.notes = {}
        self.summaries = {}
        self.flashcard_sets = {}
        
    def add_note(self, text: str) -> str:
        """
        Add a new note to the data store.
        
        Args:
            text: The text content of the note
            
        Returns:
            str: The ID of the created note
        """
        note_id = str(uuid.uuid4())
        self.notes[note_id] = {"text": text, "created_at": uuid.uuid1().time}
        logger.debug(f"Added note with ID: {note_id}")
        return note_id
    
    def get_note(self, note_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a note from the data store.
        
        Args:
            note_id: The ID of the note to retrieve
            
        Returns:
            Optional[Dict]: The note data or None if not found
        """
        return self.notes.get(note_id)
    
    def add_summary(self, original_text: str, summary: str) -> str:
        """
        Add a new summary to the data store.
        
        Args:
            original_text: The original text that was summarized
            summary: The generated summary
            
        Returns:
            str: The ID of the created summary
        """
        summary_id = str(uuid.uuid4())
        self.summaries[summary_id] = {
            "original_text": original_text,
            "summary": summary,
            "created_at": uuid.uuid1().time
        }
        logger.debug(f"Added summary with ID: {summary_id}")
        return summary_id
    
    def get_summary(self, summary_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a summary from the data store.
        
        Args:
            summary_id: The ID of the summary to retrieve
            
        Returns:
            Optional[Dict]: The summary data or None if not found
        """
        return self.summaries.get(summary_id)
    
    def add_flashcards(self, original_text: str, flashcards: List[Dict[str, str]]) -> str:
        """
        Add a new set of flashcards to the data store.
        
        Args:
            original_text: The original text that the flashcards were created from
            flashcards: The list of flashcard dictionaries (question/answer pairs)
            
        Returns:
            str: The ID of the created flashcard set
        """
        flashcard_set_id = str(uuid.uuid4())
        self.flashcard_sets[flashcard_set_id] = {
            "original_text": original_text,
            "flashcards": flashcards,
            "created_at": uuid.uuid1().time
        }
        logger.debug(f"Added flashcard set with ID: {flashcard_set_id}")
        return flashcard_set_id
    
    def get_flashcard_set(self, flashcard_set_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a flashcard set from the data store.
        
        Args:
            flashcard_set_id: The ID of the flashcard set to retrieve
            
        Returns:
            Optional[Dict]: The flashcard set data or None if not found
        """
        return self.flashcard_sets.get(flashcard_set_id)
