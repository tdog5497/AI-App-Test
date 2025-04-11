from flask import Flask, render_template, request, jsonify
import openai
import fitz  # PyMuPDF
import os

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['pdf']
    if not file:
        return jsonify({'error': 'No file uploaded'}), 400

    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()

    prompt = f"Create 10 flashcards based on this content:\n\n{text[:3000]}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return jsonify({'flashcards': response['choices'][0]['message']['content']})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
