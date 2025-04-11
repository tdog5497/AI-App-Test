from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import fitz  # PyMuPDF
import os

app = Flask(__name__)
client = OpenAI()  # Reads OPENAI_API_KEY from the environment

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('pdf')
    if not file:
        return jsonify({'error': 'No file uploaded'}), 400

    try:
        # Read text from uploaded PDF
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()

        # Prompt to generate flashcards
        prompt = f"Create 10 flashcards based on the following study material:\n\n{text[:3000]}"

        # Use gpt-3.5-turbo (universally available)
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
