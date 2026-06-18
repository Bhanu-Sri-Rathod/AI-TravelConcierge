# AI Travel Concierge 🌍

A full-stack AI travel assistant powered by **Groq, LangGraph, FastAPI, and Next.js**. The application combines AI-driven reasoning with real-time travel data to help users plan trips, explore destinations, check weather conditions, search flights, convert currencies, and generate personalized travel itineraries through natural language conversations.

---

## ✨ Features

### 🤖 AI-Powered Travel Assistant

* LangGraph-based multi-agent workflow for intelligent travel planning
* Groq LLaMA models for fast and accurate responses
* Gemini integration as a fallback LLM
* Context-aware travel recommendations and assistance

### ✈️ Travel Services

* Flight search using AviationStack API
* Personalized day-by-day itinerary generation
* Destination recommendations and travel guidance
* Best-time-to-visit suggestions

### 🌦️ Real-Time Travel Data

* 5-day weather forecasts using OpenWeatherMap
* Currency conversion using ExchangeRate API
* Location and point-of-interest data from OpenStreetMap
* Interactive map visualization with Leaflet

### 🎙️ Enhanced User Experience

* Voice-enabled travel queries using Web Speech API
* Real-time streaming responses via Server-Sent Events (SSE)
* Interactive map integration
* Responsive and user-friendly interface

### 🔒 Authentication & Storage

* JWT-based user authentication
* Secure login and registration
* Trip history management
* SQLite database integration

---

## 🏗️ Architecture

```text
┌─────────────────┐
│      User       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Next.js Frontend│
│  (React + TS)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ FastAPI Backend │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  LangGraph Orchestrator │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│   Groq LLaMA (Primary)  │
│   Gemini (Fallback)     │
└────────┬────────────────┘
         │
 ┌───────┼────────┬──────────┬──────────┐
 │       │        │          │          │
 ▼       ▼        ▼          ▼          ▼

✈️ Flight  🌦️ Weather  🗺️ Itinerary  💱 Currency

 │          │          │          │
 ▼          ▼          ▼          ▼

Aviation   OpenWeather  OpenStreetMap  ExchangeRate
Stack API     API           API           API

```
---

## 🛠️ Tech Stack

### Frontend

* Next.js
* React
* TypeScript
* Tailwind CSS
* Leaflet
* OpenStreetMap
* Web Speech API

### Backend

* FastAPI
* Python
* LangGraph
* LangChain
* SQLAlchemy
* SQLite
* JWT Authentication

### AI & APIs

* Groq (LLaMA Models)
* Google Gemini
* AviationStack API
* OpenWeatherMap API
* ExchangeRate API
* OpenStreetMap API

---

## 📌 Example Queries

* "Find flights from Delhi to Dubai"
* "What's the weather in Paris this week?"
* "Plan a 5-day trip to Singapore"
* "Convert 10,000 INR to USD"
* "Best places to visit in Bali"
* "Best time to visit Switzerland"

---

## 📂 Project Structure

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

## 🚀 Key Highlights

* Multi-agent AI architecture using LangGraph
* Full-stack implementation with FastAPI and Next.js
* Real-time travel data integration through multiple APIs
* Voice-enabled travel assistant experience
* Interactive maps and itinerary planning
* Secure authentication and trip management
* Scalable and modular architecture for future enhancements
