import os
import io
from PIL import Image
from fastapi.testclient import TestClient
from app import app
import database

client = TestClient(app)

def test_health():
    print("Testing /api/health...")
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["app"] == "PocketSmart AI"
    print("  Passed: /api/health")

def test_page_routes():
    print("Testing HTML View Routes...")
    pages = ["/", "/login", "/register", "/home-planner", "/party-planner", "/jewelry-planner"]
    for path in pages:
        res = client.get(path)
        assert res.status_code == 200, f"Failed for {path}: {res.status_code}"
        assert "<html" in res.text.lower()
    
    # Protected routes redirect to login when unauthenticated
    res = client.get("/dashboard", follow_redirects=False)
    assert res.status_code == 303
    assert "/login" in res.headers["location"]
    
    res = client.get("/history", follow_redirects=False)
    assert res.status_code == 303
    assert "/login" in res.headers["location"]
    print("  Passed: All HTML View Routes and Route Guards")

def test_auth_flow():
    print("Testing Registration and Login JWT Flows...")
    username = "testuser"
    email = "testuser@example.com"
    password = "securePassword123!"

    # Clean existing user if re-running
    conn = database.get_db_connection()
    conn.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()

    # 1. Register
    reg_res = client.post("/register", json={
        "username": username,
        "email": email,
        "password": password,
        "full_name": "Test User"
    })
    assert reg_res.status_code == 200, f"Register failed: {reg_res.text}"
    reg_data = reg_res.json()
    assert reg_data["success"] is True
    assert "access_token" in reg_data
    assert "access_token" in reg_res.cookies

    # 2. Duplicate registration protection
    dup_res = client.post("/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    assert dup_res.status_code == 400

    # 3. Login
    login_res = client.post("/login", json={
        "username_or_email": username,
        "password": password
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["success"] is True
    assert "access_token" in login_data

    # 4. Access protected dashboard with cookie
    dash_res = client.get("/dashboard", cookies={"access_token": f"Bearer {login_data['access_token']}"})
    assert dash_res.status_code == 200
    assert "Test User" in dash_res.text

    print("  Passed: Auth registration, login, JWT validation, and cookie persistence")

def test_home_budget_calculation():
    print("Testing Home Planner Budget Calculation...")
    target_budget = 40000.0
    res = client.post("/home-budget", json={
        "room_type": "Living Room",
        "room_size": "Medium (150-300 sq ft)",
        "total_budget": target_budget,
        "items_needed": ["Sofa & Seating", "Coffee Table", "LED Lighting"],
        "style_preference": "Modern Contemporary",
        "priority": "Balanced",
        "currency": "INR"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    result = data["data"]
    
    # Strict validation: allocated <= target budget
    assert result["allocated_budget"] <= target_budget
    assert result["total_budget"] == target_budget
    assert len(result["items"]) > 0
    
    # Check that store links are generated
    first_item = result["items"][0]
    assert "store_links" in first_item
    assert "amazon" in first_item["store_links"]
    assert "flipkart" in first_item["store_links"]
    assert "ikea" in first_item["store_links"]
    assert "amazon.in" in first_item["store_links"]["amazon"]
    print(f"  Passed: Home budget allocated INR {result['allocated_budget']} <= INR {target_budget} with active shopping links")

def test_party_budget_calculation():
    print("Testing Party Planner Budget Calculation...")
    target_budget = 25000.0
    guests = 20
    res = client.post("/party-budget", json={
        "event_type": "Birthday Celebration",
        "guest_count": guests,
        "venue_type": "Living Room / Apartment",
        "services_needed": ["Gourmet Catering", "Beverages & Mocktails", "Themed Decor & Balloons"],
        "total_budget": target_budget,
        "food_preference": "Mixed (Veg & Non-Veg)",
        "currency": "INR"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    result = data["data"]

    # Budget cap check
    assert result["allocated_budget"] <= target_budget
    assert result["guest_count"] == guests
    assert result["cost_per_guest"] > 0
    assert len(result["categories"]) > 0
    
    # Check vendor links
    first_cat = result["categories"][0]
    assert "action_links" in first_cat
    assert "swiggy" in first_cat["action_links"]
    assert "zomato" in first_cat["action_links"]
    assert "blinkit" in first_cat["action_links"]
    print(f"  Passed: Party budget allocated INR {result['allocated_budget']} (INR {result['cost_per_guest']}/guest) with vendor routes")

def test_jewelry_budget_multimodal():
    print("Testing Multimodal Jewelry Planner (with image upload)...")
    target_budget = 60000.0
    
    # Create in-memory mock outfit JPEG
    img = Image.new("RGB", (200, 200), color="darkgreen")
    img_io = io.BytesIO()
    img.save(img_io, format="JPEG")
    img_io.seek(0)

    res = client.post(
        "/jewelry-budget",
        data={
            "occasion": "Wedding Reception",
            "outfit_description": "Emerald green silk saree with gold zari border",
            "metal_preference": "22K Yellow Gold",
            "total_budget": target_budget,
            "currency": "INR"
        },
        files={
            "outfit_image": ("outfit.jpg", img_io, "image/jpeg")
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    result = data["data"]

    assert result["allocated_budget"] <= target_budget
    assert len(result["jewelry_pieces"]) > 0
    
    first_piece = result["jewelry_pieces"][0]
    assert "store_links" in first_piece
    assert "bluestone" in first_piece["store_links"]
    assert "caratlane" in first_piece["store_links"]
    assert "tanishq" in first_piece["store_links"]
    print(f"  Passed: Jewelry multimodal allocated INR {result['allocated_budget']} <= INR {target_budget} with brand links")

if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING POCKETSMART AI AUTOMATED QUALITY ASSURANCE TEST SUITE")
    print("=" * 60)
    test_health()
    test_page_routes()
    test_auth_flow()
    test_home_budget_calculation()
    test_party_budget_calculation()
    test_jewelry_budget_multimodal()
    print("=" * 60)
    print("ALL TESTS PASSED WITH ZERO ERRORS!")
    print("=" * 60)
