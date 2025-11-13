from flask import Flask, request, jsonify
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import wikipedia
import datetime
import requests

app = Flask(__name__)

# --- Bot Branding ---
BOT_NAME = "KL Lexus"

# --- Model Setup ---
model_name = "microsoft/DialoGPT-small"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get('message', '').strip()

    user_input_lower = user_input.lower()
    reply = ""

    # --- Predefined Responses ---
    if "time" in user_input_lower:
        reply = f"The current time is {datetime.datetime.now().strftime('%H:%M:%S')}"
    elif "date" in user_input_lower:
        reply = f"Today's date is {datetime.datetime.now().strftime('%Y-%m-%d')}"
    elif "donation" in user_input_lower:
        reply = "Donations help us provide education, resources, and digital skills to the youth in South Africa through the K&L Foundation."
    elif "mission" in user_input_lower:
        reply = "Our mission is to educate, innovate, and empower the youth through technology and digital skills."
    elif "projects" in user_input_lower:
        reply = "We run programs on coding, AI, drones, and creative digital arts for young South Africans."
    elif "contact" in user_input_lower or "reach" in user_input_lower:
        reply = "You can reach us at info@kldigital.org or visit https://kldigital.org"
    elif "who is" in user_input_lower or "what is" in user_input_lower:
        try:
            summary = wikipedia.summary(user_input, sentences=2)
            reply = summary
        except wikipedia.DisambiguationError as e:
            reply = f"Your query is ambiguous. Did you mean: {e.options[:5]}?"
        except wikipedia.PageError:
            reply = "I couldn't find much about that topic."
        except Exception:
            reply = "Sorry, I couldn't fetch information from Wikipedia."
    else:
        # --- Fallback to AI model ---
        try:
            input_ids = tokenizer.encode(user_input + tokenizer.eos_token, return_tensors='pt')
            output_ids = model.generate(input_ids, max_length=1000, pad_token_id=tokenizer.eos_token_id,
                                        do_sample=True, temperature=0.7, top_p=0.9)
            reply = tokenizer.decode(output_ids[:, input_ids.shape[-1]:][0], skip_special_tokens=True)
            if not reply.strip():
                reply = "I'm not sure about that. Can you rephrase?"
        except Exception:
            reply = "Oops! Something went wrong with the AI model."

    # --- Prefix Bot Name ---
    return jsonify({'reply': f"{BOT_NAME}: {reply}"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
