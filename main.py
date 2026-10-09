import json
import sqlite3

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import create_database, DB_NAME
from models import (
    RegisterRequest,
    LoginRequest,
    HomeRequest,
    PartyRequest,
    JewelryRequest,
)
from gemini_generator import (
    home_recommendation,
    party_recommendation,
    jewelry_recommendation,
)


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

create_database()


def db():
    return sqlite3.connect(DB_NAME)


def save_recommendation(user_id, category, budget, input_details, recommendation):
    connection = db()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO recommendations
        (user_id, category, budget, input_details, recommendation)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            category,
            budget,
            input_details,
            recommendation,
        ),
    )

    connection.commit()
    connection.close()


# ---------------- FALLBACK RECOMMENDATIONS ----------------

def fallback_party(budget, event_type, guests, theme):
    try:
        budget = float(budget)
    except (TypeError, ValueError):
        budget = 10000

    if budget >= 10000:
        return """
1. LED Party Lights - Lighting - ₹1200
2. Balloon Decoration - Decoration - ₹1500
3. Party Cake - Food - ₹2200
4. Snacks & Drinks - Food - ₹2800
5. Theme Decoration - Decoration - ₹1800

Total Estimated Cost: ₹9500
Remaining Budget: ₹500
"""

    elif budget >= 5000:
        return """
1. LED Party Lights - Lighting - ₹700
2. Balloon Decoration - Decoration - ₹800
3. Party Cake - Food - ₹1300
4. Snacks & Drinks - Food - ₹1400
5. Simple Theme Decoration - Decoration - ₹600

Total Estimated Cost: ₹4800
Remaining Budget: ₹200
"""

    else:
        return f"""
1. Balloon Decoration - Decoration - ₹500
2. Small Party Cake - Food - ₹800
3. Snacks - Food - ₹700
4. LED Lights - Lighting - ₹400

Total Estimated Cost: ₹2400
Remaining Budget: ₹{max(0, budget - 2400):.0f}
"""


def fallback_jewelry(budget, jewelry_type, occasion, style):
    try:
        budget = float(budget)
    except (TypeError, ValueError):
        budget = 10000

    if budget >= 10000:
        return """
1. Gold Necklace - Necklace - ₹4500
2. Gold Earrings - Earrings - ₹1800
3. Traditional Bangles - Bangles - ₹1500
4. Simple Ring - Ring - ₹900

Total Estimated Cost: ₹8700
Remaining Budget: ₹1300
"""

    elif budget >= 5000:
        return """
1. Gold-Plated Necklace - Necklace - ₹2200
2. Earrings - Earrings - ₹900
3. Traditional Bangles - Bangles - ₹800
4. Simple Ring - Ring - ₹600

Total Estimated Cost: ₹4500
Remaining Budget: ₹500
"""

    else:
        return f"""
1. Simple Necklace - Necklace - ₹1200
2. Earrings - Earrings - ₹500
3. Bangles - Bangles - ₹400

Total Estimated Cost: ₹2100
Remaining Budget: ₹{max(0, budget - 2100):.0f}
"""


# ---------------- BASIC PAGES ----------------

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {"request": request}
    )


@app.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse(
        "forgot_password.html",
        {"request": request}
    )


# ---------------- REGISTER ----------------

@app.post("/register")
def register(request: RegisterRequest):
    connection = db()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
            """,
            (
                request.name,
                str(request.email),
                request.password,
            ),
        )

        connection.commit()

        return RedirectResponse(
            "/login",
            status_code=303
        )

    except sqlite3.IntegrityError:
        return {
            "message": "Email already registered."
        }

    finally:
        connection.close()


# ---------------- LOGIN ----------------

@app.post("/login")
def login(request: LoginRequest):
    connection = db()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, name, email
        FROM users
        WHERE email = ? AND password = ?
        """,
        (
            str(request.email),
            request.password,
        ),
    )

    user = cursor.fetchone()
    connection.close()

    if not user:
        return {
            "success": False,
            "message": "Invalid email or password."
        }

    return {
        "success": True,
        "message": "Login successful",
        "user_id": user[0],
        "name": user[1],
        "email": user[2]
    }


# ---------------- LOGOUT ----------------

@app.get("/logout")
def logout():
    return RedirectResponse(
        "/login",
        status_code=303
    )


# ---------------- DASHBOARD ----------------

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user_id: int):
    connection = db()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id, name, email FROM users WHERE id = ?",
        (user_id,)
    )

    user = cursor.fetchone()
    connection.close()

    if not user:
        return RedirectResponse(
            "/login",
            status_code=303
        )

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user
        }
    )


# ---------------- MODULE PAGES ----------------

@app.get("/home", response_class=HTMLResponse)
def home_page(request: Request, user_id: int):
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "user_id": user_id
        }
    )


@app.get("/party", response_class=HTMLResponse)
def party_page(request: Request, user_id: int):
    return templates.TemplateResponse(
        "party.html",
        {
            "request": request,
            "user_id": user_id
        }
    )


@app.get("/jewelry", response_class=HTMLResponse)
def jewelry_page(request: Request, user_id: int):
    return templates.TemplateResponse(
        "jewelry.html",
        {
            "request": request,
            "user_id": user_id
        }
    )


# ---------------- HISTORY ----------------

@app.post("/delete-history/{recommendation_id}")
def delete_history(recommendation_id: int, user_id: int):
    connection = db()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM recommendations
        WHERE id = ? AND user_id = ?
        """,
        (recommendation_id, user_id)
    )

    connection.commit()
    connection.close()

    return RedirectResponse(
        url=f"/history?user_id={user_id}",
        status_code=303
    )
# ---------------- HISTORY PAGE ----------------

@app.get("/history", response_class=HTMLResponse)
def history_page(request: Request, user_id: int):

    connection = db()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, category, budget, input_details,
               recommendation, created_at
        FROM recommendations
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user_id,)
    )

    recommendations = cursor.fetchall()
    connection.close()

    return templates.TemplateResponse(
        "history.html",
        {
            "request": request,
            "user_id": user_id,
            "recommendations": recommendations
        }
    )
# ---------------- HOME RECOMMENDATION ----------------

@app.post("/generate-home")
def generate_home(request: HomeRequest):

    try:
        budget = float(request.budget)
    except (TypeError, ValueError):
        budget = 10000

    if budget >= 10000:

        result = f"""
1. LED Ceiling Light - Lighting - ₹1800
2. Curtains - Decor - ₹1500
3. Sofa Cushion Set - Furniture - ₹1200
4. Wall Art - Decor - ₹1000
5. Indoor Plant Set - Decor - ₹800
6. Small Coffee Table - Furniture - ₹2995

Total Estimated Cost: ₹9295
Remaining Budget: ₹{budget - 9295:.0f}

Room: {request.room}
Style: {request.style}
"""

    elif budget >= 5000:

        result = f"""
1. LED Ceiling Light - Lighting - ₹900
2. Curtains - Decor - ₹800
3. Wall Art - Decor - ₹700
4. Cushion Set - Decor - ₹600
5. Indoor Plants - Decor - ₹500
6. Small Table - Furniture - ₹1000

Total Estimated Cost: ₹4500
Remaining Budget: ₹{budget - 4500:.0f}

Room: {request.room}
Style: {request.style}
"""

    else:

        total = 2400
        remaining = max(0, budget - total)

        result = f"""
1. LED Light - Lighting - ₹500
2. Curtains - Decor - ₹600
3. Wall Decor - Decor - ₹500
4. Small Indoor Plant - Decor - ₹300
5. Cushion Set - Decor - ₹500

Total Estimated Cost: ₹{total}
Remaining Budget: ₹{remaining:.0f}

Room: {request.room}
Style: {request.style}
"""

    message = "Home recommendations generated successfully"

    save_recommendation(
        request.user_id,
        "Home Interior",
        request.budget,
        json.dumps({
            "room": request.room,
            "style": request.style
        }),
        result
    )

    return {
        "message": message,
        "budget": request.budget,
        "room": request.room,
        "style": request.style,
        "ai_recommendations": result
    }


@app.post("/generate-party")
def generate_party(request: PartyRequest):

    result = fallback_party(
        request.budget,
        request.event_type,
        request.guests,
        request.theme
    )

    message = "Party recommendations generated successfully"

    save_recommendation(
        request.user_id,
        "Party Planning",
        request.budget,
        json.dumps({
            "event_type": request.event_type,
            "guests": request.guests,
            "theme": request.theme
        }),
        result
    )

    return {
        "message": message,
        "budget": request.budget,
        "event_type": request.event_type,
        "guests": request.guests,
        "theme": request.theme,
        "ai_recommendations": result
    }

# ---------------- JEWELRY RECOMMENDATION ----------------

def fallback_jewelry(budget, jewelry_type, occasion, style):
    try:
        budget = float(budget)
    except (TypeError, ValueError):
        budget = 10000

    if budget >= 10000:
        return """
1. Gold Necklace - Necklace - ₹4500
2. Gold Earrings - Earrings - ₹1800
3. Traditional Bangles - Bangles - ₹1500
4. Simple Ring - Ring - ₹900

Total Estimated Cost: ₹8700
Remaining Budget: ₹1300
"""

    elif budget >= 5000:
        return """
1. Gold-Plated Necklace - Necklace - ₹2200
2. Earrings - Earrings - ₹900
3. Traditional Bangles - Bangles - ₹800
4. Simple Ring - Ring - ₹600

Total Estimated Cost: ₹4500
Remaining Budget: ₹500
"""

    else:
        total = 2100
        remaining = max(0, budget - total)

        return f"""
1. Simple Necklace - Necklace - ₹1200
2. Earrings - Earrings - ₹500
3. Bangles - Bangles - ₹400

Total Estimated Cost: ₹{total}
Remaining Budget: ₹{remaining:.0f}
"""


@app.post("/generate-jewelry")
def generate_jewelry(request: JewelryRequest):

    result = fallback_jewelry(
        request.budget,
        request.jewelry_type,
        request.occasion,
        request.style
    )

    message = "Jewelry recommendations generated successfully"

    save_recommendation(
        request.user_id,
        "Jewelry",
        request.budget,
        json.dumps({
            "jewelry_type": request.jewelry_type,
            "occasion": request.occasion,
            "style": request.style
        }),
        result
    )

    return {
        "message": message,
        "budget": request.budget,
        "jewelry_type": request.jewelry_type,
        "occasion": request.occasion,
        "style": request.style,
        "ai_recommendations": result
    }