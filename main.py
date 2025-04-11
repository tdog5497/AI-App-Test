from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import fitz  # PyMuPDF
import os

app = Flask(__name__)
client = OpenAI()  # Uses OPENAI_API_KEY from environment

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('pdf')
    if not file:
        return jsonify({'error': 'No file uploaded'}), 400

    try:
        # Extract text from PDF
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()

        # Format: Question: Answer
        prompt = (
            "Generate 10 flashcards based on the following study material. "
            "Format each flashcard on a new line with the question and answer separated by a colon. "
            "Example: What is the capital of France?: Paris\n\n"
            f"{text[:3000]}"
        )

        print("PROMPT SENT TO OPENAI:\n", prompt)  # optional log for debugging

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        flashcards = response.choices[0].message.content
        return jsonify({'flashcards': flashcards})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
