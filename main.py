from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import fitz  # PyMuPDF
import os
import json
import re

app = Flask(__name__, template_folder='templates', static_folder='static')

client = OpenAI()  # Will use OPENAI_API_KEY env variable

DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

prompt_template = (
    "You're a legal tutor helping a student prepare for law school exams. "
    "Generate useful flashcards from the following outline. Format them as:\n"
    "Question: ...\nAnswer: ...\n\nOnly include flashcards that would be helpful for reviewing this material.\n\n{}"
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
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = "".join([page.get_text() for page in doc])

        chunks = [text[i:i+3000] for i in range(0, len(text), 3000)]
        all_flashcards = []

        for chunk in chunks:
            if len(all_flashcards) >= 300:
                break

            prompt = prompt_template.format(chunk)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )

            lines = response.choices[0].message.content.strip().split('\n')
            current_question = None

            for line in lines:
                line = line.strip()
                if line.lower().startswith("question:"):
                    current_question = line.split(":", 1)[1].strip()
                elif line.lower().startswith("answer:") and current_question:
                    answer = line.split(":", 1)[1].strip()
                    all_flashcards.append({
                        "question": current_question,
                        "answer": answer
                    })
                    current_question = None

                if len(all_flashcards) >= 300:
                    break

        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', set_name)
        file_path = os.path.join(DATA_FOLDER, f"{safe_name}.json")

        with open(file_path, "w") as f:
            json.dump(all_flashcards, f, indent=2)

        return jsonify({"success": True, "flashcards": all_flashcards})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
