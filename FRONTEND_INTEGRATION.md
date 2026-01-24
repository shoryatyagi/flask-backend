# Frontend Integration Guide

This guide explains how to connect your Next.js frontend to the Flask backend with Firebase authentication.

## 1. Install Firebase in Frontend

```bash
cd my-app
npm install firebase
```

## 2. Create Firebase Configuration

Create `src/lib/firebase.js`:

```javascript
import { initializeApp, getApps } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut } from 'firebase/auth';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

// Initialize Firebase
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

export { auth, googleProvider, signInWithPopup, signOut };
```

## 3. Update Environment Variables

Add to your `.env.local`:

```env
# Flask Backend URL
NEXT_PUBLIC_API_URL=http://localhost:5000
NEXT_PUBLIC_WEBSOCKET_URL=http://localhost:5000

# Firebase Client Configuration (from Firebase Console)
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id
```

## 4. Create Auth Context

Create `src/context/AuthContext.js`:

```javascript
'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { auth, googleProvider, signInWithPopup, signOut } from '@/lib/firebase';
import { onAuthStateChanged } from 'firebase/auth';

const AuthContext = createContext({});

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        // Get Firebase ID token
        const idToken = await firebaseUser.getIdToken();
        
        // Create session with Flask backend
        try {
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/session`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${idToken}`,
              'Content-Type': 'application/json',
            },
          });
          
          const data = await response.json();
          
          setUser({
            ...data.user,
            idToken,
            getIdToken: () => firebaseUser.getIdToken(),
          });
        } catch (error) {
          console.error('Session error:', error);
          setUser(null);
        }
      } else {
        setUser(null);
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const signIn = async () => {
    try {
      await signInWithPopup(auth, googleProvider);
    } catch (error) {
      console.error('Sign in error:', error);
      throw error;
    }
  };

  const logOut = async () => {
    try {
      await signOut(auth);
      setUser(null);
    } catch (error) {
      console.error('Sign out error:', error);
      throw error;
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, signIn, logOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
```

## 5. Create API Helper

Create `src/lib/api.js`:

```javascript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export async function apiRequest(endpoint, options = {}) {
  const { method = 'GET', body, auth } = options;
  
  const headers = {
    'Content-Type': 'application/json',
  };
  
  if (auth) {
    const idToken = await auth.getIdToken();
    headers['Authorization'] = `Bearer ${idToken}`;
  }
  
  const response = await fetch(`${API_URL}${endpoint}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'API request failed');
  }
  
  return response.json();
}

// Quiz Generation
export async function generateQuiz(topic, numberOfQuestions, difficulty, auth) {
  return apiRequest('/api/generate-quiz', {
    method: 'POST',
    body: { topic, numberOfQuestions, difficulty },
    auth,
  });
}

// PDF Processing
export async function processPdfChunks(file, numberOfQuestions) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('numberOfQuestions', numberOfQuestions.toString());
  
  const response = await fetch(`${API_URL}/api/process-pdf-chunks`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to process PDF');
  }
  
  return response.json();
}

// Quiz from Chunks
export async function generateQuizFromChunks(chunks, numberOfQuestions, quizName, auth) {
  return apiRequest('/api/generate-quiz-from-pdf-chunks', {
    method: 'POST',
    body: { chunks, numberOfQuestions, quizName },
    auth,
  });
}

// Quiz History
export async function getQuizHistory(auth) {
  return apiRequest('/api/quiz-history', { auth });
}

export async function saveQuizHistory(quizData, auth) {
  return apiRequest('/api/quiz-history', {
    method: 'POST',
    body: quizData,
    auth,
  });
}

export async function getQuizHistoryById(id, auth) {
  return apiRequest(`/api/quiz-history/${id}`, { auth });
}
```

## 6. Update Socket.IO Connection

Update socket connection to Flask backend:

```javascript
import { io } from 'socket.io-client';

const SOCKET_URL = process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'http://localhost:5000';

export const socket = io(SOCKET_URL, {
  autoConnect: false,
  transports: ['websocket', 'polling'],
});

// Connect when needed
export function connectSocket() {
  if (!socket.connected) {
    socket.connect();
  }
}

// Disconnect when done
export function disconnectSocket() {
  if (socket.connected) {
    socket.disconnect();
  }
}
```

## 7. Update Layout to Use Auth Provider

Update `src/app/layout.js`:

```javascript
import { AuthProvider } from '@/context/AuthContext';

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
```

## 8. Replace NextAuth Components

Update your Google Auth Button:

```javascript
'use client';

import { useAuth } from '@/context/AuthContext';

export default function GoogleAuthButton() {
  const { user, loading, signIn, logOut } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (user) {
    return (
      <div className="flex items-center gap-4">
        <img src={user.image} alt={user.name} className="w-8 h-8 rounded-full" />
        <span>{user.name}</span>
        <button onClick={logOut}>Sign Out</button>
      </div>
    );
  }

  return (
    <button onClick={signIn}>
      Sign in with Google
    </button>
  );
}
```

## 9. Usage Examples

### Making Authenticated API Calls

```javascript
import { useAuth } from '@/context/AuthContext';
import { getQuizHistory, saveQuizHistory } from '@/lib/api';

function QuizHistoryPage() {
  const { user } = useAuth();
  const [history, setHistory] = useState([]);

  useEffect(() => {
    if (user) {
      loadHistory();
    }
  }, [user]);

  async function loadHistory() {
    try {
      const data = await getQuizHistory(user);
      setHistory(data.history);
    } catch (error) {
      console.error('Failed to load history:', error);
    }
  }

  async function saveResult(quizData) {
    try {
      await saveQuizHistory(quizData, user);
      loadHistory();
    } catch (error) {
      console.error('Failed to save:', error);
    }
  }

  // ... render
}
```

## 10. Firebase Console Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project
3. Enable Authentication → Google Sign-In
4. Add your domains to Authorized domains
5. Get your web app config from Project Settings
6. Generate Service Account key for Flask backend
