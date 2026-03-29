import os
import json
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from generator import process_identity_generation

app = Flask(__name__)
CORS(app)

DATA_FILE = 'data.json'

def load_data():
    """Load personas from the JSON file."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r') as f:
            content = f.read()
            if not content:
                return []
            return json.loads(content)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_data(data):
    """Save personas to the JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/personas', methods=['GET'])
def get_personas():
    """Fetch all stored personas."""
    return jsonify(load_data())

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json(silent=True) or {}
    p1 = data.get('p1')
    p2 = data.get('p2')
    user_context = data.get('context') # Capture the new field

    is_merge = bool(p1 and p2)

    MAX_ATTEMPTS = 3
    final_identity = None

    for attempt in range(MAX_ATTEMPTS):
        print(f"Generation attempt {attempt + 1}/{MAX_ATTEMPTS} ({'merge' if is_merge else 'random'})...")

        new_identity = process_identity_generation(p1, p2, user_context) if is_merge else process_identity_generation(None, None, user_context)

        if new_identity and new_identity.get('name') and new_identity.get('name') != "N/A":
            personas = load_data()
            new_name = new_identity['name']

            # Reject if any existing persona shares the same name
            is_duplicate = any(
                p.get('name', '').lower() == new_name.lower()
                for p in personas
            )

            if not is_duplicate:
                final_identity = new_identity
                break
            else:
                print(f"  Name '{new_name}' already exists. Retrying...")

    if final_identity:
        final_identity['id'] = int(time.time() * 1000)
        personas = load_data()
        personas.insert(0, final_identity)
        save_data(personas)
        return jsonify(final_identity)
    else:
        return jsonify({"error": "Failed to generate a unique identity after several attempts."}), 500

@app.route('/personas/<int:p_id>', methods=['DELETE'])
def delete_persona(p_id):
    """Delete a persona by ID."""
    personas = load_data()
    personas = [p for p in personas if p.get('id') != p_id]
    save_data(personas)
    return jsonify({"success": True})

if __name__ == '__main__':
    print("Sentry AI Backend running on http://localhost:5000")
    app.run(port=5000, debug=True)