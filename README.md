# 🧠 Cortex
**A living 3D brain that visualizes your CS knowledge.**

Upload GitHub repos, PDFs, or text, Cortex scores your skills across **51 categories using Google Gemini**, maps them onto a **glowing interactive brain**, and offers **AI-powered learning advice** through a built-in chatbot.

Built for **HackCanada 2026**.

---

# ✨ Features

### 🧠 3D Knowledge Brain
Interactive **Three.js neural network** with **9 glowing regions** representing skill groups. Regions light up as you upload evidence of your skills.

### 📥 Multi-Source Ingestion
Upload **GitHub repos (auto-fetched via API), PDFs, or plain text descriptions**.

### 🤖 AI Scoring
**Google Gemini** analyzes your content and scores **51 technical categories (0–1)** with keyword fallback when the API is unavailable.

### 📊 Profile Accumulation
Scores merge over time using **EMA blending** — more uploads = more accurate profile.  
Strong sources (**GitHub**) carry more weight than text prompts.

### 💬 Chatbot Advisor
Ask **Lumas (the AI advisor)** for **SWOT analyses, learning paths, project suggestions, and skill-gap insights** — all grounded in your actual profile data.

### 🏆 Proficiency Tiers
Scores translate into meaningful labels:

**Novice → Beginner → Intermediate → Proficient → Advanced → Expert**

---

# 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Next.js Frontend                      │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │BrainScene│  │ UploadPanel  │  │     ChatBot       │  │
│  │(Three.js)│  │(GitHub/PDF)  │  │  (Gemini-powered) │  │
│  └────┬─────┘  └──────┬───────┘  └────────┬──────────┘  │
│       │               │                   │              │
│  ┌────┴───────────────┴───────────────────┴──────────┐  │
│  │        ProfileContext + categoryMapping            │
│  └────────────────────────┬───────────────────────────┘
└───────────────────────────┼─────────────────────────────
                            │ REST API
┌───────────────────────────┼─────────────────────────────┐
│                    FastAPI Backend                      │
│  ┌────────────────────────┴─────────────────────────┐   │
│  │                 /api router                      │   │
│  └──┬──────────────────────────────────────────────┬┘   │
│     │                                              │    │
│  ┌──┴──────────────┐                    ┌──────────┴──┐ │
│  │ Profile Scoring │                    │   Chatbot   │ │
│  │  ├ orchestrator │                    │  ├ service  │ │
│  │  ├ gemini_scorer│                    │  ├ router   │ │
│  │  ├ profile_mgr  │                    │  └ models   │ │
│  │  └ categories   │                    └─────────────┘ │
│  └──┬──────────────┘                                   │
│     │                                                  │
│  ┌──┴──────────────┐                                   │
│  │    Ingestion     │                                  │
│  │  ├ github_proc   │                                  │
│  │  ├ pdf_proc      │                                  │
│  │  └ text_proc     │                                  │
│  └─────────────────┘                                   │
└────────────────────────────────────────────────────────┘
```

---

# 🧩 Tech Stack

| Layer | Technology |
|------|------------|
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS |
| 3D Visualization | Three.js, @react-three/fiber, @react-three/drei |
| Backend | Python 3.9+, FastAPI, Pydantic |
| AI | Google Gemini (gemini-2.5-flash) via google-genai SDK |
| Ingestion | GitHub REST API, PDF parsing, plain text |

---

# 📂 Project Structure

```
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── chatbot/
│   │   ├── chat_service.py      # Gemini-powered conversational advisor
│   │   ├── router.py            # POST /chat/{user_id}, GET /chat/{user_id}/insights
│   │   └── models.py            # ChatRequest, ChatResponse, InsightsResponse
│   ├── profile_scoring/
│   │   ├── categories.py        # 51 categories across 9 groups
│   │   ├── gemini_scorer.py     # Content → category scores via Gemini
│   │   ├── profile_manager.py   # EMA merge, in-memory storage, history
│   │   ├── orchestrator.py      # Single entry-point: fetch → score → merge
│   │   ├── router.py            # Profile CRUD + scoring endpoints
│   │   └── models.py            # UserProfile, GeminiScoringResult, etc.
│   └── ingestion/
│       ├── github_processor.py  # Fetch README, file tree, languages via GitHub API
│       ├── pdf_processor.py     # Extract text from PDFs
│       └── text_processor.py    # Plain text processing
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # Main page with brain + upload panel + chatbot
│   │   └── layout.tsx           # Root layout with ProfileProvider
│   ├── components/
│   │   ├── BrainScene.tsx       # Three.js canvas with lighting + controls
│   │   ├── LowPolyBrain.tsx     # Node/edge rendering, BFS animation, glow
│   │   ├── UploadPanel.tsx      # GitHub URL / PDF upload form
│   │   └── ChatBot.tsx          # Chat UI panel
│   ├── context/
│   │   └── ProfileContext.tsx   # Global profile state + API calls
│   ├── lib/
│   │   ├── api.ts               # Backend API client
│   │   └── categoryMapping.ts   # 51 categories → 9 brain regions
│   └── public/
│       └── brain_regions.json   # 1982 nodes, 5630 edges, 9 region segments
│
└── .env                         # API keys (not committed)
```

---

# 🚀 Getting Started

## Prerequisites

- Python **3.9+**
- Node.js **18+**
- A **Google Gemini API key**

---
## 1️⃣ Clone & install

```bash
git clone https://github.com/Devansh015/HackCanada.git
cd HackCanada
```

## 2️⃣ Backend setup

```bash
cd backend
pip3 install -r requirements.txt
```

## 3️⃣ Frontend setup

```bash
cd frontend
npm install
```

---

## 4️⃣ Environment variables

Create a `.env` file in the project root:

```env
GOOGLE_CLOUD_CONSOLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8080
```

---

## 5️⃣ Run

### Backend (from project root)

```bash
python3 -m uvicorn backend.main:app --reload --port 8080
```

You can also run it from inside `backend/`:

```bash
python3 -m uvicorn main:app --reload --port 8080
```

### Frontend (from `frontend/`)

```bash
npm run dev
```

Open:

```
http://localhost:3000
```

---

# 🔌 API Endpoints

## Profile Scoring

| Method | Endpoint | Description |
|------|------|------|
| POST | `/api/profile/{user_id}/init` | Create blank profile |
| GET | `/api/profile/{user_id}` | Get current scores |
| GET | `/api/profile/{user_id}/top?n=5` | Top-N categories |
| POST | `/api/profile/{user_id}/score-upload` | Score content & merge |
| GET | `/api/profile/{user_id}/history` | Upload history |
| POST | `/api/profile/{user_id}/reset` | Reset to zeros |

---

## Chatbot

| Method | Endpoint | Description |
|------|------|------|
| POST | `/api/chat/{user_id}` | Send message, get AI reply |
| GET | `/api/chat/{user_id}/insights` | Auto-generated profile insights |

### Chat Request

```json
{
  "message": "Give me a SWOT analysis",
  "conversation_history": []
}
```

### Chat Response

```json
{
  "reply": "Here's your analysis...",
  "suggestions": ["What should I learn next?"]
}
```

---

# 🧠 Skill Categories (51)

| Region | Categories |
|------|------|
| Fundamentals (4) | Variables, Functions, Control Flow, Recursion |
| OOP (9) | OOP, Classes, Objects, Inheritance, Polymorphism, Encapsulation, Abstraction, Methods, Constructors |
| Data Structures (8) | Arrays, Linked Lists, Stacks, Queues, Trees, Graphs, Hash Tables |
| Algorithms (6) | Sorting, Searching, Dynamic Programming, Time Complexity, Space Complexity |
| Systems (8) | Databases, SQL, Indexing, APIs, Operating Systems, Memory Management, Concurrency, Networking |
| Frontend (5) | HTML/CSS, JavaScript/TypeScript, React, Responsive Design, UI/UX |
| Dev Practices (5) | Git, Testing, CI/CD, Docker, Cloud Infrastructure |
| Product (3) | Documentation, Project Management, System Design |
| Hackathon (3) | Rapid Prototyping, Third-party Integrations, Creative Problem Solving |

---

# 📊 Proficiency Tiers

| Score | Tier | Meaning |
|------|------|------|
| 0.00 | Unassessed | No evidence uploaded |
| 0.01 – 0.15 | Novice | Minimal exposure |
| 0.16 – 0.35 | Beginner | Basic familiarity |
| 0.36 – 0.55 | Intermediate | Working knowledge |
| 0.56 – 0.75 | Proficient | Solid competence |
| 0.76 – 0.90 | Advanced | Strong expertise |
| 0.91 – 1.00 | Expert | Exceptional mastery |

---

# 👥 Team

Built by **Devansh Jain, Yash Soni, Dharm Patel and Aryan Kakkar** for **HackCanada 2026**.
