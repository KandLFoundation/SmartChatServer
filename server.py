import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

# ------------------- Flask App Setup -------------------
app = Flask(__name__)
CORS(app)

# ------------------- Environment Variables -------------------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
BOT_NAME = os.environ.get("BOT_NAME", "KL Lexus")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set!")

# ------------------- OpenAI 1.x Setup -------------------
openai.api_key = OPENAI_API_KEY

# ------------------- Fallback Responses -------------------
fallback_responses = {
    "donate": f"{BOT_NAME}: Thank you! Your donation helps provide food, clothes, blankets, and sanitary products to those in need. Every contribution counts!",
    "donation": f"{BOT_NAME}: Thank you! Your donation helps provide food, clothes, blankets, and sanitary products to those in need. Every contribution counts!",
    "volunteer": f"{BOT_NAME}: Volunteering is a great way to make an impact! You can help distribute goods, assist in events, or spread awareness about our cause.",
    "getting involved": f"{BOT_NAME}: You can volunteer, donate, share our mission, or participate in community campaigns.",
    "fund": f"{BOT_NAME}: All funds are used transparently to support our community programs, including food drives, clothing distribution, blankets, and hygiene support for young women."
}

def check_fallback(message):
    """Return a fallback reply if the message contains a known keyword."""
    message_lower = message.lower()
    for keyword, reply in fallback_responses.items():
        if keyword in message_lower:
            return reply
    return None

# ------------------- Routes -------------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_msg = data.get("message", "").strip()

    if not user_msg:
        return jsonify({"reply": f"{BOT_NAME}: Please type something first!"})

    # Check fallback first
    fallback_reply = check_fallback(user_msg)
    if fallback_reply:
        return jsonify({"reply": fallback_reply})

    # Try OpenAI if no fallback triggered
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are {BOT_NAME}, a helpful assistant for K&L Foundation."},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.7,
            max_tokens=200
        )
        bot_reply = response.choices[0].message.content.strip()
    except Exception as e:
        # Backup fallback if OpenAI fails
        bot_reply = f"{BOT_NAME}: Sorry, I couldn’t process that at the moment. Here’s something you can try: ask about donations, volunteering, getting involved, or fund usage. ({e})"

    return jsonify({"reply": bot_reply})

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": f"{BOT_NAME} server is running"}), 200

# ------------------- Run Server -------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render sets PORT automatically
    app.run(host="0.0.0.0", port=port)
