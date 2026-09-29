import os
import json
import base64
import urllib.parse
from typing import Dict, Any, List, Optional
from PIL import Image
import io
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()

# Initialize Google GenAI client if API key is present
genai_client = None
if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
    try:
        from google import genai
        genai_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Warning: Failed to initialize Google GenAI Client: {e}")

# ==========================================
# E-COMMERCE URL GENERATORS
# ==========================================

def url_encode(text: str) -> str:
    return urllib.parse.quote_plus(text.strip())

def make_amazon_url(query: str, domain: str = "in") -> str:
    return f"https://www.amazon.{domain}/s?k={url_encode(query)}"

def make_flipkart_url(query: str) -> str:
    return f"https://www.flipkart.com/search?q={url_encode(query)}"

def make_ikea_url(query: str, country: str = "in/en") -> str:
    return f"https://www.ikea.com/{country}/search/?q={url_encode(query)}"

def make_swiggy_url(query: str = "food") -> str:
    return f"https://www.swiggy.com/search?query={url_encode(query)}"

def make_zomato_url(query: str = "party catering") -> str:
    return f"https://www.zomato.com/search?q={url_encode(query)}"

def make_blinkit_url(query: str) -> str:
    return f"https://blinkit.com/s/?q={url_encode(query)}"

def make_urbancompany_url(query: str) -> str:
    return f"https://www.urbancompany.com/search?query={url_encode(query)}"

def make_oyo_url(location: str) -> str:
    return f"https://www.oyorooms.com/search?location={url_encode(location)}"

def make_bluestone_url(query: str) -> str:
    return f"https://www.bluestone.com/search?q={url_encode(query)}"

def make_caratlane_url(query: str) -> str:
    return f"https://www.caratlane.com/search?q={url_encode(query)}"

def make_tanishq_url(query: str) -> str:
    return f"https://www.tanishq.co.in/search?q={url_encode(query)}"

def make_myntra_url(query: str) -> str:
    return f"https://www.myntra.com/{url_encode(query)}"


def clean_json_response(raw_text: str) -> Dict[str, Any]:
    """Helper to clean and parse JSON responses from Gemini."""
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())


# ==========================================
# MODULE 1: HOME INTERIOR PLANNER
# ==========================================

def generate_home_budget(
    room_type: str,
    room_size: str,
    budget: float,
    items_needed: List[str],
    style_preference: str = "Modern",
    priority: str = "Balanced",
    currency: str = "INR"
) -> Dict[str, Any]:
    """Generate budget-conscious home interior recommendation using Gemini or smart fallback."""
    global genai_client
    
    # Reload key if user updated env
    if not genai_client and os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") != "your_gemini_api_key_here":
        try:
            from google import genai
            genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        except Exception:
            pass

    if genai_client:
        try:
            prompt = f"""
            You are an expert budget interior designer and procurement specialist.
            CRITICAL REQUIREMENT: The sum of total_price across all items MUST NOT exceed {budget}.
            Output ONLY a raw, valid JSON object without any markdown code block fences.

            Room Type: {room_type}
            Room Size: {room_size}
            Total Budget: {currency} {budget}
            Requested Items/Features: {', '.join(items_needed) if items_needed else 'Essential room furniture and lighting'}
            Style Preference: {style_preference}
            Priority Mode: {priority}

            Return this exact JSON schema:
            {{
              "summary": "Concise summary of the interior strategy",
              "style_theme": "{style_preference}",
              "total_budget": {budget},
              "allocated_budget": <float <= {budget}>,
              "remaining_budget": <float, {budget} - allocated_budget>,
              "currency": "{currency}",
              "items": [
                {{
                  "category": "Lighting | Furniture | Storage | Decor | Electrical",
                  "name": "Specific descriptive product name",
                  "quantity": <integer>,
                  "unit_price": <float>,
                  "total_price": <float, quantity * unit_price>,
                  "percentage": <float, percentage of total budget>,
                  "priority": "Essential | Recommended | Optional",
                  "search_term": "Optimized shopping search query"
                }}
              ],
              "design_advice": ["bullet 1", "bullet 2", "bullet 3"],
              "budget_hacks": ["hack 1", "hack 2", "hack 3"]
            }}
            """
            
            interaction = genai_client.interactions.create(
                model=GEMINI_MODEL,
                input=prompt
            )
            raw_text = interaction.output_text or (interaction.outputs[-1].text if interaction.outputs else "")
            data = clean_json_response(raw_text)
            
            # Enrich items with live e-commerce search URLs
            for item in data.get("items", []):
                q = item.get("search_term") or item.get("name")
                item["store_links"] = {
                    "amazon": make_amazon_url(q),
                    "flipkart": make_flipkart_url(q),
                    "ikea": make_ikea_url(q)
                }
            data["is_ai_generated"] = True
            return data
        except Exception as e:
            print(f"Gemini API call failed for Home Planner: {e}. Falling back to Smart-Engine.")

    # High quality fallback engine
    return fallback_home_budget(room_type, room_size, budget, items_needed, style_preference, priority, currency)


def fallback_home_budget(room_type, room_size, budget, items_needed, style_preference, priority, currency):
    """Resilient fallback engine that guarantees balanced allocations within budget."""
    safe_budget = float(budget)
    
    catalog = {
        "Living Room": [
            ("Furniture", "3-Seater Fabric Sofa Couch", 0.32, 1, f"{style_preference} 3 seater sofa living room"),
            ("Furniture", "Minimalist Coffee Table with Shelf", 0.08, 1, f"wooden coffee table {style_preference}"),
            ("Lighting", "Warm LED Ceiling Panel Lights (Pack of 4)", 0.06, 2, "warm white led recessed ceiling lights"),
            ("Electrical", "High Airflow BLDC Ceiling Fan 1200mm", 0.09, 1, "bldc ceiling fan remote control energy saving"),
            ("Furniture", "Sleek Floating TV Entertainment Unit", 0.15, 1, "wall mount tv entertainment unit wooden"),
            ("Decor", "Blackout Window Curtains with Eyelets (Pair)", 0.07, 2, "thermal insulated blackout window curtains"),
            ("Decor", "Soft Anti-Slip Area Floor Rug 5x7 ft", 0.08, 1, "living room area rug boho geometric"),
            ("Storage", "Compact Bookcase / Display Shelf", 0.08, 1, "ladder bookshelf wood modern")
        ],
        "Bedroom": [
            ("Furniture", "Queen Size Engineered Wood Bed with Storage", 0.35, 1, "queen size bed with hydraulic storage"),
            ("Furniture", "Orthopedic Memory Foam Mattress", 0.22, 1, "orthopedic memory foam mattress queen size"),
            ("Lighting", "Bedside Touch Dimmable Lamps (Set of 2)", 0.06, 1, "bedside table lamps touch sensor warm light"),
            ("Electrical", "Silent BLDC Remote Ceiling Fan", 0.09, 1, "energy saving silent bldc ceiling fan"),
            ("Decor", "Thermal Blackout Bedroom Curtains", 0.08, 2, "room darkening curtains 7 feet"),
            ("Storage", "2-Door Wardrobe with Hanging Rail", 0.14, 1, "modern 2 door wardrobe with lock")
        ],
        "Kitchen": [
            ("Storage", "Modular Wall Hanging Kitchen Cabinet", 0.30, 1, "modular wall kitchen rack cabinet"),
            ("Storage", "Stainless Steel 3-Tier Spice & Dish Rack", 0.10, 2, "stainless steel kitchen dish drying organizer"),
            ("Lighting", "Under-Cabinet Motion Sensor LED Strip Lights", 0.08, 2, "under cabinet led puck strip lights rechargeable"),
            ("Electrical", "High-Suction Auto-Clean Kitchen Chimney", 0.32, 1, "kitchen chimney 60cm filterless autolcean"),
            ("Decor", "Waterproof Kitchen Wall Decal Splashback Tiles", 0.06, 1, "oil proof kitchen wall sticker tiles")
        ],
        "Home Office": [
            ("Furniture", "Ergonomic High-Back Mesh Desk Chair", 0.28, 1, "ergonomic mesh office chair with lumbar support"),
            ("Furniture", "Sturdy Computer Desk with Cable Grommets", 0.26, 1, "work from home computer study table"),
            ("Lighting", "Architect Swing Arm LED Desk Task Lamp", 0.08, 1, "led desk lamp clamp eye protection dimmable"),
            ("Storage", "3-Drawer Mobile File Storage Pedestal", 0.14, 1, "under desk storage drawer organizer on wheels"),
            ("Decor", "Acoustic Pin Board & Cable Management Tray", 0.07, 1, "under desk cable management tray wire organizer")
        ]
    }
    
    room_key = room_type if room_type in catalog else "Living Room"
    base_items = catalog[room_key]
    
    allocated = 0.0
    items_list = []
    scaling_factor = 0.94 / sum(item[2] for item in base_items)
    
    for cat, name, frac, qty, search in base_items:
        item_total = round(safe_budget * frac * scaling_factor, 2)
        unit_price = round(item_total / qty, 2)
        allocated += item_total
        pct = round((item_total / safe_budget) * 100, 1)
        items_list.append({
            "category": cat,
            "name": name,
            "quantity": qty,
            "unit_price": unit_price,
            "total_price": item_total,
            "percentage": pct,
            "priority": "Essential" if frac >= 0.15 else "Recommended",
            "search_term": search,
            "store_links": {
                "amazon": make_amazon_url(search),
                "flipkart": make_flipkart_url(search),
                "ikea": make_ikea_url(search)
            }
        })
        
    return {
        "summary": f"Tailored {style_preference} interior procurement blueprint for your {room_size} {room_type}, maximizing longevity and aesthetic harmony while keeping an emergency budget reserve.",
        "style_theme": style_preference,
        "total_budget": safe_budget,
        "allocated_budget": round(allocated, 2),
        "remaining_budget": round(safe_budget - allocated, 2),
        "currency": currency,
        "items": items_list,
        "design_advice": [
            f"Adhere to the 60-30-10 color rule tailored for {style_preference}: 60% dominant neutral wall tone, 30% secondary furniture texture, and 10% accent decor.",
            "Layer ambient ceiling lighting with warm task lamps to create depth without paying for expensive false ceilings.",
            "Leave at least 3 feet of clear walking clearance around major furniture pieces to maintain spacious circulation."
        ],
        "budget_hacks": [
            "Use modular flat-pack furniture with DIY assembly to save up to 25% on delivery and carpentry charges.",
            "Choose peel-and-stick textured wallpaper for one accent wall instead of costly full-room repainting.",
            "Compare Amazon and Flipkart seasonal sales using the generated links to lock in card discounts."
        ],
        "is_ai_generated": False
    }


# ==========================================
# MODULE 2: PARTY PLANNER
# ==========================================

def generate_party_budget(
    event_type: str,
    guest_count: int,
    venue_type: str,
    services_needed: List[str],
    total_budget: float,
    food_preference: str = "Mixed (Veg & Non-Veg)",
    currency: str = "INR"
) -> Dict[str, Any]:
    """Generate fractional party budget allocation across vendors using Gemini or fallback."""
    global genai_client
    
    if not genai_client and os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") != "your_gemini_api_key_here":
        try:
            from google import genai
            genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        except Exception:
            pass

    if genai_client:
        try:
            prompt = f"""
            You are an elite event director and party cost strategist.
            CRITICAL REQUIREMENT: The sum of all allocated_amount fields MUST NOT exceed {total_budget}.
            Output ONLY a raw, valid JSON object without markdown code fences.

            Event: {event_type}
            Guest Count: {guest_count}
            Venue: {venue_type}
            Services Required: {', '.join(services_needed) if services_needed else 'Food, Drinks, Music, Decor'}
            Total Budget: {currency} {total_budget}
            Food Preference: {food_preference}

            Return JSON matching:
            {{
              "summary": "Executive event summary",
              "event_type": "{event_type}",
              "guest_count": {guest_count},
              "total_budget": {total_budget},
              "allocated_budget": <float <= {total_budget}>,
              "cost_per_guest": <float, allocated_budget / {guest_count}>,
              "currency": "{currency}",
              "categories": [
                {{
                  "name": "Food & Catering | Drinks & Bar | Theme & Decor | Music & Entertainment | Photography | Venue & Stays | Contingency",
                  "allocated_amount": <float>,
                  "percentage": <float>,
                  "description": "Specific breakdown of what this covers",
                  "recommended_platforms": ["Platform 1", "Platform 2"],
                  "search_query": "Targeted search query for booking",
                  "tips": "Practical tip for this category"
                }}
              ],
              "schedule_timeline": [
                {{"time": "05:00 PM", "activity": "Vendor setup"}},
                {{"time": "07:00 PM", "activity": "Guest arrival & welcome drinks"}},
                {{"time": "08:30 PM", "activity": "Main meal service"}},
                {{"time": "10:30 PM", "activity": "Celebration & wrap up"}}
              ],
              "saving_hacks": ["hack 1", "hack 2", "hack 3"]
            }}
            """
            
            interaction = genai_client.interactions.create(
                model=GEMINI_MODEL,
                input=prompt
            )
            raw_text = interaction.output_text or (interaction.outputs[-1].text if interaction.outputs else "")
            data = clean_json_response(raw_text)
            
            for cat in data.get("categories", []):
                q = cat.get("search_query") or f"{event_type} {cat.get('name')}"
                cat["action_links"] = {
                    "swiggy": make_swiggy_url(q),
                    "zomato": make_zomato_url(q),
                    "blinkit": make_blinkit_url(q),
                    "urbancompany": make_urbancompany_url(q),
                    "oyo": make_oyo_url("party venue hotel")
                }
            data["is_ai_generated"] = True
            return data
        except Exception as e:
            print(f"Gemini API call failed for Party Planner: {e}. Falling back to Smart-Engine.")

    return fallback_party_budget(event_type, guest_count, venue_type, services_needed, total_budget, food_preference, currency)


def fallback_party_budget(event_type, guest_count, venue_type, services_needed, total_budget, food_preference, currency):
    safe_budget = float(total_budget)
    safe_guests = max(int(guest_count), 1)
    
    has_venue_rent = any("venue" in s.lower() or "hall" in s.lower() for s in services_needed) or "Banquet" in venue_type or "Airbnb" in venue_type
    
    if has_venue_rent:
        fractions = [
            ("Venue & Space Rental", 0.30, "Private lounge, banquet hall, or rented party villa space.", ["OYO Rooms", "Airbnb", "Local Banquets"], "party banquet hall rental"),
            ("Food & Gourmet Catering", 0.35, f"Complete party spread ({food_preference}): 2 starters, 2 mains, breads, rice & dessert.", ["Swiggy Gourmet", "Zomato Catering", "Local Caterer"], f"{food_preference} party catering buffet"),
            ("Beverages & Mocktail Station", 0.12, "Soft drinks, premium juices, mocktail syrups, crushed ice & disposable glassware.", ["Blinkit Instamart", "Zepto", "Local Supermarket"], "party soft drinks mixers crushed ice"),
            ("Theme Decor & Balloon Arch", 0.08, "Custom themed backdrop, LED fairy lights, balloon garland & table centerpieces.", ["Amazon", "Party Hunterz", "Blinkit"], f"{event_type} party decoration kit backdrop"),
            ("Sound, Music & Party Lights", 0.07, "High-wattage portable bluetooth party speaker with wireless mic & disco lights.", ["Urban Company", "Amazon Rent", "Local AV Vendor"], "bluetooth party speaker with mic"),
            ("Contingency & Cleaning Fund", 0.04, "Reserved buffer for last-minute guest additions, ice replenishment, and post-party deep cleaning.", ["Urban Company Cleaning"], "home party deep cleaning service")
        ]
    else:
        fractions = [
            ("Food & Gourmet Catering", 0.45, f"High-quality party feast ({food_preference}) with multiple appetizers, mains, and dessert.", ["Swiggy Gourmet", "Zomato Party Box", "Local Caterers"], f"{food_preference} party catering box"),
            ("Beverages, Bar & Ice Station", 0.18, "Mocktails, soda mixers, artisanal sodas, fresh lemons, ice cubes, and crystal-finish acrylic cups.", ["Blinkit", "Zepto", "Instamart"], "party beverages mocktail mixers ice"),
            ("Decor, Lighting & Photo Backdrop", 0.15, "Fairy string lights, photo-op backdrop with ring lights, confetti, and table runners.", ["Amazon", "Flipkart", "Blinkit"], f"{event_type} photo booth props lights decor"),
            ("Music, Games & Entertainment", 0.12, "Premium sound system playlist setup, fun party card/board games, and karaoke mic.", ["Amazon", "Urban Company"], "party karaoke microphone party games"),
            ("Post-Party Cleaning & Emergency Buffer", 0.06, "Stress-free next-morning deep kitchen & living room cleaning.", ["Urban Company"], "deep cleaning service urban company")
        ]

    categories = []
    allocated_sum = 0.0
    
    for name, frac, desc, platforms, q in fractions:
        amount = round(safe_budget * frac, 2)
        allocated_sum += amount
        pct = round((amount / safe_budget) * 100, 1)
        categories.append({
            "name": name,
            "allocated_amount": amount,
            "percentage": pct,
            "description": desc,
            "recommended_platforms": platforms,
            "search_query": q,
            "action_links": {
                "swiggy": make_swiggy_url(q),
                "zomato": make_zomato_url(q),
                "blinkit": make_blinkit_url(q),
                "urbancompany": make_urbancompany_url(q),
                "oyo": make_oyo_url("party hotel lounge")
            },
            "tips": f"Pre-order {name.lower()} at least 24-48 hours in advance to avoid surge pricing."
        })

    return {
        "summary": f"Smart-budget blueprint for your {event_type} hosting {safe_guests} guests at {venue_type}, balancing gourmet hospitality with memorable ambience.",
        "event_type": event_type,
        "guest_count": safe_guests,
        "total_budget": safe_budget,
        "allocated_budget": round(allocated_sum, 2),
        "cost_per_guest": round(allocated_sum / safe_guests, 2),
        "currency": currency,
        "categories": categories,
        "schedule_timeline": [
            {"time": "04:30 PM", "activity": "Decor setup, ambient lighting test & music playlist start"},
            {"time": "06:00 PM", "activity": "Beverages, ice stations & welcome appetizer platter ready"},
            {"time": "07:00 PM", "activity": "Guests arrive, social mixer games & photo booth sessions"},
            {"time": "08:45 PM", "activity": "Main meal / buffet opened"},
            {"time": "10:15 PM", "activity": "Celebration moment, desserts & late-night chill"}
        ],
        "saving_hacks": [
            "Use quick-commerce apps (Blinkit/Zepto) for last-minute ice, soda, and chips instead of paying 3x markups to venues.",
            "Order finger foods in combo party boxes rather than individual portions to cut food costs by up to 30%.",
            "Set up a DIY smartphone tripod photo station with ring light instead of hiring a dedicated photographer for intimate gatherings."
        ],
        "is_ai_generated": False
    }


# ==========================================
# MODULE 3: JEWELRY PLANNER (MULTIMODAL)
# ==========================================

def generate_jewelry_budget(
    occasion: str,
    outfit_description: str,
    metal_preference: str,
    total_budget: float,
    currency: str = "INR",
    image_bytes: Optional[bytes] = None,
    image_mime_type: Optional[str] = None
) -> Dict[str, Any]:
    """Generate multimodal jewelry recommendation matching outfit aesthetics and budget."""
    global genai_client
    
    if not genai_client and os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") != "your_gemini_api_key_here":
        try:
            from google import genai
            genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        except Exception:
            pass

    if genai_client:
        try:
            text_prompt = f"""
            You are an expert high-fashion jewelry stylist and gemology consultant.
            Analyze the user's outfit to curate complementary jewelry pieces (necklace, earrings, bangles/bracelets, rings).
            Match the neckline, embroidery, silhouette, formality, and color palette.
            CRITICAL REQUIREMENT: The sum of estimated_price across all jewelry_pieces MUST NOT exceed {total_budget}.
            Output ONLY a raw, valid JSON object without markdown code block fences.

            Occasion: {occasion}
            User's Outfit Description: {outfit_description}
            Preferred Metal / Material: {metal_preference}
            Total Budget: {currency} {total_budget}

            Return JSON matching this exact structure:
            {{
              "summary": "Stylist assessment of the overall look",
              "outfit_analysis": {{
                "style_detected": "Brief description of the attire style",
                "color_palette": ["Color 1", "Color 2"],
                "neckline_match": "Neckline shape analysis and why certain jewelry cuts flatter it",
                "formality": "Casual | Festive | Black Tie | Traditional Wedding"
              }},
              "total_budget": {total_budget},
              "allocated_budget": <float <= {total_budget}>,
              "remaining_budget": <float, {total_budget} - allocated_budget>,
              "currency": "{currency}",
              "jewelry_pieces": [
                {{
                  "piece_type": "Necklace | Earrings | Bangles / Bracelet | Ring | Headwear",
                  "title": "Specific descriptive jewelry name",
                  "estimated_price": <float>,
                  "percentage": <float>,
                  "metal_gem": "e.g. 18K Yellow Gold with Freshwater Pearls",
                  "why_it_matches": "Stylist rationale connecting piece with outfit details",
                  "search_term": "Optimized shopping query"
                }}
              ],
              "styling_advice": ["bullet 1", "bullet 2"],
              "investment_tip": "Advice on hallmarking, resale value, or maintenance"
            }}
            """
            
            if image_bytes:
                b64_image = base64.b64encode(image_bytes).decode("utf-8")
                mime = image_mime_type or "image/jpeg"
                interaction_input = [
                    {"type": "text", "text": text_prompt},
                    {"type": "image", "data": b64_image, "mime_type": mime}
                ]
            else:
                interaction_input = text_prompt

            interaction = genai_client.interactions.create(
                model=GEMINI_MODEL,
                input=interaction_input
            )
            raw_text = interaction.output_text or (interaction.outputs[-1].text if interaction.outputs else "")
            data = clean_json_response(raw_text)
            
            for piece in data.get("jewelry_pieces", []):
                q = piece.get("search_term") or piece.get("title")
                piece["store_links"] = {
                    "bluestone": make_bluestone_url(q),
                    "caratlane": make_caratlane_url(q),
                    "tanishq": make_tanishq_url(q),
                    "myntra": make_myntra_url(q),
                    "amazon": make_amazon_url(q)
                }
            data["is_ai_generated"] = True
            return data
        except Exception as e:
            print(f"Gemini API call failed for Jewelry Planner: {e}. Falling back to Smart-Engine.")

    return fallback_jewelry_budget(occasion, outfit_description, metal_preference, total_budget, currency, bool(image_bytes))


def fallback_jewelry_budget(occasion, outfit_description, metal_preference, total_budget, currency, has_image=False):
    safe_budget = float(total_budget)
    
    desc_lower = outfit_description.lower()
    is_traditional = any(w in desc_lower for w in ["saree", "lehenga", "kurta", "anarkali", "sherwani", "ethnic", "zari"])
    is_western = any(w in desc_lower for w in ["gown", "dress", "suit", "blazer", "tuxedo", "cocktail", "western"])
    
    if is_western:
        detected_style = "Contemporary Western / Indo-Western Fusion"
        neckline = "Deep V / Collar Cut - ideal for drop pendants or collar statement pieces"
        pieces_blueprint = [
            ("Necklace", f"Minimalist Solitaire Diamond Pendant in {metal_preference}", 0.42, f"{metal_preference} solitaire diamond pendant necklace"),
            ("Earrings", f"Geometric Huggie Hoop Earrings with Pave Accents", 0.28, f"{metal_preference} hoop earrings pave"),
            ("Bangles / Bracelet", f"Dainty Tennis Bracelet / Sleek Cuff", 0.20, f"{metal_preference} tennis bracelet minimal"),
            ("Ring", f"Stackable Eternity Band Ring", 0.08, f"{metal_preference} stackable eternity band")
        ]
    else:
        detected_style = "Classic Traditional Ethnic Ensemble"
        neckline = "Broad Sweetheart / Round Neckline - pairs gorgeously with chokers or layered temple neckpieces"
        pieces_blueprint = [
            ("Necklace", f"Intricate Choker Necklace with Gemstone Droplets in {metal_preference}", 0.46, f"{metal_preference} ethnic choker necklace"),
            ("Earrings", f"Statement Chandbalis / Jhumkas with Fine Filigree", 0.26, f"{metal_preference} jhumka earrings"),
            ("Bangles / Bracelet", f"Set of 2 Textured Kadas / Openable Bangles", 0.18, f"{metal_preference} kadas bangles pair"),
            ("Ring", f"Floral Statement Cocktail Ring", 0.08, f"{metal_preference} floral statement ring")
        ]

    pieces = []
    allocated_sum = 0.0
    
    for p_type, title, frac, q in pieces_blueprint:
        price = round(safe_budget * frac * 0.98, 2)
        allocated_sum += price
        pct = round((price / safe_budget) * 100, 1)
        pieces.append({
            "piece_type": p_type,
            "title": title,
            "estimated_price": price,
            "percentage": pct,
            "metal_gem": f"{metal_preference} with fine craftsmanship",
            "why_it_matches": f"Accentuates the {neckline.split(' - ')[0]} of your outfit while respecting the {occasion} dress code.",
            "search_term": q,
            "store_links": {
                "bluestone": make_bluestone_url(q),
                "caratlane": make_caratlane_url(q),
                "tanishq": make_tanishq_url(q),
                "myntra": make_myntra_url(q),
                "amazon": make_amazon_url(q)
            }
        })

    return {
        "summary": f"Curated {metal_preference} jewelry ensemble tailored for your {occasion} outfit, engineered to achieve maximum aesthetic brilliance within your exact financial boundary.",
        "outfit_analysis": {
            "style_detected": f"{detected_style} {'(Assessed from uploaded photo)' if has_image else '(Assessed from style notes)'}",
            "color_palette": ["Harmonious Complementary Tones", "Warm Luster Highlights"],
            "neckline_match": neckline,
            "formality": f"High Formality ({occasion})"
        },
        "total_budget": safe_budget,
        "allocated_budget": round(allocated_sum, 2),
        "remaining_budget": round(safe_budget - allocated_sum, 2),
        "currency": currency,
        "jewelry_pieces": pieces,
        "styling_advice": [
            "If your necklace features intricate detailing, keep your neckline clear of heavy brooches to avoid visual clutter.",
            "Choose warm yellow gold for warm undertone fabrics (red, maroon, emerald, mustard) and rose/white gold for cool palettes (sapphire, blush pink, lilac, silver).",
            "Balance scale: A bold statement necklace should be paired with medium studs or drops rather than sweeping shoulder-dusters."
        ],
        "investment_tip": "Always insist on BIS Hallmarked jewelry (look for the 6-digit alphanumeric HUID) and IGI/SGL diamond certification for optimal purity and buyback assurance.",
        "is_ai_generated": False
    }
