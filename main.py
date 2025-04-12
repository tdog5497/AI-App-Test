from flask import Flask, render_template, request, jsonify, send_from_directory
from openai import OpenAI
import fitz  # PyMuPDF
import os
import json
import re

app = Flask(__name__)
client = OpenAI()

DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('pdf')
    set_name = request.form.get('setName', 'Untitled Set')

    if not file:
        return jsonify({'error': 'No file uploaded'}), 400

    try:
        # Read PDF content
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()

        # Prompt with formatting
        prompt = (
            "Generate 10 flashcards based on the following study material. "
            "Format each flashcard on a new line with the question and answer separated by a colon. "
            "Example: What is the capital of France?: Paris\n\n"
            f"{text[:3000]}"
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        content = response.choices[0].message.content

        # Parse flashcards
        flashcards = []
        for line in content.strip().split("\n"):
            if ':' in line:
                q, a = line.split(':', 1)
                flashcards.append({"question": q.strip(), "answer": a.strip()})

        # Save flashcards to file
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', set_name)
        file_path = os.path.join(DATA_FOLDER, f"{safe_name}.json")

        with open(file_path, "w") as f:
            json.dump(flashcards, f, indent=2)

        return jsonify({"success": True, "flashcards": flashcards})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sets')
def list_sets():
    sets = []
    for filename in os.listdir(DATA_FOLDER):
        if filename.endswith('.json'):
            sets.append(filename.replace('.json', ''))
    return jsonify({"sets": sets})

@app.route('/sets/<set_name>')
def get_set(set_name):
    file_path = os.path.join(DATA_FOLDER, f"{set_name}.json")
    if not os.path.exists(file_path):
        return jsonify({"error": "Set not found"}), 404
    with open(file_path, "r") as f:
        flashcards = json.load(f)
    return jsonify({"flashcards": flashcards})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
