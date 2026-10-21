# Quiz App - Flask Backend

A Python Flask backend for the Quiz Application with Firebase authentication, AI-powered quiz generation, and real-time multiplayer support.

## 🏗️ Project Structure

```
flask-backend/
├── app.py                 # Main Flask application entry point
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create from .env.example)
├── .env.example           # Example environment variables
├── firebase-credentials.json  # Firebase service account (you need to add this)
│
├── routes/                # API route handlers
│   ├── __init__.py
│   ├── auth.py           # Authentication endpoints
│   ├── quiz.py           # Quiz generation endpoints
│   ├── pdf.py            # PDF processing endpoints
│   ├── history.py        # Quiz history endpoints
│   └── health.py         # Health check endpoint
│
├── services/             # Business logic services
│   ├── __init__.py
│   ├── firebase_auth.py  # Firebase authentication service
│   ├── database.py       # MongoDB database operations
│   ├── groq_ai.py        # Groq AI quiz generation
│   └── pdf_processor.py  # PDF text extraction
│
└── sockets/              # Socket.IO event handlers
    ├── __init__.py
    └── events.py         # Multiplayer WebSocket events
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- MongoDB (Atlas or local)
- Firebase project (for authentication)
- Groq API key (for AI quiz generation)

### Installation

1. **Navigate to the flask-backend directory:**
   ```bash
   cd flask-backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env with your actual values
   ```

5. **Set up Firebase credentials:**
   - Go to Firebase Console → Project Settings → Service Accounts
   - Click "Generate New Private Key"
   - Save as `firebase-credentials.json` in the flask-backend directory

6. **Run the application:**
   ```bash
   python app.py
   ```

The server will start at `http://localhost:5000`

## 🔑 Firebase Setup

### 1. Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or use existing one
3. Enable Authentication in the Firebase Console
4. Enable Google Sign-In provider under Authentication → Sign-in method

### 2. Get Service Account Credentials
1. Go to Project Settings → Service Accounts
2. Click "Generate New Private Key"
3. Save the JSON file as `firebase-credentials.json` in the flask-backend directory

### 3. Get Web App Configuration (for Frontend)
1. Go to Project Settings → General
2. Under "Your apps", add a Web app
3. Copy the Firebase configuration for your frontend

## 📡 API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/session` | Create/refresh user session |
| GET | `/api/auth/session` | Get current session |
| POST | `/api/auth/verify` | Verify Firebase token |
| GET | `/api/auth/user` | Get authenticated user details |

### Quiz Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/generate-quiz` | Generate quiz from topic |
| POST | `/api/generate-quiz-from-pdf-chunks` | Generate quiz from PDF chunks |

### PDF Processing

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/process-pdf-chunks` | Process PDF and extract text chunks |

### Quiz History

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/quiz-history` | Get user's quiz history |
| GET | `/api/quiz-history/<id>` | Get specific quiz history |
| POST | `/api/quiz-history` | Save quiz result |
| DELETE | `/api/quiz-history/<id>` | Delete quiz history |

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Server health check |

## 🔌 WebSocket Events

### Client → Server

| Event | Data | Description |
|-------|------|-------------|
| `create-room` | `{roomCode, quiz, metadata, hostName}` | Create multiplayer room |
| `join-room` | `{roomCode, playerName}` | Join existing room |
| `start-quiz` | `{roomCode}` | Start the quiz (host only) |
| `submit-answer` | `{roomCode, questionIndex, questionText, answerIndex, selectedAnswerText, timeSpent}` | Submit answer |
| `remove-player` | `{roomCode, playerName}` | Remove player (host only) |
| `get-leaderboard` | `{roomCode}` | Request leaderboard |

### Server → Client

| Event | Data | Description |
|-------|------|-------------|
| `room-created` | `{roomCode, players}` | Room created successfully |
| `joined-room` | `{roomCode, players}` | Successfully joined room |
| `player-joined` | `{playerName, players, totalPlayers}` | New player joined |
| `quiz-started` | `{currentQuestion, question, totalQuestions, quiz, metadata}` | Quiz started |
| `answer-submitted` | `{isCorrect, correctAnswer, explanation}` | Answer result |
| `player-finished` | `{correctAnswers, totalQuestions, totalTime, avgTime}` | Player completed quiz |
| `quiz-finished` | `{leaderboard, quiz}` | All players finished |
| `player-kicked` | `{message}` | Player was removed |
| `player-left` | `{playerName, totalPlayers}` | Player left room |
| `host-disconnected` | `{}` | Host left, room closing |
| `error` | `{message}` | Error occurred |

## 🔐 Authentication Flow

1. **Frontend authenticates with Firebase** (Google Sign-In)
2. **Frontend gets Firebase ID token**
3. **Frontend sends token to Flask backend** in Authorization header
4. **Flask verifies token** with Firebase Admin SDK
5. **Flask creates/updates user** in MongoDB
6. **Flask returns session data** to frontend

### Making Authenticated Requests

```javascript
// Frontend example
const response = await fetch('http://localhost:5000/api/quiz-history', {
  headers: {
    'Authorization': `Bearer ${firebaseIdToken}`,
    'Content-Type': 'application/json'
  }
});
```

## 🔧 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_APP` | Flask application file | `app.py` |
| `FLASK_ENV` | Environment mode | `development` |
| `FLASK_DEBUG` | Debug mode | `true` |
| `SECRET_KEY` | Flask secret key | Random string |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `5000` |
| `FRONTEND_URL` | Frontend URL for CORS | `http://localhost:3000` |
| `MONGODB_URI` | MongoDB connection string | `mongodb+srv://...` |
| `MONGODB_DB_NAME` | Database name | `quizapp` |
| `FIREBASE_CREDENTIALS_PATH` | Path to Firebase JSON | `./firebase-credentials.json` |
| `GROQ_API_KEY` | Groq API key | `gsk_...` |
| `GROQ_MODEL` | Groq model name | `openai/gpt-oss-20b` |
| `MAX_QUESTIONS_AI` | Maximum questions per topic quiz | `20` |
| `MAX_QUESTIONS_PDF` | Maximum questions per PDF quiz | `50` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:3000` |

## 🔄 Connecting Frontend to Flask Backend

Update your frontend to use the Flask backend:

### 1. Update API Base URL

```javascript
// In your frontend config
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
```

### 2. Update WebSocket URL

```javascript
// In your frontend config
const WEBSOCKET_URL = process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'http://localhost:5000';
```

### 3. Update Authentication

Replace NextAuth with Firebase Client SDK:

```javascript
// Install Firebase
npm install firebase

// Initialize Firebase
import { initializeApp } from 'firebase/app';
import { getAuth, signInWithPopup, GoogleAuthProvider } from 'firebase/auth';

const firebaseConfig = {
  // Your Firebase config from console
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Sign in with Google
const signIn = async () => {
  const provider = new GoogleAuthProvider();
  const result = await signInWithPopup(auth, provider);
  const idToken = await result.user.getIdToken();
  
  // Send token to Flask backend
  await fetch(`${API_BASE_URL}/api/auth/session`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${idToken}`
    }
  });
};
```

## 🐳 Docker Support

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

Build and run:

```bash
docker build -t quiz-flask-backend .
docker run -p 5000:5000 --env-file .env quiz-flask-backend
```

## 📝 License

MIT License
