# AI Agent Notes (Smart-Mini-Library)

## Goal
Add an “AI agent” experience to the UI.

## Constraints
- No external LLM API calls required.
- Must support UI/UX and include an image-generation-like output (offline/deterministic).

## Proposed MVP (offline deterministic)
1) New route: `GET/POST /agent`
2) UI:
   - Text input: user message
   - Agent output chat bubbles
   - Optional "Generate image" section
3) Offline agent behavior:
   - Use deterministic rules:
     - If user asks for “recommend”, call existing `recommend_books()` using the message.
     - If user asks for “summarize”, call existing `summarize_article()`.
     - Otherwise, call existing `build_learning_resources()` and present a structured plan.
   - Image generation:
     - Create a simple SVG “cover” image based on topic hash.
     - Return it as a `data:image/svg+xml;base64,...` URI.

## Files to change for implementation
- `app.py`: add route + helper functions
- `templates/agent.html`: new
- `templates/base.html`: add nav link
- `static/style.css`: add agent-specific styling
- `TODO.md`: track completion

