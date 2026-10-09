import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY) if API_KEY else None

MODEL_NAME = "gemini-3.8-flash"


def generate_ai(prompt: str) -> str:
    if not client:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        if response and response.text:
            return response.text

        return "AI temporarily unavailable."

    except Exception as e:
        print(f"GEMINI ERROR: {e}")
        return "AI temporarily unavailable."


def home_recommendation(budget, room, style):
    prompt = f"""
You are a smart home interior recommendation assistant.

User budget: {budget}
Room: {room}
Preferred style: {style}

Suggest 5 practical home interior items within the user's budget.

For each item, provide:
- Item name
- Category
- Estimated price in INR

Keep the total estimated cost within the user's budget.

Give simple and useful recommendations.
"""
    return generate_ai(prompt)


def party_recommendation(budget, event_type, guests, theme):
    prompt = f"""
You are a smart party planning recommendation assistant.

User budget: {budget}
Event type: {event_type}
Number of guests: {guests}
Theme: {theme}

Suggest 5 practical party planning items within the user's budget.

For each item, provide:
- Item name
- Category
- Estimated price in INR

Keep the total estimated cost within the user's budget.

Give simple and useful recommendations.
"""
    return generate_ai(prompt)


def jewelry_recommendation(budget, jewelry_type, occasion, style):
    prompt = f"""
You are a smart jewelry recommendation assistant.

User budget: {budget}
Jewelry type: {jewelry_type}
Occasion: {occasion}
Style: {style}

Suggest 5 practical jewelry recommendations within the user's budget.

For each recommendation, provide:
- Item name
- Jewelry category
- Estimated price in INR

Keep the total estimated cost within the user's budget.

Give simple and useful recommendations.
"""
    return generate_ai(prompt)