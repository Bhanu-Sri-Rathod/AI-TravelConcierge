import httpx
from config import AVIATIONSTACK_API_KEY, OPENWEATHER_API_KEY, EXCHANGE_API_KEY
from typing import Optional

# ─── AviationStack – Flights ────────────────────────────────────────────────

async def search_flights(
    dep_iata: str,
    arr_iata: str,
    flight_date: Optional[str] = None
) -> dict:
    """Search flights between two airports using AviationStack."""
    params = {
        "access_key": AVIATIONSTACK_API_KEY,
        "dep_iata": dep_iata.upper(),
        "arr_iata": arr_iata.upper(),
        "limit": 10,
    }
    if flight_date:
        params["flight_date"] = flight_date  # YYYY-MM-DD

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            r = await client.get("http://api.aviationstack.com/v1/flights", params=params)
            data = r.json()
            flights = data.get("data", [])
            if not flights:
                return {"flights": [], "message": f"No flights found from {dep_iata} to {arr_iata}"}
            results = []
            for f in flights[:8]:
                dep = f.get("departure", {})
                arr = f.get("arrival", {})
                airline = f.get("airline", {})
                results.append({
                    "flight_number": f.get("flight", {}).get("iata", "N/A"),
                    "airline": airline.get("name", "Unknown"),
                    "status": f.get("flight_status", "scheduled"),
                    "departure": {
                        "airport": dep.get("airport", dep_iata),
                        "iata": dep.get("iata", dep_iata),
                        "scheduled": dep.get("scheduled", "N/A"),
                        "terminal": dep.get("terminal", "N/A"),
                        "gate": dep.get("gate", "N/A"),
                    },
                    "arrival": {
                        "airport": arr.get("airport", arr_iata),
                        "iata": arr.get("iata", arr_iata),
                        "scheduled": arr.get("scheduled", "N/A"),
                        "terminal": arr.get("terminal", "N/A"),
                    }
                })
            return {"flights": results, "count": len(results)}
        except Exception as e:
            return {"error": str(e), "flights": []}


async def get_airport_info(iata_code: str) -> dict:
    """Get airport details by IATA code."""
    params = {"access_key": AVIATIONSTACK_API_KEY, "iata_code": iata_code.upper()}
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get("http://api.aviationstack.com/v1/airports", params=params)
            data = r.json().get("data", [])
            if data:
                a = data[0]
                return {
                    "name": a.get("airport_name"),
                    "iata": a.get("iata_code"),
                    "city": a.get("city_iata_code"),
                    "country": a.get("country_name"),
                    "latitude": a.get("latitude"),
                    "longitude": a.get("longitude"),
                }
            return {"error": f"Airport {iata_code} not found"}
        except Exception as e:
            return {"error": str(e)}


# ─── OpenWeatherMap ──────────────────────────────────────────────────────────

async def get_weather(city: str, days: int = 5):
    print("OPENWEATHER_API_KEY loaded:", bool(OPENWEATHER_API_KEY))
    print("OPENWEATHER_API_KEY:", OPENWEATHER_API_KEY[:8] if OPENWEATHER_API_KEY else "None")

    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "cnt": min(days * 8, 40),
    }
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get("https://api.openweathermap.org/data/2.5/forecast", params=params)
            data = r.json()
            print("Weather API Response:", data)
            if data.get("cod") != "200":
                return {"error": data.get("message", "City not found"), "city": city}

            city_info = data.get("city", {})
            forecasts = []
            seen_dates = set()
            for item in data.get("list", []):
                date = item["dt_txt"].split(" ")[0]
                if date not in seen_dates:
                    seen_dates.add(date)
                    weather = item["weather"][0]
                    main = item["main"]
                    forecasts.append({
                        "date": date,
                        "description": weather["description"].capitalize(),
                        "icon": weather["icon"],
                        "temp_min": round(main["temp_min"]),
                        "temp_max": round(main["temp_max"]),
                        "humidity": main["humidity"],
                        "feels_like": round(main["feels_like"]),
                        "wind_speed": item.get("wind", {}).get("speed", 0),
                    })
            return {
                "city": city_info.get("name", city),
                "country": city_info.get("country", ""),
                "latitude": city_info.get("coord", {}).get("lat"),
                "longitude": city_info.get("coord", {}).get("lon"),
                "forecasts": forecasts[:days]
            }
        except Exception as e:
            return {"error": str(e), "city": city}


async def get_current_weather(city: str) -> dict:
    """Get current weather for a city."""
    params = {"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"}
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get("https://api.openweathermap.org/data/2.5/weather", params=params)
            d = r.json()
            if d.get("cod") != 200:
                return {"error": d.get("message", "Not found")}
            return {
                "city": d["name"],
                "country": d["sys"]["country"],
                "temp": round(d["main"]["temp"]),
                "feels_like": round(d["main"]["feels_like"]),
                "description": d["weather"][0]["description"].capitalize(),
                "humidity": d["main"]["humidity"],
                "wind_speed": d["wind"]["speed"],
                "latitude": d["coord"]["lat"],
                "longitude": d["coord"]["lon"],
            }
        except Exception as e:
            return {"error": str(e)}


# ─── Exchange Rates ──────────────────────────────────────────────────────────

async def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert currency using live exchange rates."""
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/pair/{from_currency.upper()}/{to_currency.upper()}/{amount}"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(url)
            d = r.json()
            if d.get("result") == "success":
                return {
                    "from": from_currency.upper(),
                    "to": to_currency.upper(),
                    "amount": amount,
                    "converted": round(d["conversion_result"], 2),
                    "rate": d["conversion_rate"],
                }
            return {"error": d.get("error-type", "Conversion failed")}
        except Exception as e:
            return {"error": str(e)}


async def get_exchange_rates(base: str = "USD") -> dict:
    """Get all exchange rates for a base currency."""
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/latest/{base.upper()}"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(url)
            d = r.json()
            if d.get("result") == "success":
                rates = d.get("conversion_rates", {})
                # Return only the most useful currencies
                useful = ["USD","EUR","GBP","INR","JPY","AUD","CAD","CHF","SGD","AED","THB","MYR"]
                return {
                    "base": base.upper(),
                    "rates": {k: v for k, v in rates.items() if k in useful},
                    "last_updated": d.get("time_last_update_utc", "")
                }
            return {"error": "Failed to fetch rates"}
        except Exception as e:
            return {"error": str(e)}


# ─── OpenStreetMap Nominatim – Geocoding (free, no key needed) ──────────────

async def geocode_city(city: str) -> dict:
    """Geocode a city name to lat/lon using OSM Nominatim."""
    params = {"q": city, "format": "json", "limit": 1}
    headers = {"User-Agent": "TravelConcierge/1.0"}
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get("https://nominatim.openstreetmap.org/search", params=params, headers=headers)
            results = r.json()
            if results:
                loc = results[0]
                return {
                    "name": loc.get("display_name", city),
                    "latitude": float(loc["lat"]),
                    "longitude": float(loc["lon"]),
                    "type": loc.get("type", ""),
                }
            return {"error": f"Location '{city}' not found"}
        except Exception as e:
            return {"error": str(e)}


async def search_places(city: str, category: str = "tourism") -> dict:
    """Search for places of interest in a city using Nominatim."""
    query = f"{category} in {city}"
    params = {"q": query, "format": "json", "limit": 8, "addressdetails": 1}
    headers = {"User-Agent": "TravelConcierge/1.0"}
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get("https://nominatim.openstreetmap.org/search", params=params, headers=headers)
            results = r.json()
            places = []
            for p in results:
                places.append({
                    "name": p.get("display_name", "").split(",")[0],
                    "full_address": p.get("display_name", ""),
                    "latitude": float(p["lat"]),
                    "longitude": float(p["lon"]),
                    "type": p.get("type", ""),
                })
            return {"places": places, "city": city, "category": category}
        except Exception as e:
            return {"error": str(e), "places": []}
