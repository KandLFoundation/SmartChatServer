import os
import time
from collections import defaultdict, deque

from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

# ------------------- Flask App Setup -------------------
app = Flask(__name__)
CORS(app)

# ------------------- Environment Variables -------------------
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
BOT_NAME = os.environ.get("BOT_NAME", "KL Lexus")
MODEL_NAME = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set!")

client = Groq(api_key=GROQ_API_KEY)

# ------------------- Foundation Knowledge -------------------
SYSTEM_PROMPT = f"""You are {BOT_NAME}, the friendly virtual assistant for K&L Foundation,
a community non-profit based in Polokwane, Limpopo, South Africa.

Foundation facts (use these, don't invent extra ones):
- Mission: "Giving hope, one hand at a time." K&L Foundation supports vulnerable people
  in South Africa through food, clothing, blankets, sanitary pads, and digital/tech
  skills programs.
- Programs include: food and clothing distribution, blanket drives, sanitary pad
  donations, AI workshops, tech support, and web development skills training for youth.
- How to donate: items (food, clothes, blankets, sanitary pads) or funds. Visitors can
  email kandlfoundation.sa@gmail.com or use the Donate page on the website.
- How to volunteer: help distribute goods, assist at events, or help spread awareness.
  Point people to the "Get in Touch" / contact section, or the same email address.
- Location: Polokwane, Limpopo, South Africa.
- Contact email: kandlfoundation.sa@gmail.com

Style:
- Keep replies short and warm (2-4 sentences), like a helpful volunteer, not a corporate bot.
- If you don't know something specific (e.g. exact bank details, event dates), say so
  honestly and point the person to the contact email instead of guessing.
- Only talk about K&L Foundation and how to help/get help. For unrelated questions,
  gently redirect back to how you can help with the Foundation.
"""

MAX_HISTORY_MESSAGES = 12  # user+assistant turns kept per request (trimmed client-side too)

# ------------------- Basic rate limiting (per IP) -------------------
RATE_LIMIT_WINDOW = 60      # seconds
RATE_LIMIT_MAX_REQUESTS = 15
_request_log = defaultdict(deque)


def is_rate_limited(ip):
    now = time.time()
    log = _request_log[ip]
    while log and now - log[0] > RATE_LIMIT_WINDOW:
        log.popleft()
    if len(log) >= RATE_LIMIT_MAX_REQUESTS:
        return True
    log.append(now)
    return False


# ------------------- Routes -------------------
@app.route("/chat", methods=["POST"])
def chat():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if is_rate_limited(ip):
        return jsonify({
            "reply": f"{BOT_NAME}: You're sending messages a bit fast — please wait a moment and try again."
        }), 429

    data = request.get_json(silent=True) or {}
    user_msg = (data.get("message") or "").strip()
    history = data.get("history") or []  # [{role: "user"|"assistant", content: "..."}]

    if not user_msg:
        return jsonify({"reply": f"{BOT_NAME}: Please type something first!"})

    # Build message list: system prompt + trimmed history + new user message
    trimmed_history = history[-MAX_HISTORY_MESSAGES:]
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in trimmed_history:
        role = turn.get("role")
        content = turn.get("content")
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            messages.append({"role": role, "content": content.strip()})
    messages.append({"role": "user", "content": user_msg})

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.6,
            max_tokens=300,
        )
        bot_reply = response.choices[0].message.content.strip()
    except Exception as e:
        bot_reply = (
            f"{BOT_NAME}: Sorry, I couldn't process that right now. You can reach us "
            f"directly at kandlfoundation.sa@gmail.com in the meantime. ({e})"
        )

    return jsonify({"reply": bot_reply})


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": f"{BOT_NAME} server is running", "model": MODEL_NAME}), 200


# ------------------- Run Server -------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render sets PORT automatically
    app.run(host="0.0.0.0", port=port)
