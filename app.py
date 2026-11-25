"""
app.py
-------
Flask web application for the Supermarket Shelf-Locator Chatbot.
Provides a browser-based chat UI (functional requirement: web-based UI)
and a downloadable PDF "printed summary" of the shelf list.

Run: python app.py 
Then open http://localhost:5000  in a browser.
Sample input: i want buy 2 packets of bread, fresh milk, choclate, tomatoes and sausages
"""

import os
import uuid

from flask import Flask, request, jsonify, render_template, send_file

from nlp_processor import process_shopping_list
from database import PRODUCT_DB
from receipt import build_pdf_receipt

BASE_DIR = os.path.dirname(__file__)
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = Flask(__name__)

# In-memory store mapping a receipt id -> (found, not_found) so the
# "download PDF" button can regenerate the exact receipt for that turn.
_RECEIPT_CACHE = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/menu")
def api_menu():
    items = [
        {"item": name.title(), "category": info["category"], "shelf": info["shelf"]}
        for name, info in sorted(PRODUCT_DB.items(), key=lambda kv: kv[1]["shelf"])
    ]
    return jsonify(items)


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(force=True)
    user_text = (data or {}).get("message", "").strip()

    if not user_text:
        return jsonify({"error": "Empty message"}), 400

    result = process_shopping_list(user_text)
    found = result["found"]
    not_found = result["not_found"]

    receipt_id = str(uuid.uuid4())
    _RECEIPT_CACHE[receipt_id] = {"found": found, "not_found": not_found}

    sorted_found = sorted(found, key=lambda x: x["shelf"])

    return jsonify({
        "found": sorted_found,
        "not_found": not_found,
        "receipt_id": receipt_id if found else None,
    })


@app.route("/api/receipt/<receipt_id>.pdf")
def api_receipt_pdf(receipt_id):
    cached = _RECEIPT_CACHE.get(receipt_id)
    if not cached:
        return jsonify({"error": "Receipt not found or expired"}), 404

    pdf_path = os.path.join(OUTPUT_DIR, f"receipt_{receipt_id}.pdf")
    build_pdf_receipt(cached["found"], cached["not_found"], pdf_path)
    return send_file(pdf_path, as_attachment=True, download_name="shelf_receipt.pdf")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
