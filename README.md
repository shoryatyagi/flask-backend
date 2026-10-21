# Quiz App - Flask Backend

A Python Flask backend for the Quiz Application with Firebase authentication, AI-powered quiz generation, and real-time multiplayer support.

Frontend: [QuizMaster Next.js repository](https://github.com/shoryatyagi/A.I.-Quiz). For the walkthrough video and frontend setup, see its [README](https://github.com/shoryatyagi/A.I.-Quiz#readme).

## Run locally

### Prerequisites

- Python 3.9 or newer and pip
- MongoDB Atlas or local MongoDB
- Firebase project with Authentication enabled
- Groq API key for AI quiz generation

### 1. Install and configure

Clone this repository, open a terminal in its root, and create a virtual environment:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

On macOS/Linux, use `python3 -m venv .venv`, `source .venv/bin/activate`, and `cp .env.example .env`.

Edit `.env` and provide `MONGODB_URI`, `MONGODB_DB_NAME`, `GROQ_API_KEY`, a strong random `SECRET_KEY`, and the local CORS values `FRONTEND_URL=http://localhost:3000` and `ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000`. Set `FIREBASE_CREDENTIALS_PATH` to the Firebase Admin service-account file. Download that JSON from Firebase Console → Project settings → Service accounts and save it as `firebase-credentials.json` in this folder. Never commit `.env` or the service-account file.

### 2. Start and check the API

```powershell
python app.py
```

The API listens on `http://localhost:5000`. Check `http://localhost:5000/api/health`. Keep this process running while the frontend is running; configure the frontend's `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_SOCKET_URL` as `http://localhost:5000`. See the [frontend README](https://github.com/shoryatyagi/A.I.-Quiz#run-locally) for its complete setup. Stop the server with `Ctrl+C`.

## Run backend with Docker

Configure `.env` and provide the Firebase credential file first. From the backend repository root:

```powershell
docker compose up --build flask-backend
```

This starts the backend on port 5000. The compose file also defines an optional local MongoDB service; to use it, start both services with `docker compose up --build` and set `MONGODB_URI` to a URI reachable from the backend container, such as `mongodb://mongodb:27017/`. Stop with `Ctrl+C`, then run `docker compose down`. The optional MongoDB data volume remains until explicitly removed.

## Deploy the application to AWS

The application has two AWS deployment paths, documented in the frontend repository because its EC2 helper builds both images from the sibling repositories:

### Scalable ECS/Fargate deployment

1. Read the full [ECS/Fargate guide](https://github.com/shoryatyagi/A.I.-Quiz/blob/develop/deploy/aws/README.md) and check its cost notes. It creates load balancing, NAT, Fargate services, Redis, ECR, CloudWatch resources, and networking; charges can continue until teardown.
2. Prepare AWS CLI access and a budget alert. Put the MongoDB URI, Groq key, Firebase Admin service-account JSON, Flask secret, and Redis token into AWS Secrets Manager. Keep secret values out of Git.
3. Create the OIDC provider and deploy the CloudFormation template described in the guide. Add the resulting NAT Gateway EIP to the MongoDB Atlas allowlist.
4. Set the required GitHub Actions variables and workflow access in both the frontend and backend repositories. The backend deployment branch is `master`; push to it or run the workflow manually.
5. Confirm the backend ECS service reaches a healthy state, inspect its CloudWatch logs and target health, then test API and Socket.IO behavior through the frontend's `AppUrl`.
6. Delete the CloudFormation stack after the demo; empty ECR repositories first if AWS reports they block deletion.

### Single EC2 trial deployment

1. Read the full [EC2 deployment guide](https://github.com/shoryatyagi/A.I.-Quiz/blob/develop/deploy/ec2/README.md). This is an HTTP single-instance trial and does not provide production HTTPS.
2. Clone this backend beside the frontend repository, install Docker Desktop, AWS CLI v2, and Windows OpenSSH, then authenticate AWS CLI with an appropriately limited non-root identity.
3. Follow the frontend guide to create and complete `deploy/ec2/.env.deploy`; it carries the backend secrets and must stay private.
4. From the frontend repository root in PowerShell, run `Set-ExecutionPolicy -Scope Process Bypass` and `.\deploy\ec2\deploy.ps1`. Restrict SSH access to your public IP `/32`; review the resource prompt and type `DEPLOY` to proceed.
5. Add the instance IP to MongoDB's allowlist if required, authorize the host in Firebase Authentication, and open the printed HTTP URL.
6. To clean up, run `.\deploy\ec2\destroy.ps1` from the frontend repository and type `DELETE`. The helper removes the instance and its supporting resources.

For the walkthrough video, end-to-end local steps, and frontend deployment details, use the [frontend README](https://github.com/shoryatyagi/A.I.-Quiz#readme).

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
