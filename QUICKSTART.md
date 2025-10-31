# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Backend Setup (Terminal 1)

```bash
# Navigate to project root
cd appointment-scheduling-agent

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run backend
cd backend
uvicorn main:app --reload
```

Backend will run at: `http://localhost:8000`

### 2. Frontend Setup (Terminal 2)

```bash
# Navigate to frontend directory
cd appointment-scheduling-agent/frontend

# Install dependencies
npm install

# Run frontend
npm run dev
```

Frontend will run at: `http://localhost:5173`

### 3. Test the Application

1. Open `http://localhost:5173` in your browser
2. Try these commands:
   - "I need to book an appointment"
   - "What are your operating hours?"
   - "Do you accept insurance?"

### ✅ Verification Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] OpenAI API key set in `.env`
- [ ] Can access API docs at `http://localhost:8000/docs`
- [ ] Chat interface loads in browser
- [ ] Can send messages and receive responses

## 🐛 Common Issues

**Backend won't start:**
- Check Python version: `python --version` (needs 3.10+)
- Verify dependencies: `pip list | grep fastapi`
- Check .env file exists and has OPENAI_API_KEY

**Frontend won't connect:**
- Ensure backend is running first
- Check browser console for errors
- Verify CORS settings in backend/main.py

**ChromaDB errors:**
- Delete `./chroma_db` folder and restart
- Vector store will reinitialize automatically

