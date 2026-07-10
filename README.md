# J.a.r.v.i.s (Reactive Virtual Intelligence System)

Local development setup guide for the J.a.r.v.i.s React/FastAPI stack. This system uses GitHub Models (gpt-4o-mini) for routing.

## Prerequisites
- Node.js & npm (Frontend)
- Python 3.8+ (Backend)
- GitHub Account (For LLM inference token)

---

## Step 1: Set Up the AI Backend (Python)

1. Navigate to the backend directory:
   cd backend

2. Create and activate a virtual environment:
   # Mac/Linux:
   python3 -m venv venv
   source venv/bin/activate
   
   # Windows:
   python -m venv venv
   venv\Scripts\activate

3. Install dependencies (FastAPI, Uvicorn, and OpenAI SDK):
   pip install fastapi uvicorn pydantic python-dotenv openai supabase

4. Configure AI inference token:
   - Go to GitHub Settings > Developer settings > Personal access tokens > Tokens (classic).
   - Generate a new token (no scopes required).
   - Create a `.env` file in the root of the `backend` folder and add:
     GITHUB_TOKEN=ghp_your_token_here

5. Start the backend server
   python main.py

---

## Step 2: Set Up the Frontend (React)

Open a second terminal instance.

1. Navigate to the frontend directory:
   cd frontend

2. Install dependencies:
   npm install

3. Start the development server:
   npm run dev

---

## Step 3: View the API Documentation

FastAPI automatically generates interactive API documentation based on the backend routing map. Ensure the backend server is running, then navigate to the following local URLs in your browser to view the endpoints:

- Interactive Swagger UI: http://localhost:8000/docs
  (Use this interface to test API endpoints directly from the browser)

- Static ReDoc Reference: http://localhost:8000/redoc
  (Provides a clean, readable layout of all API routes and expected JSON schemas)

- Raw OpenAPI Schema: http://localhost:8000/openapi.json
  (Use this file to import the API structure into external tools like Postman)

---

## Troubleshooting

- Bad Gateway / System Offline: Verify the backend is running on port 8000 and the `.env` file is properly formatted in the backend root directory.
- UI broken: Ensure `npm install` was run to install all `@mui/material` dependencies.