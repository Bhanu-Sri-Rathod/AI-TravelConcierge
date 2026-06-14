# AI Travel Concierge 🌍

A full-stack AI travel assistant powered by **Groq + LangGraph + FastAPI + Next.js**.

## Features
- **Flight search** via AviationStack API
- **Weather forecasts** (5-day) via OpenWeatherMap
- **Day-by-day itinerary generation** with real POI data from OpenStreetMap
- **Currency conversion** via ExchangeRate API
- **Interactive map** via Leaflet + OpenStreetMap (zero cost, no key needed)
- **Voice input** via Web Speech API
- **Streaming responses** via Server-Sent Events
- **User auth** with JWT
- **Trip saving** to SQLite database
- **LangSmith tracing** for all agent runs

## Architecture

```
User → Next.js (React) → FastAPI (Python)
                              ↓
                       LangGraph Agent
                       ┌─────┴──────┐
                    Router (GROQ)
                    ↙  ↙  ↙  ↙  ↙
            Flights Weather Itinerary Currency General
               ↓      ↓       ↓        ↓       ↓
          AviationStack OpenWeather OSM ExchangeRate Gemini
```

## Setup (Local)

### 1. Clone & configure
```bash
git clone <your-repo>
cd travel-concierge
# All API keys are already in .env
```

### 2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
# → Running on http://localhost:8000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
# → Running on http://localhost:3000
```

### 4. Open browser
Go to `http://localhost:3000`, register an account, start chatting!

## API Keys Used
| API | Purpose | Key location |
|-----|---------|-------------|
| Groq | LLM reasoning | `.env` GROQ_API_KEY |
| Gemini | Fallback LLM | `.env` GEMINI_API_KEY |
| AviationStack | Flight data | `.env` AVIATIONSTACK_API_KEY |
| OpenWeatherMap | Weather forecast | `.env` OPENWEATHER_API_KEY |
| ExchangeRate | Currency conversion | `.env` EXCHANGE_API_KEY |
| OpenStreetMap | Maps + geocoding | No key needed |
| LangSmith | Agent tracing | `.env` LANGCHAIN_API_KEY |

## Example queries
- "Find flights from DEL to DXB"
- "What's the weather in Paris next week?"
- "Plan a 4-day trip to Singapore"
- "Convert 5000 INR to EUR"
- "Best time to visit Maldives"
- "Visa requirements for Indian passport to Japan"

## Project Structure
```
travel-concierge/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Environment config
│   ├── agents/
│   │   └── graph.py         # LangGraph agent
│   ├── tools/
│   │   └── api_tools.py     # All API integrations
│   ├── routers/
│   │   ├── auth.py          # JWT authentication
│   │   └── chat.py          # Chat + trips endpoints
│   └── db/
│       └── models.py        # SQLAlchemy models
└── frontend/
    ├── app/
    │   ├── page.tsx          # Main chat UI
    │   └── globals.css
    ├── components/
    │   └── MapView.tsx       # Leaflet map
    └── lib/
        └── api.ts            # API client
```

## Deployment
- **Backend**: Deploy to Railway (`railway up` in backend folder)
- **Frontend**: Deploy to Vercel (`vercel` in frontend folder)
- Set `NEXT_PUBLIC_API_URL` to your Railway backend URL in Vercel env vars

## LangSmith Monitoring
Visit https://smith.langchain.com → Project: `travel-concierge` to see all agent traces.
