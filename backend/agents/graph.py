"""
LangGraph Travel Concierge Agent
Uses Gemini as the LLM with Groq as fallback.
Graph: user_input → router → [flight_node | weather_node | itinerary_node | currency_node | general_node] → respond
"""
from __future__ import annotations
import os, json
from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
import operator
from config import GEMINI_API_KEY, GROQ_API_KEY

from tools.api_tools import (
    search_flights, get_weather, get_current_weather,
    convert_currency, get_exchange_rates,
    geocode_city, search_places, get_airport_info
)

# ─── LLM Setup ───────────────────────────────────────────────────────────────

# def get_llm(streaming: bool = False):
#     try:
#         print("GEMINI_API_KEY loaded:", bool(GEMINI_API_KEY))
#         print("GEMINI_API_KEY first chars:",
#               GEMINI_API_KEY[:10] if GEMINI_API_KEY else "None")

#         return ChatGoogleGenerativeAI(
#             model="gemini-2.0-flash",
#             google_api_key=GEMINI_API_KEY,
#             temperature=0.7,
#             streaming=streaming,
#         )
#     except Exception:
#         return ChatGroq(
#             model="llama3-8b-8192",
#             api_key=GROQ_API_KEY,
#             temperature=0.7,
#             streaming=streaming,
#         )
def get_llm(streaming: bool = False):
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=GROQ_API_KEY,
        temperature=0.7,
        streaming=streaming,
    )
# ─── Agent State ─────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages:       Annotated[List[BaseMessage], add_messages]
    intent:         str           # flights | weather | itinerary | currency | general
    trip_context:   dict          # destination, dates, passengers etc
    api_data:       dict          # raw results from tool calls
    final_response: str           # formatted response to stream back


SYSTEM_PROMPT = """You are an expert AI Travel Concierge. You help users:
- Search and compare flights (use IATA codes like DEL, BOM, LHR, DXB)
- Get weather forecasts for travel destinations
- Plan detailed itineraries day by day
- Convert currencies for travel budgeting
- Recommend places to visit, eat, and stay

Always be helpful, specific, and proactive. When you have flight or weather data, 
present it in a clear, structured way. For itineraries, create day-by-day plans 
with morning/afternoon/evening activities.

When users ask about flights, always clarify: departure city, destination, and date.
Format responses in clean markdown with headers and bullet points."""


# ─── Router Node ─────────────────────────────────────────────────────────────

async def router_node(state: AgentState) -> AgentState:
    """Classify the user's intent from their last message."""
    last_msg = state["messages"][-1].content if state["messages"] else ""
    
    llm = get_llm()
    classification_prompt = f"""Classify this travel query into exactly ONE category.
Reply with only the category word, nothing else.

Categories:
- flights     (searching flights, airlines, airports)
- weather     (weather, forecast, climate, temperature)
- itinerary   (plan trip, things to do, places to visit, day plan, POI)
- currency    (currency, exchange rate, convert money, how much is X in Y)
- general     (anything else: visa, packing, hotels, general advice)

Query: "{last_msg}"

Category:"""

    try:
        response = await llm.ainvoke([HumanMessage(content=classification_prompt)])
        intent = response.content.strip().lower()
        if intent not in ["flights", "weather", "itinerary", "currency", "general"]:
            intent = "general"
    except Exception:
        intent = "general"

    return {**state, "intent": intent}


# ─── Flight Node ──────────────────────────────────────────────────────────────

async def flight_node(state: AgentState) -> AgentState:
    last_msg = state["messages"][-1].content
    llm = get_llm()

    # Extract flight params from message
    extract_prompt = f"""Extract flight search parameters from this message.
Return ONLY valid JSON with keys: dep_iata, arr_iata, flight_date (YYYY-MM-DD or null).
Use standard IATA codes. If city names given, convert (e.g. Delhi→DEL, Mumbai→BOM, London→LHR, Dubai→DXB, Paris→CDG).
If date not mentioned, return null for flight_date.

Message: "{last_msg}"
JSON:"""

    try:
        resp = await llm.ainvoke([HumanMessage(content=extract_prompt)])
        params = json.loads(resp.content.strip().replace("```json","").replace("```",""))
        dep  = params.get("dep_iata", "DEL")
        arr  = params.get("arr_iata", "DXB")
        date = params.get("flight_date")
        
        flight_data = await search_flights(dep, arr, date)
        state["api_data"] = flight_data

        # Format with LLM
        format_prompt = f"""The user asked: "{last_msg}"

Here is the flight data from AviationStack API:
{json.dumps(flight_data, indent=2)}

Present this data as a helpful travel assistant. Include:
- Flight numbers, airlines, status
- Departure/arrival times and airports
- Any tips about the route
If no flights found, explain and suggest alternatives.
Use markdown formatting."""

        final = await llm.ainvoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=format_prompt)])
        return {**state, "api_data": flight_data, "final_response": final.content}
    except Exception as e:
        return {**state, "final_response": f"I had trouble fetching flight data: {e}. Please try with IATA codes like DEL→DXB."}


# ─── Weather Node ─────────────────────────────────────────────────────────────

async def weather_node(state: AgentState) -> AgentState:
    last_msg = state["messages"][-1].content
    llm = get_llm()

    # Extract city
    extract_prompt = f"""Extract the city name from this weather query. Return ONLY the city name.
Message: "{last_msg}"
City:"""
    try:
        resp = await llm.ainvoke([HumanMessage(content=extract_prompt)])
        city = resp.content.strip().strip('"').strip("'")
        
        weather_data = await get_weather(city, days=5)
        state["api_data"] = weather_data

        format_prompt = f"""User asked: "{last_msg}"

Weather data for {city}:
{json.dumps(weather_data, indent=2)}

Present this as a helpful travel weather briefing. Include:
- Current conditions summary
- Day by day forecast with emojis for weather icons (☀️🌧️⛅🌩️❄️)
- Travel tips based on the weather (what to pack, best times to go out)
Use markdown."""

        final = await llm.ainvoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=format_prompt)])
        return {**state, "api_data": weather_data, "final_response": final.content}
    except Exception as e:
        return {**state, "final_response": f"Could not fetch weather: {e}"}


# ─── Itinerary Node ───────────────────────────────────────────────────────────

async def itinerary_node(state: AgentState) -> AgentState:
    last_msg = state["messages"][-1].content
    llm = get_llm()

    # Geocode city and fetch POIs
    extract_prompt = f"""Extract the destination city and number of days from this message.
Return ONLY JSON: {{"city": "...", "days": N}}
Message: "{last_msg}"
JSON:"""
    try:
        resp = await llm.ainvoke([HumanMessage(content=extract_prompt)])
        params = json.loads(resp.content.strip().replace("```json","").replace("```",""))
        city = params.get("city", "Paris")
        days = params.get("days", 3)

        # Fetch weather and places in parallel context
        weather_data = await get_weather(city, days=days)
        places_data  = await search_places(city, "tourism")
        geo_data     = await geocode_city(city)

        combined_data = {
            "city": city,
            "days": days,
            "weather": weather_data,
            "places": places_data,
            "location": geo_data,
        }
        state["api_data"] = combined_data

        format_prompt = f"""User asked: "{last_msg}"

Real data available:
- Weather: {json.dumps(weather_data.get("forecasts", [])[:days], indent=2)}
- Places of interest: {json.dumps(places_data.get("places", [])[:6], indent=2)}
- Location: {json.dumps(geo_data, indent=2)}

Create a detailed {days}-day itinerary for {city}. For each day include:
- Morning activity with specific place names from the data
- Afternoon activity  
- Evening recommendation (dinner area / nightlife)
- Weather tip based on forecast

Also include:
- Best time to visit and current weather summary
- 3-5 must-try local foods
- Transportation tips
- Budget estimate per day in INR

Format nicely with markdown headers and emojis."""

        final = await llm.ainvoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=format_prompt)])
        return {**state, "api_data": combined_data, "final_response": final.content}
    except Exception as e:
        return {**state, "final_response": f"Could not generate itinerary: {e}"}


# ─── Currency Node ────────────────────────────────────────────────────────────

async def currency_node(state: AgentState) -> AgentState:
    last_msg = state["messages"][-1].content
    llm = get_llm()

    extract_prompt = f"""Extract currency conversion details.
Return ONLY JSON: {{"amount": N, "from": "XXX", "to": "YYY"}}
Use ISO 4217 codes (INR, USD, EUR, GBP, etc.)
If just asking about rates without amount, use amount: 1.
Message: "{last_msg}"
JSON:"""
    try:
        resp = await llm.ainvoke([HumanMessage(content=extract_prompt)])
        params = json.loads(resp.content.strip().replace("```json","").replace("```",""))
        
        result = await convert_currency(
            amount=params.get("amount", 1),
            from_currency=params.get("from", "INR"),
            to_currency=params.get("to", "USD")
        )
        # Also get broader rates
        rates = await get_exchange_rates(params.get("from", "INR"))
        
        combined = {"conversion": result, "rates": rates}
        state["api_data"] = combined

        format_prompt = f"""User asked: "{last_msg}"

Currency data:
{json.dumps(combined, indent=2)}

Present this as a travel budget helper. Include:
- The specific conversion requested
- A comparison table of other useful travel currencies
- Tips for getting best exchange rates while travelling
Use markdown."""

        final = await llm.ainvoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=format_prompt)])
        return {**state, "api_data": combined, "final_response": final.content}
    except Exception as e:
        return {**state, "final_response": f"Currency conversion error: {e}"}


# ─── General Node ─────────────────────────────────────────────────────────────

async def general_node(state: AgentState) -> AgentState:
    messages = state["messages"]
    llm = get_llm()
    try:
        full_messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
        final = await llm.ainvoke(full_messages)
        return {**state, "final_response": final.content}
    except Exception as e:
        return {**state, "final_response": f"I encountered an issue: {e}. Please try again."}


# ─── Routing Logic ────────────────────────────────────────────────────────────

def route_by_intent(state: AgentState) -> str:
    intent = state.get("intent", "general")
    routing = {
        "flights":   "flight_node",
        "weather":   "weather_node",
        "itinerary": "itinerary_node",
        "currency":  "currency_node",
        "general":   "general_node",
    }
    return routing.get(intent, "general_node")


# ─── Build Graph ──────────────────────────────────────────────────────────────

def build_graph():
    builder = StateGraph(AgentState)
    
    builder.add_node("router",         router_node)
    builder.add_node("flight_node",    flight_node)
    builder.add_node("weather_node",   weather_node)
    builder.add_node("itinerary_node", itinerary_node)
    builder.add_node("currency_node",  currency_node)
    builder.add_node("general_node",   general_node)

    builder.set_entry_point("router")
    
    builder.add_conditional_edges("router", route_by_intent, {
        "flight_node":    "flight_node",
        "weather_node":   "weather_node",
        "itinerary_node": "itinerary_node",
        "currency_node":  "currency_node",
        "general_node":   "general_node",
    })

    for node in ["flight_node", "weather_node", "itinerary_node", "currency_node", "general_node"]:
        builder.add_edge(node, END)

    return builder.compile()

graph = build_graph()
