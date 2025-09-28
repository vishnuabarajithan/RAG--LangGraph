**Table of contents**

_Installation (local)

Quick start

Project structure

Configuration / Environment Variables

Run (development)_



**1. Installation (local)**

These instructions show how to run the project locally on Windows, macOS, or Linux using a Python virtual environment (recommended). The repository already contains the modularized code:

app.py — Flask server and endpoints

rag_agent_module.py — RAG agent factory and graph logic

vectorstore_module.py — PDF loading, splitting, building Chroma vectorstore

templates/index.html & static/main.js — frontend UI

requirements.txt — Python dependencies

Use Python 3.10+ (3.11/3.12 are fine). Some language model/embeddings libraries may require specific versions — test in a venv.

A. Clone the repository
git clone https://github.com/<your-username>/rag-prototype.git
cd rag-prototype


(Or unzip the project folder you downloaded.)

B. Create & activate a virtual environment

macOS / Linux

python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip setuptools wheel


Windows (PowerShell)

python -m venv venv
.\venv\Scripts\Activate.ps1
# If activation is blocked: run once: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
python -m pip install --upgrade pip setuptools wheel


Windows (cmd)

python -m venv venv
venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel

C. Install Python dependencies
pip install -r requirements.txt


If you run into permission errors (Access is denied), either:

use python -m pip install --user -r requirements.txt (user site), or

ensure your venv is activated and run python -m pip install -r requirements.txt, or

run PowerShell as Administrator (not recommended for general use).

**2. Quick start**

Ensure the virtual environment is active and dependencies are installed.

Set environment variables (see below).

Start the Flask server:

python app.py


Open your browser and go to: http://127.0.0.1:5000

UI workflow:

Drag & drop a PDF or click choose file and pick a PDF — the file auto-uploads and a progress bar shows upload progress.

Type your question in the text area and press Enter to submit (Shift+Enter for newline).

The assistant will respond in the messages area.

**3. Project structure**
.
├── app.py                      # Flask app, endpoints: /upload, /ask
├── rag_agent_module.py         # Builds the RAG StateGraph agent & tools
├── vectorstore_module.py       # Loads PDF, splits text, creates Chroma vectorstore
├── templates/
│   └── index.html              # Front-end UI
├── static/
│   └── main.js                 # Front-end JS (drag-drop, auto-upload, keyboard handling)
├── requirements.txt
└── README.md

**4. Configuration / Environment Variables**

GOOGLE_API_KEY — (optional) If you're using Google GenAI (Gemini) LLM & embeddings, set this environment variable to your API key. The project uses ChatGoogleGenerativeAI and GoogleGenerativeAIEmbeddings by default (matching the original code).

Set it in your shell:

macOS / Linux

export GOOGLE_API_KEY="your_google_api_key"


Windows (PowerShell)

$env:GOOGLE_API_KEY = "your_google_api_key"
# or persistently:
setx GOOGLE_API_KEY "your_google_api_key"


If you want to use OpenAI instead of Google, you’ll need to edit rag_agent_module.py and vectorstore_module.py to change LLM and embeddings settings (not included by default).

**5. Run (development)**

Start the server:

python app.py


You should see Flask logs; navigate to http://127.0.0.1:5000.
Frontend features:

Drag & drop upload area, auto-upload

Inline progress & status (no alert popups)

Rounded UI, glossy beige buttons

Enter to submit question, Shift+Enter to insert newline
