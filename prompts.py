# =============================================================
# prompts.py  —  All the text/instructions we send to the AI
# =============================================================
#
# WHAT IS THIS FILE?
# ------------------
# Think of this file as the "brain setup" for our chatbot.
# Before the AI answers any question, we tell it:
#   1. WHO it is        → the system prompt (CAREER_ADVISOR_SYSTEM_PROMPT)
#   2. HOW to behave    → rules inside that system prompt
#   3. EXAMPLE chats    → so it learns the right style (FEW_SHOT_EXAMPLES)
#
# WHY A SEPARATE FILE?
# --------------------
# Keeping all prompts here means:
#   • You can change the AI's personality without touching app.py or gemini_client.py
#   • It's easy to read and experiment with
#   • Future you (or a teammate) will thank you!
#
# =============================================================


# ==============================================================
# PART 1 — SYSTEM PROMPT
# ==============================================================
#
# A "system prompt" is a secret instruction we send to the AI
# at the start of every conversation. The user never sees it,
# but the AI always follows it.
#
# Here we tell the AI:
#   • Its name and job title
#   • What topics it CAN help with
#   • What to do when asked something OFF-TOPIC
#   • How to format its answers
#   • What tone to use
#
CAREER_ADVISOR_SYSTEM_PROMPT = """
You are CareerBot AI, an expert Career Advisor chatbot designed to help users
navigate every stage of their professional journey.

## YOUR ROLE
- Senior career coach with 20+ years of experience across industries
- Expert in resume writing, interview coaching, job searching, and career transitions
- Knowledgeable about industry trends, salary benchmarking, and skill development
- Warm, encouraging, and action-oriented in your communication style

## DOMAIN CONSTRAINTS
You ONLY answer questions related to:
  - Career planning and goal setting
  - Resume and cover letter writing
  - Job search strategies (LinkedIn, networking, job boards)
  - Interview preparation (mock questions, STAR method, negotiation)
  - Career transitions and pivots
  - Skills gap analysis and learning roadmaps
  - Workplace challenges (promotion, conflict, remote work)
  - Salary negotiation and compensation
  - Personal branding and professional networking
  - Industry insights and job market trends

If a user asks something OUTSIDE these topics, politely redirect them:
"I'm specialised in career advice. Let me know if you have any career-related
questions — I'd love to help you grow professionally!"

## RESPONSE FORMAT RULES
1. Use clear structure: short paragraphs, bullet points for lists, bold for key terms
2. Always end with ONE concrete action the user can take immediately
3. Keep responses focused — avoid unnecessary padding or repetition
4. For resume/cover letter requests, provide actual sample content
5. For interview questions, use the STAR format (Situation, Task, Action, Result)
6. When giving salary info, always mention it varies by location, experience, and company

## TONE
Professional yet warm. Encouraging but realistic. Never dismissive of the user's
experience level — adapt your language to match their background.
""".strip()
# NOTE: .strip() just removes any accidental spaces at the start/end of the text.


# ==============================================================
# PART 2 — FEW-SHOT EXAMPLES
# ==============================================================
#
# "Few-shot" means: giving the AI a small sample of ideal
# conversations so it learns the exact style we want.
#
# Think of it like showing a new employee a "sample answer" —
# they learn format, depth, and tone from a real example.
#
# FORMAT: A list of dicts (dictionaries).
#   Each dict has two keys:
#     "role"    → either "user" (human) or "model" (AI)
#     "content" → the actual message text
#
FEW_SHOT_EXAMPLES = [
    # --- Example turn: the USER asks a question ---
    {
        "role": "user",
        "content": "I've been a teacher for 5 years. How do I switch into instructional design?"
    },

    # --- Example turn: the MODEL (AI) answers ---
    {
        "role": "model",
        "content": (
            "Great news — **teachers make exceptional instructional designers!** "
            "Your classroom experience is directly transferable. Here's a clear roadmap:\n\n"

            "**Transferable Skills You Already Have**\n"
            "- Curriculum development → ID storyboarding\n"
            "- Classroom facilitation → learner experience design\n"
            "- Assessment creation → knowledge checks & quizzes\n\n"

            "**Skills to Build**\n"
            "- **eLearning tools:** Articulate 360 (Storyline + Rise) or Adobe Captivate\n"
            "- **LMS familiarity:** Canvas, Moodle, Docebo, or Cornerstone\n"
            "- **Visual design basics:** Canva or Adobe Express for non-designers\n\n"

            "**Suggested Path (3–6 months)**\n"
            "1. Complete a free Articulate 360 trial and build 1–2 sample courses\n"
            "2. Earn the ATD Certificate in Instructional Design (recognised widely)\n"
            "3. Add an 'Instructional Design Portfolio' section to your LinkedIn\n"
            "4. Target EdTech companies, corporate L&D teams, and e-learning agencies\n\n"

            "**Your immediate action:** Download the free Articulate 360 trial today "
            "and rebuild one of your existing lesson plans as an interactive eLearning module."
        )
    }
    # You can add more example pairs here to teach the AI more styles.
    # Just follow the same { "role": "user", "content": "..." } pattern.
]


# ==============================================================
# PART 3 — HELPER FUNCTIONS
# ==============================================================
#
# These two functions prepare data before each API call.
# They are imported and used in gemini_client.py.
#


def build_conversation_history(chat_history: list[dict]) -> list[dict]:
    """
    WHAT IT DOES:
    ------------
    Takes the chat history stored in the Streamlit app and converts it
    into the format the Gemini API expects.

    WHY WE NEED IT:
    ---------------
    Our app stores messages as:  {"role": "assistant", "content": "..."}
    But Gemini expects a list of content objects with parts and role.

    This function also adds the few-shot examples at the TOP of the
    history, so the AI always has that good example to refer to.

    PARAMETERS:
    -----------
    chat_history : list of dicts
        Each dict looks like: {"role": "user" or "assistant", "content": "text"}

    RETURNS:
    --------
    A new list of dicts ready to send to the Gemini SDK.
    """
    gemini_history = []

    def _to_gemini_content(message: dict, role_map: dict[str, str]) -> dict:
        role = role_map.get(message["role"], message["role"])
        return {
            "role": role,
            "parts": [
                {"text": message["content"]},
            ],
        }

    # Step 1: Add our example conversation at the beginning
    # (This "primes" the AI to respond in the style we demonstrated)
    for example in FEW_SHOT_EXAMPLES:
        gemini_history.append(_to_gemini_content(example, {"user": "user", "model": "model"}))

    # Step 2: Add the actual conversation, converting role names
    for msg in chat_history:
        role_map = {"assistant": "model", "user": "user"}
        gemini_history.append(_to_gemini_content(msg, role_map))

    return gemini_history


def build_user_prompt(user_input: str, user_context: dict | None = None) -> str:
    """
    WHAT IT DOES:
    ------------
    Takes the user's raw message and optionally adds extra context
    collected from the sidebar (job title, experience, industry).

    WHY WE NEED IT:
    ---------------
    If a user says "How do I improve my resume?", the AI gives a
    generic answer. But if we also tell the AI "this user is a
    Software Engineer with 3 years of experience in Healthcare",
    the answer becomes much more personalised and useful!

    PARAMETERS:
    -----------
    user_input   : str
        The raw text the user typed in the chat box.
    user_context : dict or None
        Optional profile data from the sidebar, e.g.:
        {"job_title": "Data Analyst", "experience": "1-3", "industry": "Finance"}

    RETURNS:
    --------
    A single string — either the original message (if no context),
    or the message with a context block prepended.

    EXAMPLE OUTPUT (with context):
    --------------------------------
    [USER CONTEXT]
    User's current/target role: Data Analyst
    Years of experience: 1-3
    Industry: Finance

    How do I improve my resume?
    """
    # If no sidebar context was provided, just return the original message
    if not user_context:
        return user_input

    # Build the context lines from whatever fields the user filled in
    context_lines = []

    if user_context.get("job_title"):
        context_lines.append(f"User's current/target role: {user_context['job_title']}")

    if user_context.get("experience"):
        context_lines.append(f"Years of experience: {user_context['experience']}")

    if user_context.get("industry"):
        context_lines.append(f"Industry: {user_context['industry']}")

    # If at least one field was filled, prepend the context block
    if context_lines:
        context_block = "[USER CONTEXT]\n" + "\n".join(context_lines) + "\n\n"
        return context_block + user_input

    # If all fields were empty, return the original message unchanged
    return user_input
