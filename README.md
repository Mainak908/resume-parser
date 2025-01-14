# Resume Parser API

![resume-parser](https://github.com/user-attachments/assets/97bd4fe5-7e7f-43dc-9e60-71b0ed54877e)

API that accepts PDF or DOCX resumes converts them to text and uses OpenRouter API to extract structured information.

## Why

Resume parsing is expensive and requires monthly fees. For low volume, it can cost around $0.10 per resume. Using this API, the cost is at least 100x cheaper with no monthly commitment.

## Limitations
As it is LLM-based, results might be inconsistent or missing some info; use caution.

The parsing time is longer than the traditional resume parser, based on resume length, model TPS (Tokens Per Second), and model load.

## Setup

1. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your OpenRouter API key:
```
OPENROUTER_API_KEY=your_api_key_here
```

## Usage

1. Start the server:
```bash
python app.py
```

2. Send a POST request to `/parse` endpoint with a resume file:
```bash
curl -X POST -F "file=@path/to/resume.pdf" http://localhost:5000/parse
```

The API accepts both PDF and DOCX files and returns a structured JSON response containing the parsed resume information.

## Response Format

The API returns a JSON object based on the schema in the `config.yml` file. The default one would return the following structure:
- basics (name, contact info, location, etc.)
- work experience
- education
- skills
- languages
- interests
- certifications
- awards
- publications
- projects
- volunteer work
- references
- custom sections
- metadata

## Error Handling

The API returns appropriate error messages for:
- Missing files
- Invalid file types
- File processing errors
- AI processing errors

## File Size Limit

The maximum file size is 16MB. It can be changed from the `config.yml` file.

