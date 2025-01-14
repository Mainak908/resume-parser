import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from markitdown import MarkItDown
import requests
import magic
from dotenv import load_dotenv
import json
import yaml

load_dotenv()


def load_config():
    with open("config.yml", "r") as config_file:
        return yaml.safe_load(config_file)


# Load configuration
config = load_config()
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = int(config["general"]["max_file_size"])
app.config["UPLOAD_FOLDER"] = config["general"]["upload_folder"]

# Ensure upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "docx"}
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_markdown(file_path):
    md = MarkItDown()
    return str(md.convert(file_path).text_content)


def process_resume_with_ai(text):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": config["site"]["url"],
        "X-Title": config["site"]["name"],
    }

    prompt = f"""Please analyze this resume and extract information into a structured format.
    Here's the resume text:
    {text}

    Please provide the information in a structured JSON format following the schema provided.
    Only include fields where information is available in the resume.
    Make sure the output is valid JSON."""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json={
            "models": config["models"][0:2],
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {
                "type": "json_schema",
                "schema": config["resume_schema"],
            },
        },
    )

    if response.status_code != 200:
        print(response.json())
        raise Exception("Failed to process with AI")

    result = response.json()
    print(result)
    try:
        # Extract the JSON from the AI response
        content = result["choices"][0]["message"]["content"]
        # Find the JSON part in the response
        start_idx = content.find("{")
        end_idx = content.rfind("}") + 1
        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx]
            return json.loads(json_str)
        return json.loads(content)
    except Exception as e:
        raise Exception(f"Failed to parse AI response: {str(e)}")


@app.route("/parse", methods=["POST"])
def parse_resume():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return (
            jsonify(
                {"error": "Invalid file type. Only PDF and DOCX files are allowed"}
            ),
            400,
        )

    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        # Detect file type using python-magic
        file_type = magic.from_file(file_path, mime=True)

        # Extract text based on file type
        if (
            file_type == "application/pdf"
            or file_type
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            text = extract_markdown(file_path)
        else:
            os.remove(file_path)
            return jsonify({"error": "Unsupported file type"}), 400

        # Process with AI
        result = process_resume_with_ai(text)

        # Clean up
        os.remove(file_path)

        return jsonify(result)

    except Exception as e:
        # Clean up in case of error
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
