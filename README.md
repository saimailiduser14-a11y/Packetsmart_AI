# PocketSmart AI 🛍️✨

**PocketSmart AI** is a GenAI-powered recommendation engine engineered to deliver budget-conscious, multi-platform shopping allocations and vendor routing across three primary domains:
1. **Home Interior Planner**: Room configurations, lighting, modular furniture, BLDC fans, with direct query links to Amazon.in, Flipkart, and IKEA.
2. **Party & Event Planner**: Event types, guest counts, fractional budgets across Swiggy, Zomato, Blinkit, and Urban Company, plus per-guest cost metrics and run-of-show timelines.
3. **Multimodal Jewelry Stylist**: Attire style and neckline pairing with optional outfit photo uploads analyzed via Google Gemini multimodal vision, mapping to BlueStone, CaratLane, and Tanishq.

Built with **FastAPI**, **Google Gemini** (`google-genai` SDK), **SQLite/Serverless persistence**, and designed specifically for **Vercel Serverless** deployment.

---

## 🏗️ Architecture & File Structure

```text
pocketsmart-ai/
├── api/
│   └── index.py             # Vercel Serverless Entrypoint Wrapper
├── static/
│   ├── uploads/             # Ephemeral / Permanent outfit image uploads
│   └── styles.css           # Glassmorphic modern responsive design system
├── templates/               # Jinja2 Dynamic HTML View Templates
│   ├── base.html            # Shared layout, navbar, modals & toast alerts
│   ├── dashboard.html       # User workspace, analytics KPIs & recent plans
│   ├── history.html         # Filterable archives & detailed plan modals
│   ├── home_planner.html    # Home interior procurement tool
│   ├── index.html           # Landing page & feature showcase
│   ├── jewelry_planner.html # Multimodal jewelry styling engine with dropzone
│   ├── login.html           # Secure sign-in form
│   ├── party_planner.html   # Event management & hospitality budget engine
│   └── register.html        # Account registration
├── app.py                   # FastAPI Routing, Route Guards & Core Logic
├── auth.py                  # PBKDF2-HMAC-SHA256 & JWT Cookie Sessions
├── database.py              # SQLite storage (handles /tmp on Vercel)
├── gemini_service.py        # Gemini Vision & E-commerce URL Generators
├── requirements.txt         # Serverless runtime dependencies
├── vercel.json              # Vercel route & build definitions
├── .env.example             # Configuration template
└── test_suite.py            # Automated QA & validation test suite
```

---

## ⚡ Quick Start (Local Development)

### 1. Configure Environment Secrets
Copy `.env.example` to `.env` and insert your Google AI Studio API key:
```bash
cp .env.example .env
```
Inside `.env`:
```ini
GEMINI_API_KEY=your_actual_google_ai_studio_key_here
GEMINI_MODEL=gemini-3.8-flash
SECRET_KEY=generate_a_secure_random_key_here_for_jwt
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```
*(Note: If `GEMINI_API_KEY` is not provided, PocketSmart AI gracefully activates its built-in Smart-Engine fallback to ensure zero downtime and uninterrupted local testing.)*

### 2. Run the FastAPI Application
Start the Uvicorn ASGI server:
```bash
uvicorn app:app --reload --port 8000
```
Open your browser at `http://127.0.0.1:8000`.

---

## 🧪 Automated Testing & Quality Assurance

Run the comprehensive QA test suite:
```bash
python test_suite.py
```
This tests:
* ✅ `/api/health` status and environment diagnostics
* ✅ All HTML view templates (`/`, `/home-planner`, `/party-planner`, `/jewelry-planner`, `/login`, `/register`)
* ✅ Unauthenticated route guard enforcement (`/dashboard` and `/history` redirect to `/login`)
* ✅ Full authentication lifecycle (registration, duplicate checks, login, JWT cookie generation)
* ✅ Mathematical budget enforcement: Line items sum $\le$ user-entered ceiling
* ✅ Multimodal image upload handling and PIL / bytes parsing
* ✅ History engine persistence and deletion

---

## 🚀 Deployment to Vercel

PocketSmart AI is pre-configured for Vercel's Serverless Python runtime.

### Step 1: Install Vercel CLI & Login
```bash
npm install -g vercel
vercel login
```

### Step 2: Deploy
From the project root:
```bash
vercel
```

### Step 3: Set Environment Variables on Vercel
In your Vercel Dashboard under **Settings > Environment Variables**, add:
* `GEMINI_API_KEY` = your Google AI Studio API key
* `SECRET_KEY` = your 32+ character JWT secret string
* `GEMINI_MODEL` = `gemini-3.8-flash` (or `gemini-2.5-flash`)

### Step 4: Promote to Production
```bash
vercel --prod
```

### Ephemeral Storage Handling
On Vercel, the file system is read-only except for `/tmp`. PocketSmart AI automatically switches:
* Database file: `/tmp/pocketsmart.db`
* Uploaded outfit images: `/tmp/uploads`
when `VERCEL=1` is detected in the environment.

---

## 🛡️ Security Features
* **PBKDF2-HMAC-SHA256**: Uses 100,000 rounds with cryptographically unique salts.
* **HTTP-Only JWT Cookies**: Eliminates XSS token theft while supporting Bearer headers for AJAX requests.
* **Zero Overspending Cap**: Enforces total allocations $\le$ user budget with an emergency safety cushion.
