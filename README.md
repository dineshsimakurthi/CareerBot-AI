# CareerBot AI — Google Gemini Chatbot

A production-ready **Career Advisor Chatbot** built with Streamlit + Google Gemini API.

---

## Project Structure

```
chatbot/
├── app.py              # Streamlit UI (entry point)
├── gemini_client.py    # Gemini API integration (modular, separated from UI)
├── prompts.py          # System prompts + few-shot CoT examples (configurable)
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
└── README.md
```

---

## Setup Instructions

### Step 1 — Get a Gemini API Key (Free)
1. Go to: https://aistudio.google.com/app/apikey
2. Click **Create API Key**
3. Copy the key (starts with `AIza...`)

### Step 2 — Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3 — Configure API Key

**Option A: Environment file (recommended)**
```bash
cp .env.example .env
# Edit .env and replace "your_gemini_api_key_here" with your actual key
```

**Option B: Sidebar input**
Just paste your key directly into the sidebar when the app is running.

### Step 4 — Run the App
```bash
streamlit run app.py
```

The app opens at: http://localhost:8501

---

## Features

| Feature | Details |
|---|---|
| **Domain** | Career Advisor (resume, interviews, job search, salary) |
| **Model** | Gemini 1.5 Flash (fast + cost-efficient) |
| **Prompt Engineering** | Few-shot CoT, role-based system prompt, domain constraints |
| **Security** | API key via env var, never hardcoded |
| **Error Handling** | Safety filter fallback, API error fallback, key validation |
| **Token Tracking** | Per-call and session totals shown in sidebar |
| **Logging** | Structured logs for every API call and error |
| **UI** | Chat bubbles, loading spinner, quick-topic chips, user profile sidebar |

---

## Technical Architecture

```
User Input (Streamlit UI)
        │
        ▼
   prompts.py
   build_user_prompt()      ← injects optional user context
   build_conversation_history() ← formats history for Gemini
        │
        ▼
  gemini_client.py
  GeminiClient.send_message()  ← API call, logging, error handling
        │
        ▼
  Google Gemini API  (gemini-1.5-flash)
  System Prompt: CAREER_ADVISOR_SYSTEM_PROMPT
        │
        ▼
   ChatResponse (dataclass)
   .text / .success / .input_tokens / .output_tokens / .latency_ms
        │
        ▼
  app.py — renders response in chat bubble, updates session state
```

---

## Prompt Engineering Design

The system prompt (`prompts.py`) defines:
- **Role**: Senior career coach with 20+ years experience
- **Domain constraints**: Only answers career-related questions
- **Output format rules**: Structured bullets, bold key terms, one action per response
- **Tone**: Professional, warm, encouraging

Three **few-shot examples** prime the model before the first user turn so response quality is consistent from message #1.

---


Streamlit Deploy Link :- https://careerbot-ai-8b7b4cmoatc6zxfuwektxh.streamlit.app
