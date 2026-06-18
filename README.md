# 🌍 AI Travel Concierge

A full-stack AI-powered travel assistant built with **Groq, LangGraph, FastAPI, and Next.js**. The application helps users search flights, check weather forecasts, convert currencies, generate personalized itineraries, and explore destinations through an interactive map.

---

## ✨ Features

### ✈️ Travel & Planning
- Flight search using AviationStack API
- 5-day weather forecasts via OpenWeatherMap
- AI-generated day-by-day travel itineraries
- Real Points of Interest (POI) data from OpenStreetMap
- Currency conversion using ExchangeRate API
- Destination recommendations and travel guidance

### 🗺️ Interactive Experience
- Interactive maps powered by Leaflet and OpenStreetMap
- No map API key required
- Location visualization for attractions and destinations

### 🤖 AI-Powered Assistant
- Intelligent query routing using LangGraph
- Fast reasoning with Groq LLM
- Gemini fallback for enhanced reliability
- Streaming responses via Server-Sent Events (SSE)
- Voice input support using the Web Speech API

### 🔐 User Management
- JWT-based authentication
- User registration and login
- Save and manage trips
- SQLite database integration

---

## 🏗️ Architecture

```text
User
  │
  ▼
Next.js Frontend (React)
  │
  ▼
FastAPI Backend
  │
  ▼
LangGraph Agent
  │
  ├── Flight Agent      → AviationStack API
  ├── Weather Agent     → OpenWeatherMap API
  ├── Itinerary Agent   → OpenStreetMap API
  ├── Currency Agent    → ExchangeRate API
  └── General Agent     → Groq / Gemini
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd travel-concierge
```

### 2. Configure Environment Variables

Create a `.env` file in the backend directory and add:

```env
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
AVIATIONSTACK_API_KEY=your_aviationstack_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
EXCHANGE_API_KEY=your_exchange_api_key
SECRET_KEY=your_secret_key
```

---

### 3. Backend Setup

```bash
cd backend

python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt

python main.py
```

Backend runs at:

```text
http://localhost:8000
```

---

### 4. Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

Frontend runs at:

```text
http://localhost:3000
```

---

### 5. Launch the Application

Open your browser and visit:

```text
http://localhost:3000
```

Create an account, log in, and start planning your next trip.

---

## 🔑 API Integrations

| Service | Purpose |
|----------|----------|
| Groq | Primary LLM reasoning |
| Gemini | Fallback LLM |
| AviationStack | Flight information |
| OpenWeatherMap | Weather forecasts |
| ExchangeRate API | Currency conversion |
| OpenStreetMap | Maps, geocoding, and POI data |

---

## 💬 Example Queries

- "Find flights from DEL to DXB"
- "What's the weather in Paris next week?"
- "Plan a 4-day trip to Singapore"
- "Convert 5000 INR to EUR"
- "Best time to visit Maldives"
- "Visa requirements for Indian passport holders visiting Japan"

---

## 📁 Project Structure

```text
travel-concierge/
│
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── agents/
│   │   └── graph.py
│   ├── tools/
│   │   └── api_tools.py
│   ├── routers/
│   │   ├── auth.py
│   │   └── chat.py
│   └── db/
│       └── models.py
│
└── frontend/
    ├── app/
    │   ├── page.tsx
    │   └── globals.css
    ├── components/
    │   └── MapView.tsx
    └── lib/
        └── api.ts
```

---

## 🛠️ Tech Stack

### Frontend
- Next.js
- React
- TypeScript
- Tailwind CSS
- Leaflet
- OpenStreetMap

### Backend
- FastAPI
- Python
- SQLAlchemy
- SQLite
- JWT Authentication

### AI & Agent Framework
- Groq
- Gemini
- LangGraph
- LangChain

---

## 💡 Why AI Travel Concierge?

Planning a trip often requires switching between multiple platforms for flights, weather forecasts, maps, currency conversion, and itinerary planning. AI Travel Concierge brings all these services together into a single intelligent assistant that provides personalized travel recommendations and real-time information through a conversational interface.

---

## 🎯 Future Enhancements

- Hotel and accommodation recommendations
- Multi-city trip planning
- Budget optimization suggestions
- Personalized travel preferences
- Real-time flight tracking
- Travel expense management

---

## 🌍 Travel Smarter with AI

AI Travel Concierge combines modern AI agents, real-time travel data, and interactive mapping to deliver a seamless travel planning experience—all from a single chat interface.
