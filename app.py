import os
import sys
import shutil
import uuid
from typing import Optional, List
from fastapi import FastAPI, Request, Form, File, UploadFile, Depends, HTTPException, status, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Robust directory paths for Local & Vercel Serverless
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Set up ephemeral file storage for Vercel vs Local
UPLOAD_DIR = "/tmp/uploads" if os.getenv("VERCEL") else os.path.join(STATIC_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Internal module imports
import database
import auth
import gemini_service

app = FastAPI(
    title="PocketSmart AI",
    description="GenAI-powered budget-conscious multi-platform shopping & vendor allocation engine",
    version="1.0.0"
)

# Mount static files with absolute path
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Configure Jinja2 templates with absolute path
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# ==========================================
# PYDANTIC MODELS FOR API REQUESTS
# ==========================================

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None

class LoginRequest(BaseModel):
    username_or_email: str
    password: str

class HomeBudgetRequest(BaseModel):
    room_type: str
    room_size: str
    total_budget: float
    items_needed: List[str] = []
    style_preference: str = "Modern Contemporary"
    priority: str = "Balanced"
    currency: str = "INR"

class PartyBudgetRequest(BaseModel):
    event_type: str
    guest_count: int
    venue_type: str
    services_needed: List[str] = []
    total_budget: float
    food_preference: str = "Mixed (Veg & Non-Veg)"
    currency: str = "INR"

# ==========================================
# HTML PAGE ROUTES
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    user = auth.get_current_user_optional(request)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "user": user,
            "title": "PocketSmart AI - Smart Budget & Shopping Allocator"
        }
    )

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = auth.get_current_user_optional(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "user": None,
            "title": "Sign In - PocketSmart AI"
        }
    )

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    user = auth.get_current_user_optional(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "user": None,
            "title": "Create Account - PocketSmart AI"
        }
    )

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    user = auth.get_current_user_optional(request)
    if not user:
        return RedirectResponse(url="/login?redirect=/dashboard", status_code=303)
    
    stats = database.get_user_stats(user["id"])
    recent_plans = database.get_recommendations(user_id=user["id"], limit=6)
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": user,
            "stats": stats,
            "recent_plans": recent_plans,
            "title": "Dashboard - PocketSmart AI"
        }
    )

@app.get("/home-planner", response_class=HTMLResponse)
async def home_planner_page(request: Request):
    user = auth.get_current_user_optional(request)
    return templates.TemplateResponse(
        request=request,
        name="home_planner.html",
        context={
            "user": user,
            "title": "Home Interior Planner - PocketSmart AI"
        }
    )

@app.get("/party-planner", response_class=HTMLResponse)
async def party_planner_page(request: Request):
    user = auth.get_current_user_optional(request)
    return templates.TemplateResponse(
        request=request,
        name="party_planner.html",
        context={
            "user": user,
            "title": "Party & Event Budget Planner - PocketSmart AI"
        }
    )

@app.get("/jewelry-planner", response_class=HTMLResponse)
async def jewelry_planner_page(request: Request):
    user = auth.get_current_user_optional(request)
    return templates.TemplateResponse(
        request=request,
        name="jewelry_planner.html",
        context={
            "user": user,
            "title": "Jewelry Stylist & Budget Planner - PocketSmart AI"
        }
    )

@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    user = auth.get_current_user_optional(request)
    if not user:
        return RedirectResponse(url="/login?redirect=/history", status_code=303)
    
    recommendations = database.get_recommendations(user_id=user["id"], limit=100)
    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={
            "user": user,
            "recommendations": recommendations,
            "title": "My Recommendation History - PocketSmart AI"
        }
    )

# ==========================================
# AUTHENTICATION API ENDPOINTS
# ==========================================

@app.post("/register")
async def register_user(reg: RegisterRequest, response: Response):
    # Check if username or email is already taken
    if database.get_user_by_username(reg.username):
        raise HTTPException(status_code=400, detail="Username is already registered")
    if database.get_user_by_email(reg.email):
        raise HTTPException(status_code=400, detail="Email is already registered")
    
    if len(reg.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    hashed_pw = auth.hash_password(reg.password)
    user = database.create_user(reg.username, reg.email, hashed_pw, reg.full_name)
    if not user:
        raise HTTPException(status_code=500, detail="Failed to create user account")

    # Generate JWT
    token = auth.create_access_token({"sub": user["username"], "user_id": user["id"]})
    
    # Set HTTP-only Cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=auth.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False  # Set to True on production HTTPS
    )

    return {
        "success": True,
        "message": "Account created successfully",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"]
        }
    }

@app.post("/login")
async def login_user(login_data: LoginRequest, response: Response):
    user = database.get_user_by_username(login_data.username_or_email)
    if not user:
        user = database.get_user_by_email(login_data.username_or_email)

    if not user or not auth.verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = auth.create_access_token({"sub": user["username"], "user_id": user["id"]})
    
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=auth.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False
    )

    return {
        "success": True,
        "message": "Logged in successfully",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "full_name": user["full_name"]
        }
    }

@app.post("/token")
async def token_endpoint(username: str = Form(...), password: str = Form(...)):
    """OAuth2 password spec compliant token endpoint."""
    user = database.get_user_by_username(username) or database.get_user_by_email(username)
    if not user or not auth.verify_password(password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = auth.create_access_token({"sub": user["username"], "user_id": user["id"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/logout")
async def logout(response: Response):
    res = RedirectResponse(url="/login", status_code=303)
    res.delete_cookie(key="access_token")
    return res

# ==========================================
# DOMAIN ENGINE API ENDPOINTS
# ==========================================

@app.post("/home-budget")
async def calculate_home_budget(req: HomeBudgetRequest, request: Request):
    user = auth.get_current_user_optional(request)
    
    result = gemini_service.generate_home_budget(
        room_type=req.room_type,
        room_size=req.room_size,
        budget=req.total_budget,
        items_needed=req.items_needed,
        style_preference=req.style_preference,
        priority=req.priority,
        currency=req.currency
    )

    # Save to history if user logged in
    rec_id = None
    if user:
        rec_id = database.save_recommendation(
            user_id=user["id"],
            category="home",
            title=f"{req.room_type} ({req.style_preference})",
            input_params=req.model_dump(),
            result_data=result,
            total_budget=req.total_budget,
            allocated_budget=result.get("allocated_budget", req.total_budget)
        )

    return {
        "success": True,
        "recommendation_id": rec_id,
        "data": result
    }

@app.post("/party-budget")
async def calculate_party_budget(req: PartyBudgetRequest, request: Request):
    user = auth.get_current_user_optional(request)
    
    result = gemini_service.generate_party_budget(
        event_type=req.event_type,
        guest_count=req.guest_count,
        venue_type=req.venue_type,
        services_needed=req.services_needed,
        total_budget=req.total_budget,
        food_preference=req.food_preference,
        currency=req.currency
    )

    rec_id = None
    if user:
        rec_id = database.save_recommendation(
            user_id=user["id"],
            category="party",
            title=f"{req.event_type} for {req.guest_count} guests",
            input_params=req.model_dump(),
            result_data=result,
            total_budget=req.total_budget,
            allocated_budget=result.get("allocated_budget", req.total_budget)
        )

    return {
        "success": True,
        "recommendation_id": rec_id,
        "data": result
    }

@app.post("/jewelry-budget")
async def calculate_jewelry_budget(
    request: Request,
    occasion: str = Form(...),
    outfit_description: str = Form(...),
    metal_preference: str = Form(...),
    total_budget: float = Form(...),
    currency: str = Form("INR"),
    outfit_image: Optional[UploadFile] = File(None)
):
    user = auth.get_current_user_optional(request)
    
    image_bytes = None
    image_mime_type = None
    saved_image_path = None
    
    if outfit_image and outfit_image.filename:
        try:
            image_bytes = await outfit_image.read()
            image_mime_type = outfit_image.content_type or "image/jpeg"
            
            # Save file to uploads folder
            ext = os.path.splitext(outfit_image.filename)[1] or ".jpg"
            filename = f"outfit_{uuid.uuid4().hex[:8]}{ext}"
            saved_image_path = os.path.join(UPLOAD_DIR, filename)
            with open(saved_image_path, "wb") as f:
                f.write(image_bytes)
        except Exception as e:
            print(f"Error handling image upload: {e}")

    result = gemini_service.generate_jewelry_budget(
        occasion=occasion,
        outfit_description=outfit_description,
        metal_preference=metal_preference,
        total_budget=total_budget,
        currency=currency,
        image_bytes=image_bytes,
        image_mime_type=image_mime_type
    )

    rec_id = None
    if user:
        input_params = {
            "occasion": occasion,
            "outfit_description": outfit_description,
            "metal_preference": metal_preference,
            "total_budget": total_budget,
            "currency": currency,
            "has_image": bool(image_bytes)
        }
        rec_id = database.save_recommendation(
            user_id=user["id"],
            category="jewelry",
            title=f"{occasion} - {metal_preference} Set",
            input_params=input_params,
            result_data=result,
            total_budget=total_budget,
            allocated_budget=result.get("allocated_budget", total_budget),
            image_path=saved_image_path
        )

    return {
        "success": True,
        "recommendation_id": rec_id,
        "data": result
    }

# ==========================================
# HISTORY & STATS API ENDPOINTS
# ==========================================

@app.get("/recommendation-history")
async def get_history(request: Request, category: Optional[str] = "all"):
    user = auth.get_current_user_optional(request)
    if not user:
        return {"success": False, "message": "User not authenticated", "recommendations": []}
    
    recs = database.get_recommendations(user_id=user["id"], category=category)
    return {"success": True, "recommendations": recs}

@app.get("/recommendation-details/{rec_id}")
async def get_recommendation_details(rec_id: int, request: Request):
    user = auth.get_current_user_optional(request)
    user_id = user["id"] if user else None
    
    rec = database.get_recommendation_by_id(rec_id, user_id=user_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation record not found")
        
    return {"success": True, "recommendation": rec}

@app.delete("/recommendation/{rec_id}")
async def delete_rec(rec_id: int, request: Request):
    user = auth.get_current_user(request)
    success = database.delete_recommendation(rec_id, user_id=user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Item not found or unauthorized")
    return {"success": True, "message": "Recommendation removed"}

@app.get("/api/user-stats")
async def user_stats_endpoint(request: Request):
    user = auth.get_current_user(request)
    stats = database.get_user_stats(user["id"])
    return {"success": True, "stats": stats}

@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "app": "PocketSmart AI",
        "gemini_model": gemini_service.GEMINI_MODEL,
        "has_gemini_key": bool(gemini_service.GEMINI_API_KEY and gemini_service.GEMINI_API_KEY != "your_gemini_api_key_here"),
        "serverless": bool(os.getenv("VERCEL"))
    }
