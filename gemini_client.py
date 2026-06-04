# =============================================================
# gemini_client.py  —  Modular Gemini API integration layer
# =============================================================
"""
All Gemini API logic is encapsulated here.
The UI (app.py) never imports google.genai directly.
Uses the current google-genai SDK (v1.0+).
"""

import os
import logging
import time
from dataclasses import dataclass
from typing import Optional

from google import genai
from google.genai import types

from prompts import CAREER_ADVISOR_SYSTEM_PROMPT, build_conversation_history, build_user_prompt

# ------------------------------------------------------------------
# LOGGING
# ------------------------------------------------------------------
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("gemini_client")


# ------------------------------------------------------------------
# DATA CLASSES
# ------------------------------------------------------------------
@dataclass
class ChatResponse:
    """Structured response returned to the UI layer."""
    text: str
    success: bool
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    error_message: str = ""
    model_used: str = ""


@dataclass
class TokenUsageTracker:
    """Accumulates token usage across the session."""
    total_input: int = 0
    total_output: int = 0
    call_count: int = 0

    def update(self, input_tokens: int, output_tokens: int):
        self.total_input  += input_tokens
        self.total_output += output_tokens
        self.call_count   += 1

    @property
    def total_tokens(self) -> int:
        return self.total_input + self.total_output


# ------------------------------------------------------------------
# GENERATION CONFIG  (token optimisation)
# ------------------------------------------------------------------
GENERATION_CONFIG = types.GenerateContentConfig(
    system_instruction=CAREER_ADVISOR_SYSTEM_PROMPT,
    temperature=0.7,
    top_p=0.90,
    top_k=40,
    max_output_tokens=1024,
    candidate_count=1,
    safety_settings=[
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
    ],
)


# ------------------------------------------------------------------
# GEMINI CLIENT CLASS
# ------------------------------------------------------------------
class GeminiClient:
    """
    Production-grade wrapper around the google-genai SDK.
    Handles: initialisation, structured requests, error handling,
    fallback responses, and token usage logging.
    """

    MODEL_NAME = "gemini-flash-lite-latest"

    def __init__(self):
        self._initialised = False
        self._client: Optional[genai.Client] = None
        self.token_tracker = TokenUsageTracker()
        self._initialise()

    # ---- Initialisation ------------------------------------------
    def _initialise(self):
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key or api_key == "your_gemini_api_key_here":
            logger.error("GEMINI_API_KEY is not set or is still a placeholder.")
            self._initialised = False
            return

        try:
            self._client = genai.Client(api_key=api_key)
            self._initialised = True
            logger.info("Gemini client initialised with model: %s", self.MODEL_NAME)
        except Exception as exc:
            logger.exception("Failed to initialise Gemini client: %s", exc)
            self._initialised = False

    @property
    def is_ready(self) -> bool:
        return self._initialised and self._client is not None

    # ---- Core chat method ----------------------------------------
    def send_message(
        self,
        user_input: str,
        chat_history: list[dict],
        user_context: dict | None = None,
    ) -> "ChatResponse":
        """
        Sends a user message to Gemini and returns a ChatResponse.

        Parameters
        ----------
        user_input   : Raw text typed by the user.
        chat_history : Full session history (list of {role, content} dicts).
        user_context : Optional sidebar metadata (role, industry, etc.).
        """
        if not self.is_ready:
            return ChatResponse(
                text=self._not_ready_message(),
                success=False,
                error_message="API client not initialised.",
            )

        start_time = time.perf_counter()

        try:
            # 1. Build the final prompt and Gemini-format history
            final_prompt = build_user_prompt(user_input, user_context)
            history      = build_conversation_history(chat_history[:-1])  # exclude current turn

            logger.info(
                "API call #%d | history_turns=%d | prompt_chars=%d",
                self.token_tracker.call_count + 1,
                len(history),
                len(final_prompt),
            )

            # 2. Create a chat session with history + system prompt baked in
            chat_session = self._client.chats.create(
                model=self.MODEL_NAME,
                config=GENERATION_CONFIG,
                history=history,
            )

            # 3. Send the message
            response = chat_session.send_message(final_prompt)

            # 4. Extract text
            response_text = response.text.strip()

            # 5. Token usage
            usage         = response.usage_metadata
            input_tokens  = getattr(usage, "prompt_token_count",     0) or 0
            output_tokens = getattr(usage, "candidates_token_count", 0) or 0
            latency_ms    = (time.perf_counter() - start_time) * 1000

            self.token_tracker.update(input_tokens, output_tokens)

            logger.info(
                "Response OK | tokens_in=%d tokens_out=%d latency=%.0fms",
                input_tokens, output_tokens, latency_ms,
            )

            return ChatResponse(
                text=response_text,
                success=True,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                model_used=self.MODEL_NAME,
            )

        except Exception as exc:
            latency_ms    = (time.perf_counter() - start_time) * 1000
            error_str     = str(exc)
            logger.exception("API error after %.0fms: %s", latency_ms, error_str)

            # Friendly fallback based on error type
            if "blocked" in error_str.lower() or "safety" in error_str.lower():
                friendly = (
                    "I wasn't able to process that request due to content guidelines. "
                    "Could you rephrase your question? I'm here to help with career advice!"
                )
            elif "api_key" in error_str.lower() or "401" in error_str or "403" in error_str:
                friendly = (
                    "⚠️ **Invalid API Key.** Please check your Gemini API key in the sidebar "
                    "or your `.env` file and try again."
                )
            elif "quota" in error_str.lower() or "429" in error_str:
                friendly = (
                    "⚠️ **Rate limit reached.** You've hit the Gemini free tier limit. "
                    "Please wait a moment and try again, or check your quota at "
                    "[aistudio.google.com](https://aistudio.google.com)."
                )
            else:
                friendly = self._fallback_message()

            return ChatResponse(
                text=friendly,
                success=False,
                error_message=error_str,
                latency_ms=latency_ms,
            )

    # ---- Static helpers ------------------------------------------
    @staticmethod
    def _not_ready_message() -> str:
        return (
            "⚠️ **API Key Required**\n\n"
            "The chatbot isn't connected yet. Please:\n"
            "1. Paste your Gemini API key in the **sidebar** on the left\n"
            "2. Or add it to your `.env` file as `GEMINI_API_KEY=AIza...`\n"
            "3. Get a **free** key at [aistudio.google.com](https://aistudio.google.com/app/apikey)\n\n"
            "Once connected, I'm ready to help with your career!"
        )

    @staticmethod
    def _fallback_message() -> str:
        return (
            "I'm experiencing a temporary issue connecting to my AI backend. "
            "Please try again in a moment. If the problem persists, check your API key "
            "and internet connection."
        )
