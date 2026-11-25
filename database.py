"""
database.py
------------
Predefined product -> shelf location database for the Supermarket Chatbot.

Each product entry contains:
    - shelf:    Shelf/aisle number (string, e.g. "A3")
    - category: Product category (for display / grouping)
    - aliases:  Alternative names, synonyms, or common misspellings that
                should also resolve to this product (used by the NLP
                matching layer for robustness).

NOTE: This is a simple in-memory database for demonstration purposes.
In a production system this would be backed by a real database
(e.g. SQLite/PostgreSQL) with an admin interface for supermarket staff
to update stock locations.
"""

PRODUCT_DB = {
    "milk": {
        "shelf": "A1",
        "category": "Dairy",
        "aliases": ["fresh milk", "full cream milk", "milk carton"],
    },
    "bread": {
        "shelf": "A2",
        "category": "Bakery",
        "aliases": ["loaf", "loaf of bread", "white bread", "brown bread"],
    },
    "eggs": {
        "shelf": "A1",
        "category": "Dairy",
        "aliases": ["egg", "egg tray", "egg pack"],
    },
    "butter": {
        "shelf": "A1",
        "category": "Dairy",
        "aliases": ["margarine"],
    },
    "cheese": {
        "shelf": "A1",
        "category": "Dairy",
        "aliases": ["cheddar", "cheese block", "cheese slice"],
    },
    "rice": {
        "shelf": "B1",
        "category": "Grains & Staples",
        "aliases": ["basmati rice", "white rice", "rice bag"],
    },
    "sugar": {
        "shelf": "B2",
        "category": "Grains & Staples",
        "aliases": ["white sugar", "brown sugar"],
    },
    "salt": {
        "shelf": "B2",
        "category": "Grains & Staples",
        "aliases": ["table salt", "sea salt"],
    },
    "flour": {
        "shelf": "B1",
        "category": "Grains & Staples",
        "aliases": ["wheat flour", "all purpose flour"],
    },
    "olive oil": {
        "shelf": "B3",
        "category": "Cooking Essentials",
        "aliases": ["oil", "cooking oil", "extra virgin olive oil"],
    },
    "tomatoes": {
        "shelf": "C1",
        "category": "Fresh Produce",
        "aliases": ["tomato", "tomatoe", "cherry tomatoes"],
    },
    "onions": {
        "shelf": "C1",
        "category": "Fresh Produce",
        "aliases": ["onion", "red onion", "big onion"],
    },
    "potatoes": {
        "shelf": "C2",
        "category": "Fresh Produce",
        "aliases": ["potato", "potatos"],
    },
    "bananas": {
        "shelf": "C3",
        "category": "Fresh Produce",
        "aliases": ["banana"],
    },
    "apples": {
        "shelf": "C3",
        "category": "Fresh Produce",
        "aliases": ["apple"],
    },
    "chicken": {
        "shelf": "D1",
        "category": "Meat & Poultry",
        "aliases": ["chicken breast", "chicken meat"],
    },
    "fish": {
        "shelf": "D2",
        "category": "Seafood",
        "aliases": ["fresh fish", "seafood"],
    },
    "toothpaste": {
        "shelf": "E1",
        "category": "Personal Care",
        "aliases": ["tooth paste"],
    },
    "soap": {
        "shelf": "E1",
        "category": "Personal Care",
        "aliases": ["bar soap", "bathing soap"],
    },
    "shampoo": {
        "shelf": "E1",
        "category": "Personal Care",
        "aliases": ["hair shampoo"],
    },
    "toilet paper": {
        "shelf": "E2",
        "category": "Household",
        "aliases": ["tissue", "tissue paper", "toilet roll"],
    },
    "detergent": {
        "shelf": "E2",
        "category": "Household",
        "aliases": ["washing powder", "laundry detergent", "washing detergent"],
    },
    "coffee": {
        "shelf": "F1",
        "category": "Beverages",
        "aliases": ["instant coffee", "coffee powder"],
    },
    "tea": {
        "shelf": "F1",
        "category": "Beverages",
        "aliases": ["tea bags", "tea leaves", "black tea"],
    },
    "biscuits": {
        "shelf": "F2",
        "category": "Snacks",
        "aliases": ["biscuit", "cookies", "cookie"],
    },
    "chocolate": {
        "shelf": "F2",
        "category": "Snacks",
        "aliases": ["chocolate bar", "choc"],
    },
}


def get_all_items():
    """Return the full product database."""
    return PRODUCT_DB


def get_shelf(item_name: str):
    """Direct lookup by exact canonical item name (case-insensitive)."""
    entry = PRODUCT_DB.get(item_name.lower())
    return entry
