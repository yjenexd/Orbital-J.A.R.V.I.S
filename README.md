J.a.r.v.i.s (Reactive Virtual Intelligence System)

Welcome to the local testing environment for J.a.r.v.i.s. This project consists of a React frontend built with Material UI, powered by a Python FastAPI backend that routes requests to enterprise-grade Large Language Models via the GitHub Models API.

Follow these steps to get both the UI and the AI engine running on your local machine.

Prerequisites
Before you begin, ensure you have the following installed:

Node.js & npm: For running the React frontend.

Python 3.8+: For running the FastAPI backend.

A GitHub Account: To generate a free developer token for the AI model.

Step 1: Set Up the AI Backend (Python)
The backend acts as the orchestrator, enforcing schedule constraints and communicating with the AI.

1. Navigate to the backend directory
Open a terminal and navigate into the backend folder:

Bash
cd backend
2. Create and activate a Virtual Environment
This keeps the project dependencies isolated.

Mac/Linux:

Bash
python -m venv venv
source venv/bin/activate

Windows:

Bash
python -m venv venv
venv\Scripts\activate

3. Install Dependencies
With the virtual environment active (venv), install the required Python packages:

Bash
pip install fastapi uvicorn pydantic python-dotenv openai

4. Generate your free GitHub AI Token
To allow J.a.r.v.i.s to think, you need a free testing token.

Log into GitHub and go to Settings > Developer settings > Personal access tokens > Tokens (classic).

Click Generate new token (classic).

Give it a name (e.g., "Jarvis Testing"), set an expiration, and leave all permission checkboxes completely blank.

Click Generate and copy the long ghp_... string.

5. Configure your Environment Variables
In the root of the backend folder, create a file named exactly .env. Paste your token inside it like this:

Plaintext
GITHUB_TOKEN=ghp_your_copied_token_here

6. Start the Server
Run the backend server. It will boot up on port 8000.

Bash
uvicorn main:app --reload
💻 Step 2: Set Up the Frontend (React)
Open a second, separate terminal window (leave the Python server running in the first one).

1. Navigate to the frontend directory
Go to the root of the React project:

Bash
cd frontend
2. Install Node Modules
Install the necessary React and Material UI dependencies:

Bash
npm install
3. Start the UI Server
Launch the development server:

Bash
npm run dev
# Note: If this project uses Create React App instead of Vite, use `npm start`

Step 3: Test the System
Open your browser and navigate to the local host address provided by your React terminal (usually http://localhost:3000 or http://localhost:5173).

You should see the J.a.r.v.i.s Chat Interface.

Type a message, such as: "Can you schedule a meeting for me on June 5, 2026?"

J.a.r.v.i.s should decline the request, citing an overseas trip to China, confirming that both the AI connection and the custom backend constraints are working perfectly!

Troubleshooting
"System offline" or "Bad Gateway" in the chat: Ensure your Python backend terminal is running and that your .env file is named correctly and placed inside the backend folder.

UI styling looks broken: Ensure you ran npm install to grab the @mui/material packages.