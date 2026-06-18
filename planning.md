# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): ...
- `size` (str): ...
- `max_price` (float): ...

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): ...
- `wardrobe` (dict): ...

**What it returns:**
<!-- Describe the return value -->

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (...): ...

**What it returns:**
<!-- Describe the return value -->

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | |
| suggest_outfit | Wardrobe is empty | |
| create_fit_card | Outfit input is missing or incomplete | |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

**Milestone 4 — Planning loop and state management:**

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**What FitFindr needs to do:** FitFindr is a thrift-shopping agent that takes a user's request plus their wardrobe and chains three tools to land on a single styled recommendation. A user's request for an item triggers `search_listings` (filtering the mock dataset by description, size, and max price); the top match then triggers `suggest_outfit`, which pairs that item against the user's wardrobe; and that suggestion triggers `create_fit_card` to write the final caption. If `search_listings` finds nothing the agent stops and tells the user what to loosen (price, size, or keywords) rather than calling later tools with empty input, and if the wardrobe is empty `suggest_outfit` styles the item on its own instead of failing.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1 — Search:** The agent parses the request and calls `search_listings(description="vintage graphic tee", size=None, max_price=30.0)`. It scans the dataset for tops whose title/tags match "vintage graphic tee" and whose price is ≤ $30, returning the top matches (e.g. `lst_006` "Graphic Tee — 2003 Tour Bootleg Style," $24, depop, good; `lst_033` "Vintage Band Tee — Faded Grey," $19, depop, fair). The agent picks the top result, `lst_006`.

**Step 2 — Suggest outfit:** With a listing in hand, the agent calls `suggest_outfit(new_item=<lst_006>, wardrobe=<example wardrobe>)`. It reads the user's closet — baggy dark-wash jeans (`w_001`), chunky white sneakers (`w_007`), black denim jacket (`w_006`) — and returns a styling suggestion: "Wear this boxy bootleg tee with your baggy dark-wash jeans and chunky white sneakers; throw the cropped black denim jacket over the top and half-tuck the tee for shape."

**Step 3 — Fit card:** The agent passes the suggestion and item into `create_fit_card(outfit=<suggestion>, new_item=<lst_006>)`, which produces a shareable caption: "scored this 2003 bootleg tour tee on depop for $24 🤎 styled it with my baggy jeans + chunky sneakers and it's the easy fit i'll wear on repeat."

**Final output to user:** The user sees the matched listing (title, price, platform, condition), the styling suggestion built from their own wardrobe, and the ready-to-post fit card caption. If Step 1 had returned no matches, the user would instead see a short message suggesting they raise the price cap or broaden the keywords, and the interaction would end there.
