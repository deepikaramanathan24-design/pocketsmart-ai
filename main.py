
import json
import sqlite3
import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

from database import create_database, DB_NAME
from models import (
    RegisterRequest,
    LoginRequest,
    ResetPasswordRequest,
    HomeRequest,
    PartyRequest,
    JewelryRequest,
)

app = FastAPI(title="PocketSmart AI")

# Static files and HTML templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create database tables
create_database()


# --------------------------------------------------
# DATABASE HELPERS
# --------------------------------------------------

def get_connection():
    return sqlite3.connect(DB_NAME)


def get_user_by_id(user_id: int):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    )
    user = cursor.fetchone()
    conn.close()
    return user


def get_user_by_email(email: str):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    )
    user = cursor.fetchone()
    conn.close()
    return user


def save_recommendation(
    user_id: int,
    category: str,
    budget: float,
    user_input,
    recommendation: str,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO recommendations
        (user_id, category, budget, input_data, recommendation)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            category,
            budget,
            json.dumps(user_input),
            recommendation,
        ),
    )

    conn.commit()
    conn.close()


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str):
    try:
        return pwd_context.verify(password, hashed_password)
    except Exception:
        return False


# --------------------------------------------------
# FALLBACK RECOMMENDATIONS
# --------------------------------------------------

def fallback_home(budget: float, room_type: str = "Bedroom"):
    if budget <= 10000:
        return (
            f"Budget-friendly {room_type} Interior Plan (Budget: ₹{budget:,.0f})\n\n"
            "1. Wall paint and simple decoration - ₹2,000\n"
            "2. LED lighting - ₹1,000\n"
            "3. Curtains and bedsheet - ₹2,000\n"
            "4. Storage and organizers - ₹2,000\n"
            "5. Small decor items - ₹1,500\n"
            "6. Extra budget reserve - ₹1,500\n\n"
            "Tip: Compare prices before buying and adjust the items to your budget."
        )

    return (
        f"Home Interior Plan for {room_type} (Budget: ₹{budget:,.0f})\n\n"
        "1. Wall paint and finish - 15% of budget\n"
        "2. Lighting - 10% of budget\n"
        "3. Furniture - 35% of budget\n"
        "4. Curtains and furnishings - 15% of budget\n"
        "5. Storage - 15% of budget\n"
        "6. Decoration and reserve - 10% of budget\n\n"
        "Tip: Get quotations from multiple vendors before purchasing."
    )


def fallback_party(budget: float, occasion: str = "Birthday"):
    return (
        f"{occasion} Party Plan (Budget: ₹{budget:,.0f})\n\n"
        "1. Venue or home decoration - 20% of budget\n"
        "2. Food and refreshments - 35% of budget\n"
        "3. Cake and desserts - 15% of budget\n"
        "4. Decorations - 10% of budget\n"
        "5. Games and entertainment - 10% of budget\n"
        "6. Emergency reserve - 10% of budget\n\n"
        "Tip: Confirm guest count first to avoid overspending."
    )


def fallback_jewelry(budget: float, jewelry_type: str = "Gold",
                     occasion: str = "Wedding",
                     style: str = "Traditional"):
    return (
        f"{style} {jewelry_type} Jewelry Ideas for {occasion}\n"
        f"Budget: ₹{budget:,.0f}\n\n"
        "Suggested budget allocation:\n"
        "1. Main jewelry item - 50% of budget\n"
        "2. Earrings or matching accessory - 20% of budget\n"
        "3. Additional jewelry - 20% of budget\n"
        "4. Reserve for price differences - 10% of budget\n\n"
        "Tip: Check the current price, making charges, weight, and hallmark "
        "before buying. Actual prices vary by jeweler and design."
    )


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request},
    )


# --------------------------------------------------
# LOGIN / REGISTER PAGES
# --------------------------------------------------

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"request": request},
    )


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"request": request},
    )


@app.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="forgot_password.html",
        context={"request": request},
    )


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@app.post("/register")
def register(data: RegisterRequest):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE email = ?",
            (data.email,)
        )

        if cursor.fetchone():
            conn.close()
            return JSONResponse(
                {"success": False, "message": "Email already registered."},
                status_code=400,
            )

        hashed = hash_password(data.password)

        # This assumes your users table has:
        # name, email, password columns.
        cursor.execute(
            """
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
            """,
            (data.name, data.email, hashed),
        )

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "Registration successful. Please login.",
        }

    except Exception as exc:
        print("REGISTER ERROR:", exc)
        return JSONResponse(
            {"success": False, "message": "Registration failed."},
            status_code=500,
        )


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.post("/login")
def login(data: LoginRequest):
    try:
        user = get_user_by_email(data.email)

        if not user:
            return JSONResponse(
                {"success": False, "message": "Invalid email or password."},
                status_code=401,
            )

        stored_password = user["password"]

        if not verify_password(data.password, stored_password):
            return JSONResponse(
                {"success": False, "message": "Invalid email or password."},
                status_code=401,
            )

        return {
            "success": True,
            "message": "Login successful.",
            "user_id": user["id"],
            "name": user["name"],
            "redirect_url": f"/dashboard?user_id={user['id']}",
        }

    except Exception as exc:
        print("LOGIN ERROR:", exc)
        return JSONResponse(
            {"success": False, "message": "Login failed."},
            status_code=500,
        )


# --------------------------------------------------
# FORGOT PASSWORD
# --------------------------------------------------

@app.post("/forgot-password")
def reset_password(data: ResetPasswordRequest):
    try:
        user = get_user_by_email(data.email)

        if not user:
            return JSONResponse(
                {"success": False, "message": "Email not found."},
                status_code=404,
            )

        hashed = hash_password(data.new_password)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password = ? WHERE email = ?",
            (hashed, data.email),
        )
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "Password updated successfully.",
        }

    except Exception as exc:
        print("RESET PASSWORD ERROR:", exc)
        return JSONResponse(
            {"success": False, "message": "Could not reset password."},
            status_code=500,
        )


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user_id: int):
    user = get_user_by_id(user_id)

    if not user:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"request": request, "user": user},
    )


# --------------------------------------------------
# RECOMMENDATION PAGES
# --------------------------------------------------

@app.get("/home", response_class=HTMLResponse)
def home_page(request: Request, user_id: int):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"request": request, "user_id": user_id},
    )


@app.get("/party", response_class=HTMLResponse)
def party_page(request: Request, user_id: int):
    return templates.TemplateResponse(
        request=request,
        name="party.html",
        context={"request": request, "user_id": user_id},
    )


@app.get("/jewelry", response_class=HTMLResponse)
def jewelry_page(request: Request, user_id: int):
    return templates.TemplateResponse(
        request=request,
        name="jewelry.html",
        context={"request": request, "user_id": user_id},
    )


# --------------------------------------------------
# GENERATE HOME INTERIOR RECOMMENDATION
# --------------------------------------------------

@app.post("/generate-home")
def generate_home(data: HomeRequest):
    try:
        budget = float(data.budget)
        user_id = int(data.user_id)

        room_type = getattr(data, "room_type", "Bedroom")
        if not room_type:
            room_type = "Bedroom"

        recommendation = fallback_home(budget, str(room_type))

        save_recommendation(
            user_id=user_id,
            category="Home Interior",
            budget=budget,
            user_input=data.model_dump(),
            recommendation=recommendation,
        )

        return {
            "success": True,
            "recommendation": recommendation,
        }

    except Exception as exc:
        print("HOME RECOMMENDATION ERROR:", exc)
        return JSONResponse(
            {"success": False, "message": "Could not generate recommendation."},
            status_code=500,
        )


# --------------------------------------------------
# GENERATE PARTY RECOMMENDATION
# --------------------------------------------------

@app.post("/generate-party")
def generate_party(data: PartyRequest):
    try:
        budget = float(data.budget)
        user_id = int(data.user_id)

        occasion = getattr(data, "occasion", "Birthday")
        if not occasion:
            occasion = "Birthday"

        recommendation = fallback_party(budget, str(occasion))

        save_recommendation(
            user_id=user_id,
            category="Party Planning",
            budget=budget,
            user_input=data.model_dump(),
            recommendation=recommendation,
        )

        return {
            "success": True,
            "recommendation": recommendation,
        }

    except Exception as exc:
        print("PARTY RECOMMENDATION ERROR:", exc)
        return JSONResponse(
            {"success": False, "message": "Could not generate recommendation."},
            status_code=500,
        )


# --------------------------------------------------
# GENERATE JEWELRY RECOMMENDATION
# --------------------------------------------------

@app.post("/generate-jewelry")
def generate_jewelry(data: JewelryRequest):
    try:
        budget = float(data.budget)
        user_id = int(data.user_id)

        jewelry_type = getattr(data, "jewelry_type", "Gold")
        occasion = getattr(data, "occasion", "Wedding")
        style = getattr(data, "style", "Traditional")

        recommendation = fallback_jewelry(
            budget,
            str(jewelry_type),
            str(occasion),
            str(style),
        )

        save_recommendation(
            user_id=user_id,
            category="Jewelry",
            budget=budget,
            user_input=data.model_dump(),
            recommendation=recommendation,
        )

        return {
            "success": True,
            "recommendation": recommendation,
        }

    except Exception as exc:
        print("JEWELRY RECOMMENDATION ERROR:", exc)
        return JSONResponse(
            {"success": False, "message": "Could not generate recommendation."},
            status_code=500,
        )


# --------------------------------------------------
# RECOMMENDATION HISTORY
# --------------------------------------------------

@app.get("/history", response_class=HTMLResponse)
def history_page(request: Request, user_id: int):
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, category, budget, input_data, recommendation
            FROM recommendations
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user_id,),
        )

        recommendations = cursor.fetchall()
        conn.close()

        return templates.TemplateResponse(
            request=request,
            name="history.html",
            context={
                "request": request,
                "user_id": user_id,
                "recommendations": recommendations,
            },
        )

    except Exception as exc:
        print("HISTORY ERROR:", exc)
        return HTMLResponse(
            "Unable to load recommendation history.",
            status_code=500,
        )


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.get("/logout")
def logout():
    return RedirectResponse("/", status_code=303)
