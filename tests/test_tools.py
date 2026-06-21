from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

SAMPLE_OUTFIT = (
    "Pair the bootleg tee with baggy dark-wash jeans and chunky white "
    "sneakers; layer a cropped black denim jacket on top."
)

# A sample listing dict to feed into suggest_outfit (independent of search).
SAMPLE_ITEM = {
    "id": "lst_006",
    "title": "Graphic Tee — 2003 Tour Bootleg Style",
    "category": "tops",
    "colors": ["black"],
    "style_tags": ["graphic tee", "vintage", "grunge"],
    "price": 24.0,
    "platform": "depop",
}

def test_search_returns_results():
    # A match: real query that should find listings.
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    # A no-match: returns an empty list, never raises.
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []

def test_search_price_filter():
    # A strict max_price: every result stays within the cap.
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


# --- suggest_outfit (calls the live Groq API) ---

def test_suggest_outfit_with_wardrobe():
    # Normal case: returns a non-empty styling string.
    result = suggest_outfit(SAMPLE_ITEM, get_example_wardrobe())
    assert isinstance(result, str)
    assert result.strip() != ""

def test_suggest_outfit_empty_wardrobe():
    # Failure mode: empty wardrobe must not crash — returns general advice.
    result = suggest_outfit(SAMPLE_ITEM, get_empty_wardrobe())
    assert isinstance(result, str)
    assert result.strip() != ""


# --- create_fit_card ---

def test_create_fit_card_empty_outfit():
    # Failure mode (no API call): empty/whitespace outfit returns a string,
    # never raises.
    assert isinstance(create_fit_card("", SAMPLE_ITEM), str)
    assert create_fit_card("   ", SAMPLE_ITEM).strip() != ""

def test_create_fit_card_returns_caption():
    # Normal case (calls the live Groq API): returns a non-empty caption.
    result = create_fit_card(SAMPLE_OUTFIT, SAMPLE_ITEM)
    assert isinstance(result, str)
    assert result.strip() != ""

def test_create_fit_card_varies():
    # Captions should differ across runs on the same input (high temperature).
    cards = [create_fit_card(SAMPLE_OUTFIT, SAMPLE_ITEM) for _ in range(3)]
    assert len(set(cards)) > 1