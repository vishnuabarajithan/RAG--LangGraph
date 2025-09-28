import os
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from rag_agent_module import create_rag_agent
from vectorstore_module import build_vectorstore_from_pdf

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

GLOBAL_STATE = {
    'rag_agent': None,
    'retriever_tool': None,
    'vectorstore': None
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        try:
            retriever, vectorstore = build_vectorstore_from_pdf(save_path)
        except Exception as e:
            return jsonify({'error': f'Error building vectorstore: {e}'}), 500

        rag_agent, retriever_tool = create_rag_agent(retriever, vectorstore)

        GLOBAL_STATE['rag_agent'] = rag_agent
        GLOBAL_STATE['retriever_tool'] = retriever_tool
        GLOBAL_STATE['vectorstore'] = vectorstore

        return jsonify({'message': 'File uploaded and vectorstore created'}), 200

    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json or {}
    question = data.get('question', '')
    if not question:
        return jsonify({'error': 'No question provided'}), 400

    rag_agent = GLOBAL_STATE.get('rag_agent')
    retriever_tool = GLOBAL_STATE.get('retriever_tool')

    if rag_agent is None or retriever_tool is None:
        return jsonify({'error': 'No document uploaded. Upload PDF first.'}), 400

    try:
        context = retriever_tool(question)
    except Exception as e:
        return jsonify({'error': f'Retriever error: {e}'}), 500

    user_input = question + "\n\nCONTEXT:\n" + context
    from langchain_core.messages import HumanMessage
    messages = [HumanMessage(content=user_input)]

    try:
        result = rag_agent.invoke({'messages': messages})
    except Exception as e:
        return jsonify({'error': f'Agent invocation error: {e}'}), 500

    try:
        answer = result['messages'][-1].content
    except Exception:
        answer = str(result)

    return jsonify({'answer': answer}), 200

if __name__ == '__main__':
    app.run(debug=True)
