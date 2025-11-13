import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

# ------------------- Your app initialization -------------------
app = Flask(__name__)
CORS(app)

# Load environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
BOT_NAME = os.environ.get("BOT_NAME", "KL Lexus")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set!")

# ------------------- FIX: Set OpenAI API key for 1.x -------------------
openai.api_key = OPENAI_API_KEY
# ---------------------------------------------------------------------

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_msg = data.get("message", "").strip()

    if not user_msg:
        return jsonify({"reply": f"{BOT_NAME}: Please type something first!"})

    try:
        # ------------------- FIX: Use openai.chat.completions.create -------------------
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
        # -------------------------------------------------------------------------------
    except Exception as e:
        bot_reply = f"{BOT_NAME}: Sorry, I couldn’t process that. ({e})"

    return jsonify({"reply": bot_reply})

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "KL Lexus server is running"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render sets PORT automatically
    app.run(host="0.0.0.0", port=port)
