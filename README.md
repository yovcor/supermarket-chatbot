Supermarket Shelf-Locator Chatbot

A web-based chatbot that reads a customer's shopping list in plain English and tells them which shelf each item is on, using NLP (tokenization, POS tagging, lemmatization, and fuzzy matching) to extract and match items against a product database.


Install the dependencies: pip install -r requirements.txt

Start the server: python app.py

Then open **http://localhost:5000** in your browser.

Usage

Type your shopping list in plain sentences, like "I need milk, bread, eggs and toothpaste." The chatbot replies with a table showing each item's shelf number. It tolerates typos and plurals, so "tootpaste" still matches "toothpaste."

Click View full menu to see all items in the store's database. If at least one item is found, click Print / Download Receipt (PDF) to get a printable summary.

Project files

- app.py — Flask server and API routes
- database.py — product-to-shelf lookup table
- nlp_processor.py — NLP pipeline for extracting and matching items
- receipt.py — generates the text and PDF receipts
- templates/index.html — the chat interface

