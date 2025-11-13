import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

# ------------------- App initialization -------------------
app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from your website

# Load environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
BOT_NAME = os.environ.get("BOT_NAME", "KL Lexus")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set!")

# ------------------- OpenAI 1.x setup -------------------
openai.api_key = OPENAI_API_KEY

# ------------------- Fallback knowledge base -------------------
fallback_responses = {
    "donation": f"{BOT_NAME}: Thank you for asking! Your donation helps us provide food, clothing, blankets, and sanitary products to those in need. Every contribution makes a real difference in our community.",
    "volunteer": f"{BOT_NAME}: Volunteering is a great way to make an impact! You can help distribute goods, assist in events, or spread awareness about our cause.",
    "getting involved": f"{BOT_NAME}: There are many ways to get involved: volunteer, donate, share our mission, or participate in community campaigns.",
    "fund usage": f"{BOT_NAME}: All funds are used transparently to support our community programs, including food drives, clothing distribution, blankets, and hygiene support for young women."
}

def check_fallback(message):
    message_lower = message.lower()
    for keyword, reply in fallback_responses.items():
        if keyword in message_lower:
            return reply
    return None

# ------------------- Chat endpoint -------------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_msg = data.get("message", "").strip()

    if not user_msg:
        return jsonify({"reply": f"{BOT_NAME}: Please type something first!"})

    # ------------------- Check fallback knowledge base -------------------
    fallback_reply = check_fallback(user_msg)
    if fallback_reply:
        return jsonify({"reply": fallback_reply})

    # ------------------- Call OpenAI -------------------
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
        # Backup response if OpenAI fails
        bot_reply = f"{BOT_NAME}: Sorry, I couldn’t process that at the moment. Here’s something you can try: ask about donations, volunteering, getting involved, or fund usage. ({e})"

    return jsonify({"reply": bot_reply})

# ------------------- Home endpoint -------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": f"{BOT_NAME} server is running"}), 200

# ------------------- Run server -------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render sets PORT automatically
    app.run(host="0.0.0.0", port=port)
