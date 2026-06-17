# J.a.r.v.i.s (Reactive Virtual Intelligence System)

Local development setup guide for the J.a.r.v.i.s React/FastAPI stack. This system uses GitHub Models (gpt-4o-mini) for routing.

## Prerequisites
- Node.js & npm (Frontend)
- Python 3.8+ (Backend)
- GitHub Account (For LLM inference token)
- Vercel CLI: `npm install -g vercel`
- Railway CLI: `npm install -g @railway/cli`

---

## Step 1: Set Up the AI Backend (Python)

1. Navigate to the backend directory:
   cd backend

2. Create and activate a virtual environment:
   # Mac/Linux:
   Note: If you are on Ubuntu/WSL and get a "venv not found" error, run sudo apt install python3-venv first.

   python3 -m venv venv
   source venv/bin/activate
   
   # Windows:
   python -m venv venv
   venv\Scripts\activate

> [!WARNING]
> **Important: Virtual Environment Location**
> To avoid dependency conflicts and editor confusion, all Python packages must be kept strictly within the `backend/` directory. 
> 
> * **Do not** let VS Code automatically create a `.venv` folder in the root project directory.
> * Always ensure you have navigated into the backend (`cd backend`) before running your `venv` activation command.
> If you accidentally create a `.venv` in the root folder, delete it immediately before proceeding to install any dependencies.

3. Install dependencies:
   pip install -r requirements.txt

> [!TIP]
> **VS Code Users: Select the Correct Interpreter**
> To prevent VS Code from showing "missing import" errors, you need to point it to the virtual environment you just created.
> 
> 1. Open any Python file in the repository (e.g., `backend/main.py`).
> 2. Press `Ctrl + Shift + P` (Windows/Linux) or `Cmd + Shift + P` (Mac) to open the Command Palette.
> 3. Type and select **`Python: Select Interpreter`**.
> 4. Choose the interpreter that points to your backend environment:
>    - **Mac/Linux:** Look for `./backend/venv/bin/python`
>    - **Windows:** Look for `.\backend\venv\Scripts\python.exe`

4. Configure environment variables:
   - Create a `.env` file in the root of the `backend` folder with the following keys.
   - Get these values from the project owner (do not commit this file):
     GITHUB_TOKEN=ghp_your_token_here
     SUPABASE_URL=your_supabase_url
     SUPABASE_KEY=your_supabase_key
     GOOGLE_CLIENT_ID=your_google_client_id
     GOOGLE_CLIENT_SECRET=your_google_client_secret
     GOOGLE_REFRESH_TOKEN=your_google_refresh_token

5. Start the backend server locally:
   uvicorn main:app --reload

---

## Step 2: Set Up the Frontend (React)

Open a second terminal instance.

1. Navigate to the frontend directory:
   cd frontend

2. Install dependencies:
   npm install

3. Create a `.env` file in the `frontend` folder:
   VITE_API_URL=http://localhost:8000

4. Start the frontend locally:
   npm run dev

---

## Step 3: Deploying to Production

### Backend (Railway)

1. Install the Railway CLI and log in:
   npm install -g @railway/cli
   railway login

   - Ask the project owner to add you to the Railway project at railway.app.

2. Link to the existing Railway project:
   cd backend
   railway link

   - Select the correct project and service when prompted.

3. Deploy the backend:
   railway up

4. Ensure all environment variables are set in Railway:
   - Go to railway.app → your project → your service → Variables tab.
   - Add all keys from your `.env` file if not already present.

### Frontend (Vercel)

1. Install the Vercel CLI and log in:
   npm install -g vercel
   vercel login

   - Ask the project owner to add you to the Vercel project at vercel.com → project → Settings → Members.

2. Link to the existing Vercel project:
   cd frontend
   vercel link

   - Select the correct project when prompted.

3. Deploy the frontend:
   vercel --prod

4. Ensure VITE_API_URL is set in Vercel:
   - Go to vercel.com → your project → Settings → Environment Variables.
   - Key: VITE_API_URL
   - Value: https://your-railway-app.up.railway.app (get this from the project owner)

---

## Step 4: View the API Documentation

FastAPI automatically generates interactive API documentation. Ensure the backend is running, then navigate to:

- Interactive Swagger UI: http://localhost:8000/docs
- Static ReDoc Reference: http://localhost:8000/redoc
- Raw OpenAPI Schema: http://localhost:8000/openapi.json

---

## Troubleshooting

- Blank UI on Vercel: Check that VITE_API_URL is set correctly in Vercel environment variables and redeploy with `vercel --prod`.
- Bad Gateway / System Offline: Verify the backend is running and the `.env` file is properly configured.
- Railway deploy fails: Ensure all environment variables are set in the Railway Variables tab.
- UI broken: Ensure `npm install` was run to install all `@mui/material` dependencies.