"""
nlp_processor.py
------------------
Core NLP engine for the Supermarket Chatbot.

Pipeline (per functional requirement #2):
    1. Tokenization           - spaCy tokenizer splits raw text into tokens
    2. POS tagging             - identify nouns/adjectives that form product
                                  phrases and discard verbs, determiners,
                                  quantities, and connective words
    3. Noun-chunk extraction   - spaCy's dependency parser groups tokens into
                                  noun phrases (acts as our lightweight NER
                                  for product names, since supermarket items
                                  are not covered by spaCy's default NER
                                  labels like PERSON/ORG/GPE)
    4. Lemmatization            - normalizes plurals (e.g. "tomatoes" -> "tomato")
    5. Fuzzy matching          - resolves the cleaned phrase against the
                                  product database (canonical names + aliases),
                                  tolerating typos and minor wording differences
"""

import re
import spacy
from rapidfuzz import fuzz, process

from database import PRODUCT_DB

# Load spaCy's small English pipeline once (tokenizer, tagger, parser, lemmatizer)
_nlp = spacy.load("en_core_web_sm")

# Words that commonly precede an item but are not part of the product name
# (container/quantity words). These are stripped from noun chunks so that
# "a bottle of olive oil" -> "olive oil" and "2 packs of milk" -> "milk".
CONTAINER_WORDS = {
    "pack", "packs", "packet", "packets", "bottle", "bottles", "bag", "bags",
    "box", "boxes", "can", "cans", "tin", "tins", "loaf", "loaves", "bar",
    "bars", "piece", "pieces", "pair", "pairs", "roll", "rolls", "tube",
    "tubes", "jar", "jars", "carton", "cartons", "kg", "g", "gram", "grams",
    "kilogram", "kilograms", "liter", "liters", "litre", "litres", "ml",
    "dozen", "some", "few", "little", "lot", "lots",
}

# Generic request/politeness words that should never be treated as items
STOPWORD_PHRASES = {
    "i", "me", "we", "you", "some", "a", "an", "the", "please", "thanks",
    "thank you", "list", "item", "items", "good", "goods", "product",
    "products", "shelf", "shelves", "location", "locations",
}

# Common request-phrase preambles/politeness wrappers customers type before
# their actual list of goods. Stripped out before segmentation so leftover
# pronouns/verbs (e.g. "Can I get") don't pollute the extracted item names.
_PREAMBLE_PATTERNS = [
    r"^(can|could|may)\s+i\s+(get|have|buy)\s+",
    r"^i\s+(would like|want|need)\s+to\s+buy\s+",
    r"^i\s+(would like|want|need)\s+",
    r"^i'd\s+like\s+",
    r"^(get|give|fetch|find)\s+me\s+",
    r"^(please\s+)?(add|buy)\s+",
    r"^my\s+(shopping\s+)?list\s+(is|includes|has)\s*:?\s*",
    r"^looking\s+for\s+",
]

_TRAILING_PATTERNS = [
    r"\s*please\s*$",
    r"\s*thanks?\s*(you)?\s*$",
]

# Build a flat lookup: alias/canonical-name -> canonical product name
_ALIAS_TO_CANONICAL = {}
for canonical, info in PRODUCT_DB.items():
    _ALIAS_TO_CANONICAL[canonical.lower()] = canonical
    for alias in info.get("aliases", []):
        _ALIAS_TO_CANONICAL[alias.lower()] = canonical

_ALL_SEARCHABLE_TERMS = list(_ALIAS_TO_CANONICAL.keys())

FUZZY_MATCH_THRESHOLD = 78  # 0-100, rapidfuzz similarity score


def _clean_chunk(chunk_doc):
    """
    Strip leading determiners/numbers/container-words and trailing
    punctuation from a spaCy noun-chunk span, and lemmatize remaining nouns.
    Returns a cleaned string, e.g. "2 packs of milk" -> "milk".
    """
    tokens = [t for t in chunk_doc if not t.is_punct and not t.is_space]

    # Drop leading determiners, numbers, and container words
    while tokens and (
        tokens[0].pos_ in ("DET", "NUM")
        or tokens[0].text.lower() in CONTAINER_WORDS
        or tokens[0].pos_ == "ADP"  # e.g. "of"
    ):
        tokens = tokens[1:]

    if not tokens:
        return ""

    # If the phrase is just "bottle of olive oil" style already split by the
    # earlier strip, also drop a trailing "of <container>" pattern is rare;
    # handled naturally since noun_chunks from spaCy split at "of" already
    # in most cases for simple sentences.

    words = []
    for t in tokens:
        if t.text.lower() in CONTAINER_WORDS:
            continue
        # Use lemma for nouns to normalize plurals; keep adjectives as-is
        if t.pos_ == "NOUN":
            words.append(t.lemma_.lower())
        else:
            words.append(t.text.lower())

    return " ".join(words).strip()


def _strip_preamble(text: str) -> str:
    """Remove common request-phrase wrappers, e.g. 'Can I get X' -> 'X'."""
    cleaned = text.strip()
    for pattern in _PREAMBLE_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    for pattern in _TRAILING_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _clean_segment(segment: str) -> str:
    """
    Run POS tagging on a single delimiter-separated segment and strip any
    remaining leading pronouns/verbs/determiners/container-words and
    trailing filler words, lemmatizing the head noun(s).
    """
    seg_doc = _nlp(segment.strip())
    tokens = [t for t in seg_doc if not t.is_punct and not t.is_space]

    # Strip leading filler: pronouns, verbs, auxiliaries, determiners,
    # numbers, adpositions, and known container words. Never strip down to
    # nothing -- a lone remaining token is kept even if spaCy mis-tags a
    # typo'd product name (e.g. "chiken" -> VERB) as filler.
    while len(tokens) > 1 and (
        tokens[0].pos_ in ("DET", "NUM", "PRON", "VERB", "AUX", "ADP", "PART")
        or tokens[0].text.lower() in CONTAINER_WORDS
    ):
        tokens = tokens[1:]

    # Strip trailing filler (e.g. politeness words, stray verbs)
    while len(tokens) > 1 and (
        tokens[-1].pos_ in ("VERB", "AUX", "PRON", "INTJ")
        or tokens[-1].text.lower() in {"please", "thanks", "thank"}
    ):
        tokens = tokens[:-1]

    # A single leftover token that is a pure stopword/container word (not a
    # potential product name) should still be discarded.
    if len(tokens) == 1 and (
        tokens[0].text.lower() in CONTAINER_WORDS
        or tokens[0].text.lower() in {"please", "thanks", "thank", "a", "an", "the"}
    ):
        tokens = []

    if not tokens:
        return ""

    words = []
    for t in tokens:
        if t.text.lower() in CONTAINER_WORDS:
            continue
        if t.pos_ == "NOUN":
            words.append(t.lemma_.lower())
        else:
            # Keep raw surface form (covers misspellings mis-tagged as
            # VERB/PROPN/etc. by spaCy, which the fuzzy matcher can still
            # resolve against the product database).
            words.append(t.text.lower())

    return " ".join(words).strip()


def extract_candidate_items(text: str):
    """
    Steps 1-4 of the pipeline: strip conversational wrappers, tokenize on
    natural list delimiters (commas / 'and' / '&' / newlines), POS-tag each
    segment, and lemmatize/clean it into a candidate product-name phrase.

    Returns a list of unique, non-empty candidate phrases in the order
    they appeared in the input.
    """
    stripped = _strip_preamble(text)

    # Segment on commas, semicolons, newlines, ampersands, and the word "and"
    raw_segments = re.split(r",|;|\n|&|\band\b", stripped, flags=re.IGNORECASE)

    candidates = []
    seen = set()

    for seg in raw_segments:
        seg = seg.strip()
        if not seg:
            continue
        cleaned = _clean_segment(seg)
        if not cleaned or cleaned in STOPWORD_PHRASES:
            continue
        if cleaned not in seen:
            seen.add(cleaned)
            candidates.append(cleaned)

    # Fallback: if segmentation produced nothing (single free-flowing
    # sentence with no delimiters), fall back to spaCy noun-chunk extraction.
    if not candidates:
        doc = _nlp(stripped)
        for chunk in doc.noun_chunks:
            cleaned = _clean_chunk(chunk)
            if cleaned and cleaned not in STOPWORD_PHRASES and cleaned not in seen:
                seen.add(cleaned)
                candidates.append(cleaned)

    return candidates


def match_item_to_database(candidate: str):
    """
    Step 5: Fuzzy-match a cleaned candidate phrase against the product
    database (canonical names + aliases).

    Returns a tuple: (canonical_name or None, match_score 0-100)
    """
    candidate = candidate.lower().strip()
    if not candidate:
        return None, 0

    # 1) Exact match against canonical names or aliases
    if candidate in _ALIAS_TO_CANONICAL:
        return _ALIAS_TO_CANONICAL[candidate], 100

    # 2) Substring match (handles cases like "olive" matching "olive oil").
    # Only applied when the candidate is reasonably short (a real product
    # phrase, not an unsegmented run-on chunk) to avoid false positives.
    if len(candidate.split()) <= 3:
        for term, canonical in _ALIAS_TO_CANONICAL.items():
            if candidate == term:
                continue
            if (candidate in term or term in candidate) and len(candidate) >= 4:
                return canonical, 95

    # 3) Fuzzy match (handles typos / plural variants rapidfuzz didn't catch)
    best = process.extractOne(
        candidate, _ALL_SEARCHABLE_TERMS, scorer=fuzz.WRatio
    )
    if best is not None:
        term, score, _ = best
        if score >= FUZZY_MATCH_THRESHOLD:
            return _ALIAS_TO_CANONICAL[term], score

    return None, 0


def process_shopping_list(text: str):
    """
    Full pipeline entry point. Given a raw customer utterance/list, returns
    a dict with:
        - found:     list of {item, canonical, shelf, category, score}
        - not_found: list of raw candidate phrases that couldn't be matched
    """
    candidates = extract_candidate_items(text)

    found = []
    not_found = []

    for candidate in candidates:
        canonical, score = match_item_to_database(candidate)
        if canonical:
            info = PRODUCT_DB[canonical]
            found.append({
                "requested_as": candidate,
                "item": canonical,
                "shelf": info["shelf"],
                "category": info["category"],
                "confidence": score,
            })
        else:
            not_found.append(candidate)

    return {"found": found, "not_found": not_found}
