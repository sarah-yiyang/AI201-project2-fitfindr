# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

---

# FitFindr — Implementation

FitFindr is a thrift-shopping agent: given a natural-language request and the user's wardrobe, it finds a secondhand listing, suggests how to style it, and writes a shareable caption. The flow is a fixed three-tool pipeline driven by a planning loop in `agent.py`, with the three tools in `tools.py` and a Gradio UI in `app.py`.

Run it:
```bash
.venv/bin/python app.py          # launches the Gradio UI
.venv/bin/python agent.py        # CLI smoke test (happy path + no-results path)
pytest tests/                    # tool tests
```

## Example Run (end to end)

A full interaction, captured from `run_agent`. **One natural-language query flows through all three tools** — `search_listings` → `suggest_outfit` → `create_fit_card` — with state passed automatically (the user never re-enters the item or the outfit).

**Query:** *"I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"*

```
# 1. search_listings(description="...vintage graphic tee...", size=None, max_price=30.0)
selected_item → Graphic Tee — 2003 Tour Bootleg Style | $24.0 · depop

# 2. suggest_outfit(new_item=<that item>, wardrobe=<example wardrobe>)
outfit_suggestion → "If you grab that Graphic Tee, you can create a grunge-inspired
   look by pairing it with your Baggy straight-leg jeans and Black combat boots...
   layer it under your Vintage black denim jacket for a cooler-weather option."

# 3. create_fit_card(outfit=<that suggestion>, new_item=<that item>)
fit_card → "Just scored this Graphic Tee on depop for $24.0 and I'm obsessed with the
   2003 tour bootleg style vibes. Been wearing it with my fave baggy straight-leg
   jeans and black combat boots for a laid-back, grunge-inspired look..."
```

State passing was confirmed with object-identity (`is`) checks: the exact `selected_item` dict reached both `suggest_outfit` and `create_fit_card`, and the exact `outfit_suggestion` string returned by `suggest_outfit` was the one fed into `create_fit_card`.

**Divergent path — non-standard input** (`python agent.py`, second test case). The agent does **not** run the same three-tool sequence every time:

```
Query: "designer ballgown size XXS under $5"
# search_listings(description="designer ballgown", size="XXS", max_price=5.0) → []
# search_results is empty → loop sets session["error"] and STOPS.
# suggest_outfit and create_fit_card are NOT called (outfit_suggestion / fit_card stay None).

Error message: No listings found — try broadening your keywords, loosening the
size, or raising the price cap.
```

The failure response is specific and actionable: it names what happened (no listings) and what to try next (broaden keywords, loosen size, raise the price cap).

## Tool Inventory

All signatures below match the actual functions in `tools.py`.

### `search_listings(description, size=None, max_price=None) -> list[dict]`
- **Inputs:**
  - `description` (str) — keywords describing the item, e.g. `"vintage graphic tee"`
  - `size` (str | None, default `None`) — size filter; case-insensitive substring match (`"M"` matches `"S/M"`). `None` skips size filtering.
  - `max_price` (float | None, default `None`) — inclusive price ceiling. `None` skips price filtering.
- **Output:** a list of the **top 3** matching listing dicts, sorted by relevance (best first); fewer than 3 if fewer match; `[]` if nothing matches. Each dict has the full listing fields (`id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`).
- **Purpose:** filter the mock dataset by price/size, then score remaining listings by keyword overlap with `description`, drop zero-score listings, and return the best matches.

### `suggest_outfit(new_item, wardrobe) -> str`
- **Inputs:**
  - `new_item` (dict) — a listing dict (the matched item)
  - `wardrobe` (dict) — a wardrobe dict with an `items` key (a list of wardrobe-item dicts); may be empty
- **Output:** a non-empty string with styling suggestions.
- **Purpose:** call the LLM (Groq `llama-3.3-70b-versatile`) to suggest 1–2 outfits. With a non-empty wardrobe it references the user's named pieces; with an empty wardrobe it gives general standalone styling advice.

### `create_fit_card(outfit, new_item) -> str`
- **Inputs:**
  - `outfit` (str) — the styling suggestion returned by `suggest_outfit`
  - `new_item` (dict) — the matched listing dict
- **Output:** a 2–4 sentence string usable as an Instagram/TikTok caption (or a descriptive error string if `outfit` is empty).
- **Purpose:** call the LLM (high temperature, so captions vary) to turn the outfit into a casual, authentic caption that mentions the item name, price, and platform once each.

## Planning Loop

`run_agent(query, wardrobe)` in `agent.py` runs a fixed pipeline and **branches on each tool's result** rather than calling all three unconditionally:

1. **Parse** — `_parse_query()` extracts `description`, `size`, and `max_price` from the query via regex (no LLM call), and stores them in `session["parsed"]`.
2. **Search** — calls `search_listings` with the parsed params. **Conditional:** if `search_results` is empty, it sets `session["error"]` and **returns the session immediately** — `suggest_outfit` and `create_fit_card` are never called.
3. **Select** — if there are results, `selected_item = search_results[0]`.
4. **Suggest** — calls `suggest_outfit(selected_item, wardrobe)`. An empty wardrobe does **not** stop the loop: the tool returns standalone advice and the pipeline continues.
5. **Fit card** — calls `create_fit_card(outfit_suggestion, selected_item)`.
6. **Return** the completed session.

The gating rule: a stage runs only if the previous stage produced usable state. The single early exit is the no-results branch in step 2.

## State Management

All state lives in one session dict created by `_new_session(query, wardrobe)`. Each stage reads from it and writes its result back; tools never call each other directly. Fields, and when they're set:

| Session key | Set by | Read by (as tool parameter) |
|-------------|--------|------------------------------|
| `query` | `_new_session` (user input) | query parsing |
| `parsed` | parsing step | `search_listings(description, size, max_price)` |
| `search_results` | `search_listings` | planning loop (branch + select) |
| `selected_item` | planning loop (`search_results[0]`) | `suggest_outfit(new_item=…)`, `create_fit_card(new_item=…)` |
| `wardrobe` | `_new_session` | `suggest_outfit(wardrobe=…)` |
| `outfit_suggestion` | `suggest_outfit` | `create_fit_card(outfit=…)` |
| `fit_card` | `create_fit_card` | final output |
| `error` | any early exit | planning loop, `app.py` |

## Error Handling Strategy

Each tool fails by returning a sensible value instead of raising, so the loop and UI never crash.

| Tool | Failure mode | Strategy | Concrete example from testing |
|------|-------------|----------|-------------------------------|
| `search_listings` | No listing matches | Return `[]`; the loop sets `session["error"]` and stops before the LLM tools | `search_listings("designer ballgown", size="XXS", max_price=5)` → `[]`, and `run_agent(...)` left `selected_item`, `outfit_suggestion`, `fit_card` all `None` |
| `suggest_outfit` | Empty wardrobe | Don't crash on `wardrobe["items"] == []`; return general standalone styling advice instead | `suggest_outfit(item, get_empty_wardrobe())` returned a non-empty advice string (vs. naming specific pieces with the example wardrobe) |
| `create_fit_card` | Empty/whitespace `outfit` | Guard before the LLM call; return a descriptive error string, never raise | `create_fit_card("", item)` and `create_fit_card("   ", item)` both returned `"Can't write a fit card without an outfit suggestion. Generate an outfit first, then try again."` |

## Spec Reflection

- **How the spec helped:** Writing the State Management section's session-key → tool-parameter table before coding surfaced a naming mismatch — the session stores `selected_item`/`outfit_suggestion`, but the tools take `new_item`/`outfit`. Having that mapping written down meant `run_agent` wired the right values into each call on the first try instead of passing a wrongly-named key.
- **Where implementation diverged:** The original Tool 1 spec said `search_listings` returns "a list of matching listing dicts, sorted by relevance" with no limit. In testing, a query like `"vintage graphic tee"` returned 29 results, because a single weak keyword (`"vintage"`) is enough to score a match. I diverged by capping output at the top 3 — which both matches the assignment's "returns 3 matching listings" framing and keeps the agent focused on the best match. I then updated planning.md to say "top 3" so the spec and code agree.

## AI Usage

- I directed Claude Code to implement the function from my Tool 1 spec using `load_listings()` (not re-reading the file), with keyword-overlap scoring and an empty-list failure mode. The generated version returned every listing with a non-zero score (29 results for one query). I overrode that by adding the top-3 cap and re-ran my three test queries (a match, a no-match, a strict `max_price`) to confirm the relevant items still ranked first.
- When `pytest tests/` failed with `ModuleNotFoundError: No module named 'tools'`, the AI first proposed adding a `conftest.py`. I rejected that as an extra file I didn't want, and instead had it diagnose the real cause (the project root wasn't on `sys.path`) and add a one-line `pytest.ini` with `pythonpath = .`, which made the documented `pytest tests/` command work directly.
