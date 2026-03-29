#### Overview
Sentry AI is a full-stack identity generation engine designed for data obfuscation and privacy preservation. The system enables users to generate realistic, grounded personas to protect their own information, reducing the need to share authentic personal information with third-party trackers or data brokers.

#### Technical Architecture
The project is split into a decoupled client-server architecture:

*   **Backend (Python/Flask):** Acts as the orchestration layer. It manages persona persistence via a flat-file JSON database and interfaces with local Large Language Models (LLMs) for content generation.
*   **Generation Engine (Ollama Integration):** Utilizes `llama3.2` (3b) via a local Ollama API. This ensures that the generation process remains private and offline. It employs structured prompt engineering to produce specific JSON-mapped fields while using Python-based algorithmic generators for deterministic data (SSNs, phone numbers, and age distributions).
*   **Frontend (HTML5/Tailwind/JS):** A single-page application (SPA) that provides a dashboard for persona management and a visual "Merger Workspace."

#### Key Features
1.  **Synthetic Identity Generation:** Produces comprehensive profiles including professional backgrounds, education, contact details, and unique biographies.
2.  **Identity Merging:** A unique feature allowing users to drag and drop two "parent" personas into a workspace to generate a "merged" identity. The LLM analyzes the traits of both inputs to create a distinct, plausible hybrid.
3.  **Local-First Privacy:** By relying on a local LLM instance (Ollama), the project avoids sending potentially sensitive context to external cloud providers.
4.  **Contextual Awareness:** The generation prompt allows for "user context," enabling the LLM to steer persona creation toward specific industries, locations, or roles based on user needs.

#### How to Use
Ensure Ollama is installed with the model `llama3.2:latest` downloaded using `ollama pull llama3.2:latest`
Ensure all libraries are installed, install them using `pip install flask flask-cors requests`
Ensure Ollama is serving on port 11434 (just put `ollama list` in a window or run `ollama serve`)
Run `app.py` to start the Flask server
Double-click `index.html` to start

#### Tech Stack
*   **Frontend:** Tailwind CSS, Lucide Icons, Vanilla JavaScript.
*   **Backend:** Flask, Flask-CORS, Requests.
*   **Inference:** Ollama (`llama3.2:latest`).
*   **Storage:** Local JSON (`data.json`).
