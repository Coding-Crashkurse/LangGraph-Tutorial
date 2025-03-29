import random
import requests
from mcp.server.fastmcp import FastMCP

# Erstelle Server
mcp = FastMCP("Echo Server")


import requests
import random
import uuid
from datetime import datetime, timedelta


@mcp.tool(name="basic_calculator", description="Performs basic arithmetic.")
def basic_calculator(operation: str, a: float, b: float) -> float:
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero.")
        return a / b
    else:
        raise ValueError(f"Unknown operation: {operation}")


@mcp.tool(name="weather_lookup", description="Fetch the current weather for a city.")
def weather_lookup(city: str) -> str:
    url = f"https://wttr.in/{city}?format=3"
    response = requests.get(url)
    return response.text


@mcp.tool(name="uuid_generator", description="Generates a random UUID.")
def uuid_generator() -> str:
    return str(uuid.uuid4())


@mcp.tool(name="random_joke", description="Returns a random joke from an example API.")
def random_joke() -> str:
    url = "https://official-joke-api.appspot.com/random_joke"
    r = requests.get(url)
    data = r.json()
    return f"{data['setup']} - {data['punchline']}"


@mcp.tool(
    name="wikipedia_summary",
    description="Look up a term on Wikipedia and return a short summary.",
)
def wikipedia_summary(topic: str) -> str:
    api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic}"
    r = requests.get(api_url)
    if r.status_code == 200:
        data = r.json()
        return data.get("extract", "No summary found.")
    else:
        return "Wikipedia page not found."


@mcp.tool(
    name="language_translator",
    description="Translates text from one language to another (mocked).",
)
def language_translator(text: str, source_lang: str, target_lang: str) -> str:
    return f"[{source_lang} -> {target_lang}] {text}"


@mcp.tool(name="sentiment_analysis", description="Analyzes sentiment of text (mocked).")
def sentiment_analysis(text: str) -> str:
    if "love" in text.lower():
        return "Positive"
    elif "hate" in text.lower():
        return "Negative"
    else:
        return "Neutral"


@mcp.tool(
    name="date_calculator", description="Adds or subtracts days from a given date."
)
def date_calculator(start_date: str, days: int) -> str:
    dt = datetime.strptime(start_date, "%Y-%m-%d")
    new_date = dt + timedelta(days=days)
    return new_date.strftime("%Y-%m-%d")


@mcp.tool(
    name="password_generator",
    description="Generates a random alphanumeric password of given length.",
)
def password_generator(length: int) -> str:
    import string
    import secrets

    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


@mcp.tool(
    name="stock_price_lookup",
    description="Retrieves the (mock) price of a given stock symbol.",
)
def stock_price_lookup(symbol: str) -> float:
    return round(random.uniform(10, 500), 2)


@mcp.tool(
    name="crypto_price_lookup",
    description="Retrieves the (mock) price of a given cryptocurrency.",
)
def crypto_price_lookup(symbol: str) -> float:
    return round(random.uniform(1000, 45000), 2)


@mcp.tool(
    name="currency_converter",
    description="Convert an amount between two currencies (mock).",
)
def currency_converter(amount: float, from_currency: str, to_currency: str) -> float:
    random_rate = random.uniform(0.5, 1.5)
    return round(amount * random_rate, 2)


@mcp.tool(
    name="extract_named_entities",
    description="Extracts named entities from text (mock).",
)
def extract_named_entities(text: str) -> list[str]:
    words = text.split()
    return [w for w in words if w.istitle()]


@mcp.tool(
    name="recommend_movies",
    description="Given a genre, return a few (mock) recommended movie titles.",
)
def recommend_movies(genre: str) -> list[str]:
    sample_movies = {
        "action": ["Fast & Furious 9", "Mad Max: Fury Road", "John Wick"],
        "comedy": ["Anchorman", "Step Brothers", "Superbad"],
        "sci-fi": ["Inception", "Interstellar", "The Matrix"],
        "romance": ["The Notebook", "Pride & Prejudice", "Notting Hill"],
        "horror": ["The Conjuring", "Get Out", "It Follows"],
    }
    genre_lower = genre.lower()
    if genre_lower in sample_movies:
        return random.sample(
            sample_movies[genre_lower], k=min(3, len(sample_movies[genre_lower]))
        )
    else:
        return ["No recommendations found for this genre. Try 'action', 'comedy', etc."]


if __name__ == "__main__":
    mcp.run(transport="sse")
