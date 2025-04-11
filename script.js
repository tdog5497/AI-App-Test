// Global variables
let currentNoteId = null;
let currentNoteText = '';
let flashcards = [];
let currentCardIndex = 0;
let chatHistory = [];

// Initialize tooltips and popovers
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips and toasts
    const toastElements = document.querySelectorAll('.toast');
    toastElements.forEach(toastEl => {
        return new bootstrap.Toast(toastEl, { autohide: true, delay: 5000 });
    });
});

// PDF Upload Form Submission with Fallback
// Global flag to track if we should use the direct form submission
let useDirectFormSubmission = false;

document.getElementById('pdf-upload-form').addEventListener('submit', async function(e) {
    // If we've decided to use the direct approach (after a previous failure), let the form submit normally
    if (useDirectFormSubmission) {
        return true; // Allow the form to submit normally
    }
    
    // Otherwise, use AJAX (preventDefault)
    e.preventDefault(); 
    
    const fileInput = document.getElementById('pdf-file');
    if (!fileInput.files.length) {
        showError('Please select a PDF file to upload.');
        return;
    }
    
    const file = fileInput.files[0];
    console.log('Uploading file:', file.name, 'Size:', file.size, 'Type:', file.type);
    
    // Create FormData and append the file
    const formData = new FormData(this); // Use the form itself to create FormData
    
    try {
        showLoading('Uploading and processing PDF...');
        console.log('Sending form data...');
        
        // Use fetch to handle the submission with XHR
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData,
            // Let the browser set the content type with boundary
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            let errorDetail = 'Failed to upload PDF';
            try {
                const errorJson = await response.json();
                errorDetail = errorJson.detail || errorDetail;
            } catch (jsonError) {
                console.error('Error parsing error response:', jsonError);
            }
            
            // If we get an error about no file provided, switch to direct form submission
            if (errorDetail.includes('file') && errorDetail.includes('provided')) {
                console.log('Switching to direct form submission for future uploads');
                useDirectFormSubmission = true;
                showError('There was an issue with the upload. Try using the alternative upload method below.');
                hideLoading();
                return;
            }
            
            throw new Error(errorDetail);
        }
        
        const data = await response.json();
        console.log('Upload successful:', data);
        
        // Store the note ID and text
        currentNoteId = data.note_id || '';
        currentNoteText = data.text || '';
        
        // Display the extracted text
        document.getElementById('uploaded-text').textContent = data.text;
        document.getElementById('upload-result').classList.remove('d-none');
        
        // Enable buttons now that we have content
        enableContentButtons();
        
        // Clear the form
        fileInput.value = '';
        
        hideLoading();
    } catch (error) {
        console.error('Upload error:', error);
        hideLoading();
        showError(error.message || 'An error occurred while uploading the PDF. Please try the alternative upload method below.');
    }
});

// Text Upload Form Submission
document.getElementById('text-upload-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const textContent = document.getElementById('text-content').value.trim();
    if (!textContent) {
        showError('Please enter some text content.');
        return;
    }
    
    try {
        showLoading('Processing text...');
        
        const response = await fetch('/upload', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'text_content': textContent
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to process text');
        }
        
        const data = await response.json();
        
        // Store the note ID and text
        currentNoteId = data.note_id;
        currentNoteText = data.text;
        
        // Display the text
        document.getElementById('uploaded-text').textContent = data.text;
        document.getElementById('upload-result').classList.remove('d-none');
        
        // Enable buttons now that we have content
        enableContentButtons();
        
        // Clear the form
        document.getElementById('text-content').value = '';
        
        hideLoading();
    } catch (error) {
        hideLoading();
        showError(error.message || 'An error occurred while processing the text.');
    }
});

// Generate Summary Button Click
document.getElementById('generate-summary-btn').addEventListener('click', async function() {
    if (!currentNoteText) {
        showError('Please upload content first before generating a summary.');
        return;
    }
    
    try {
        // Show loading
        document.getElementById('summary-loading').classList.remove('d-none');
        
        const response = await fetch('/generate-summary', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: currentNoteText
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate summary');
        }
        
        const data = await response.json();
        
        // Display the summary
        document.getElementById('summary-content').innerHTML = formatTextWithParagraphs(data.summary);
        document.getElementById('summary-result').classList.remove('d-none');
        
        // Hide loading
        document.getElementById('summary-loading').classList.add('d-none');
        
        // Scroll to summary
        document.getElementById('summary-result').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        document.getElementById('summary-loading').classList.add('d-none');
        showError(error.message || 'An error occurred while generating the summary.');
    }
});

// Copy Summary Button Click
document.getElementById('copy-summary-btn').addEventListener('click', function() {
    const summaryContent = document.getElementById('summary-content').textContent;
    
    navigator.clipboard.writeText(summaryContent).then(function() {
        // Change button text temporarily
        const copyBtn = document.getElementById('copy-summary-btn');
        const originalHtml = copyBtn.innerHTML;
        copyBtn.innerHTML = '<i class="fas fa-check me-1"></i> Copied!';
        
        setTimeout(function() {
            copyBtn.innerHTML = originalHtml;
        }, 2000);
    }).catch(function() {
        showError('Failed to copy summary to clipboard.');
    });
});

// Generate Flashcards Button Click
document.getElementById('generate-flashcards-btn').addEventListener('click', async function() {
    if (!currentNoteText) {
        showError('Please upload content first before generating flashcards.');
        return;
    }
    
    try {
        // Show loading
        document.getElementById('flashcards-loading').classList.remove('d-none');
        
        const response = await fetch('/generate-flashcards', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: currentNoteText
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate flashcards');
        }
        
        const data = await response.json();
        
        // Store flashcards globally
        flashcards = data.flashcards;
        currentCardIndex = 0;
        
        // Display the first flashcard
        renderFlashcard(currentCardIndex);
        document.getElementById('flashcards-result').classList.remove('d-none');
        
        // Update pagination
        updateFlashcardPagination();
        
        // Hide loading
        document.getElementById('flashcards-loading').classList.add('d-none');
        
        // Scroll to flashcards section
        document.getElementById('flashcards-result').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        document.getElementById('flashcards-loading').classList.add('d-none');
        showError(error.message || 'An error occurred while generating flashcards.');
    }
});

// Flashcard Navigation Buttons
document.getElementById('prev-card-btn').addEventListener('click', function() {
    if (currentCardIndex > 0) {
        currentCardIndex--;
        renderFlashcard(currentCardIndex);
        updateFlashcardPagination();
    }
});

document.getElementById('next-card-btn').addEventListener('click', function() {
    if (currentCardIndex < flashcards.length - 1) {
        currentCardIndex++;
        renderFlashcard(currentCardIndex);
        updateFlashcardPagination();
    }
});

// Ask Question Form Submission
document.getElementById('question-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const questionInput = document.getElementById('question-input');
    const question = questionInput.value.trim();
    
    if (!question) {
        showError('Please enter a question.');
        return;
    }
    
    const useContext = document.getElementById('use-context-check').checked;
    const context = useContext ? currentNoteText : null;
    
    try {
        // Show chat history container if it's hidden
        document.getElementById('chat-history').classList.remove('d-none');
        
        // Show loading
        document.getElementById('question-loading').classList.remove('d-none');
        
        // Add user question to chat
        addMessageToChat('user', question);
        
        const response = await fetch('/ask-question', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: question,
                context: context
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to answer question');
        }
        
        const data = await response.json();
        
        // Add AI response to chat
        addMessageToChat('ai', data.answer);
        
        // Hide loading
        document.getElementById('question-loading').classList.add('d-none');
        
        // Clear input
        questionInput.value = '';
        
        // Scroll to bottom of chat
        const chatContainer = document.getElementById('chat-messages');
        chatContainer.scrollTop = chatContainer.scrollHeight;
    } catch (error) {
        document.getElementById('question-loading').classList.add('d-none');
        showError(error.message || 'An error occurred while answering the question.');
    }
});

// Helper Functions

// Enable buttons after content is uploaded
function enableContentButtons() {
    document.getElementById('generate-summary-btn').disabled = false;
    document.getElementById('generate-flashcards-btn').disabled = false;
    document.getElementById('ask-question-btn').disabled = false;
}

// Render a flashcard at the given index
function renderFlashcard(index) {
    if (!flashcards || !flashcards.length) return;
    
    const flashcard = flashcards[index];
    const container = document.getElementById('flashcards-container');
    
    // Create the flashcard HTML
    container.innerHTML = `
        <div class="col-md-10 mx-auto">
            <div class="card flashcard mb-4">
                <div class="card-header bg-primary bg-opacity-50">
                    <h5 class="card-title mb-0">Question</h5>
                </div>
                <div class="card-body">
                    <p class="card-text">${flashcard.question}</p>
                </div>
                <div class="card-footer text-center">
                    <button class="btn btn-sm btn-outline-light toggle-answer-btn">
                        <i class="fas fa-eye me-1"></i> Show Answer
                    </button>
                </div>
            </div>
            
            <div class="card flashcard-answer d-none">
                <div class="card-header bg-success bg-opacity-50">
                    <h5 class="card-title mb-0">Answer</h5>
                </div>
                <div class="card-body">
                    <p class="card-text">${flashcard.answer}</p>
                </div>
            </div>
        </div>
    `;
    
    // Add event listener to toggle answer button
    document.querySelector('.toggle-answer-btn').addEventListener('click', function() {
        const answerCard = document.querySelector('.flashcard-answer');
        const toggleBtn = document.querySelector('.toggle-answer-btn');
        
        if (answerCard.classList.contains('d-none')) {
            answerCard.classList.remove('d-none');
            toggleBtn.innerHTML = '<i class="fas fa-eye-slash me-1"></i> Hide Answer';
        } else {
            answerCard.classList.add('d-none');
            toggleBtn.innerHTML = '<i class="fas fa-eye me-1"></i> Show Answer';
        }
    });
}

// Update flashcard pagination text and button states
function updateFlashcardPagination() {
    document.getElementById('card-pagination').textContent = `Card ${currentCardIndex + 1} of ${flashcards.length}`;
    
    // Update button states
    document.getElementById('prev-card-btn').disabled = currentCardIndex === 0;
    document.getElementById('next-card-btn').disabled = currentCardIndex === flashcards.length - 1;
}

// Add a message to the chat history
function addMessageToChat(role, message) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    
    messageDiv.className = `chat-message ${role}-message`;
    
    if (role === 'user') {
        messageDiv.innerHTML = `
            <div class="message-bubble">
                <div class="message-content">
                    <p>${message}</p>
                </div>
                <div class="message-info">
                    <span class="message-time">${formatTime(new Date())}</span>
                </div>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="message-bubble">
                <div class="message-header">
                    <span class="ai-label"><i class="fas fa-robot me-1"></i> AI Assistant</span>
                </div>
                <div class="message-content">
                    <p>${formatTextWithParagraphs(message)}</p>
                </div>
                <div class="message-info">
                    <span class="message-time">${formatTime(new Date())}</span>
                </div>
            </div>
        `;
    }
    
    chatMessages.appendChild(messageDiv);
    
    // Store in chat history
    chatHistory.push({ role, message, timestamp: new Date() });
}

// Format text with paragraphs
function formatTextWithParagraphs(text) {
    return text.split('\n').map(line => {
        if (line.trim() === '') return '<br>';
        return `<p>${line}</p>`;
    }).join('');
}

// Format time for chat messages
function formatTime(date) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Show error toast
function showError(message) {
    const errorToast = document.getElementById('error-toast');
    document.getElementById('error-message').textContent = message;
    const toast = new bootstrap.Toast(errorToast);
    toast.show();
}

// Show loading message
function showLoading(message) {
    // Placeholder for a potential loading indicator
    // You could implement a more sophisticated loading notification system
}

// Hide loading message
function hideLoading() {
    // Placeholder for hiding a loading indicator
}

// API Key Update Form Submission
document.addEventListener('DOMContentLoaded', function() {
    const apiKeyForm = document.getElementById('update-api-key-form');
    if (apiKeyForm) {
        apiKeyForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const apiKeyInput = document.getElementById('api-key-input');
            const apiKey = apiKeyInput.value.trim();
            const resultDiv = document.getElementById('api-key-update-result');
            
            if (!apiKey) {
                resultDiv.innerHTML = '<div class="alert alert-danger mt-2">Please enter an API key.</div>';
                return;
            }
            
            try {
                // Show loading state
                resultDiv.innerHTML = '<div class="spinner-border spinner-border-sm text-light" role="status"><span class="visually-hidden">Loading...</span></div> Updating API key...';
                
                const response = await fetch('/update-api-key', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        api_key: apiKey
                    })
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.detail || 'Failed to update API key');
                }
                
                // Show success message
                resultDiv.innerHTML = '<div class="alert alert-success mt-2">API key updated successfully. Refreshing page...</div>';
                
                // Clear the input
                apiKeyInput.value = '';
                
                // Refresh the page after a short delay
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } catch (error) {
                // Show error message
                resultDiv.innerHTML = `<div class="alert alert-danger mt-2">${error.message || 'An error occurred while updating the API key.'}</div>`;
            }
        });
    }
});
