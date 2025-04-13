from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import fitz  # PyMuPDF
import os
import json
import re

app = Flask(__name__)
client = OpenAI()

DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

# 🔧 You can tweak this prompt anytime
prompt_template = (
    "You're a legal tutor helping a student prepare for law school exams. "
    "Generate useful flashcards from the following outline. Each flashcard should be on one line, "
    "formatted like: Question: Answer. Focus on exam-relevant rules, doctrines, and distinctions. "
    "Avoid general or filler info. Begin:\n\n{}"
)

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
        # Extract text from uploaded PDF
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()

        # Chunk the text into ~3000 character segments
        chunks = [text[i:i+3000] for i in range(0, len(text), 3000)]
        all_flashcards = []

        for chunk in chunks:
            if len(all_flashcards) >= 300:
                break  # limit total output to 300 cards

            prompt = prompt_template.format(chunk)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )

            lines = response.choices[0].message.content.strip().split('\n')
            for line in lines:
                if ':' in line and len(all_flashcards) < 300:
                    q, a = line.split(':', 1)
                    all_flashcards.append({
                        "question": q.strip(),
                        "answer": a.strip()
                    })

        # Save flashcards to JSON file
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', set_name)
        file_path = os.path.join(DATA_FOLDER, f"{safe_name}.json")

        with open(file_path, "w") as f:
            json.dump(all_flashcards, f, indent=2)

        return jsonify({"success": True, "flashcards": all_flashcards})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/sets')
def list_sets():
    sets = []
    for filename in os.listdir(DATA_FOLDER):
        if filename.endswith('.json'):
            sets.append(filename.replace('.json', ''))
    return render_template('sets.html', sets=sets)

@app.route('/sets/<set_name>')
def get_set(set_name):
    file_path = os.path.join(DATA_FOLDER, f"{set_name}.json")
    if not os.path.exists(file_path):
        return "Flashcard set not found", 404
    with open(file_path, "r") as f:
        flashcards = json.load(f)
    return render_template('flashcards.html', set_name=set_name, flashcards=flashcards)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
