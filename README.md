# CMS AI Filter Service

A **natural language to filter API translation layer** for the CMS Operator Portal. Operators describe what they want to find in plain English — the service translates that into a structured filter payload and proxies the result from the Java backend, returning data in the same format the existing portal table component already understands.

---

## Table of Contents

- [What It Does](#what-it-does)
- [How It Works](#how-it-works)
- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Running the Service](#running-the-service)
- [API Reference](#api-reference)
- [LLM Adapters](#llm-adapters)
- [Adding a New Adapter](#adding-a-new-adapter)
- [Filter Schema](#filter-schema)
- [Running Tests](#running-tests)
- [Integrating with Angular](#integrating-with-angular)
- [Troubleshooting](#troubleshooting)

---

## What It Does

Operators currently need 8–12 clicks to find and filter content in the portal:

> Dashboard → Media Assets → Select Filters → Apply → Wait → Select Results

With this service, an operator types a single sentence:

> *"Show me all episodes of Mirzapur in Ready For QC"*

And the system:
1. Understands the intent
2. Translates it into the exact filter API request body the Java backend expects
3. Asks a clarifying question (with clickable option chips) if anything is ambiguous
4. Returns data in the same format the existing Angular table component already renders

No new table components. No new backend queries. Just a translation layer on top of what already exists.

---

## How It Works

```
Operator types query
        │
        ▼
  Angular Command Bar
        │
        ▼
  POST /ai/resolve          ← FastAPI (this service)
        │
        ├─ Builds system prompt from filter schema + runtime context
        ├─ Calls LLM (Groq / Bedrock / Custom)
        ├─ Parses + validates LLM JSON output
        ├─ Resolves semantic date tokens (LAST_7_DAYS → real dates)
        │
        ▼
  status: resolved?  ──────────────────────────────────────────────┐
        │                                                           │
        │ status: ambiguous?                                        │
        ▼                                                           │
  Angular shows question + chips                                    │
  Operator clicks or types answer                                   │
        │                                                           │
        ▼                                                           │
  POST /ai/resolve (with history)                                   │
        │                                                           ▼
        └──────────────────────────────────────► POST /ai/execute
                                                        │
                                                        ▼
                                               Proxies to Java backend
                                                        │
                                                        ▼
                                               Returns raw response
                                                        │
                                                        ▼
                                         Angular renders existing table
```

The LLM never touches your database directly. It only outputs a structured JSON payload that your existing Java filter API already knows how to handle.

---

## Features

### Natural Language Querying
Operators write queries the way they think:
- *"Show me all released movies in India"*
- *"Give me Mirzapur episodes that failed QC"*
- *"Content ingested last week from Sony"*
- *"Show me Hindi dubbed movies with active license"*

### Intelligent Clarification
When a query is ambiguous, the service asks a focused clarifying question with clickable option chips in the UI — not a generic "please clarify" message.

```json
{
  "status": "ambiguous",
  "question": "Which season of Sacred Games are you looking for?",
  "options": ["Season 1", "Season 2", "All seasons"],
  "allow_custom": true
}
```

### Multi-Turn Conversation
Clarifications are tracked across turns. If an operator answers "Season 2" after being asked which season, the service remembers the original query context and resolves the complete intent.

### Semantic Date Resolution
Relative date expressions are converted to actual date strings at request time:
- *"last week"* → `ASSET_INGESTION_RANGE` with real date range
- *"this month"* → first day of current month to today
- Supported tokens: `TODAY`, `YESTERDAY`, `LAST_7_DAYS`, `LAST_30_DAYS`, `THIS_MONTH`, `LAST_MONTH`, `THIS_YEAR`

### LLM Output Validation & Sanitisation
The service never blindly passes LLM output to the backend. Every response is:
- Checked against the filter schema (unknown keys are dropped)
- Enum values are case-corrected (`ready for qc` → `Ready For QC`)
- Filter types are corrected if wrong (e.g. `search` vs `filter`)
- SQL injection keywords blocked from column lists

### Provider-Agnostic AI Client
Swap LLM providers via a single config change. Three adapters included out of the box:
- **Groq** (llama-3.3-70b-versatile) — recommended for testing
- **AWS Bedrock** (Claude, Titan, Mistral)
- **Custom Internal LLM** — generic HTTP POST, adapt to your internal LLM's API shape

### Zero Backend Changes
The service proxies to your existing Java filter API. No new DB queries, no schema changes, no Java code modifications needed.

### Human Summary
Every resolved response includes a plain English summary of what was matched:
> *"Episodes of Mirzapur with status Ready For QC"*

Shown above the results table so operators can confirm the system understood them correctly.

---

## Project Structure

```
cms-ai-filter/
│
├── main.py                          # FastAPI app entry point, CORS config
├── config.py                        # Pydantic settings, reads from .env
├── requirements.txt
├── pytest.ini
├── .env.example                     # Copy this to .env and fill in values
│
├── app/
│   ├── ai/
│   │   ├── client.py                # Abstract AIClient interface (ABC)
│   │   ├── factory.py               # Returns correct adapter based on config
│   │   └── adapters/
│   │       ├── groq_adapter.py      # Groq API (llama-3.3-70b)
│   │       ├── bedrock_adapter.py   # AWS Bedrock
│   │       └── custom_adapter.py    # Internal LLM via HTTP POST
│   │
│   ├── prompts/
│   │   └── system_prompt.py         # Prompt builder — generated from schema
│   │
│   ├── schema/
│   │   └── filter_schema.py         # Single source of truth for all filters
│   │
│   ├── services/
│   │   ├── intent_resolver.py       # Core orchestration: query → LLM → result
│   │   ├── filter_proxy.py          # Proxies resolved payload to Java backend
│   │   ├── validator.py             # Validates + sanitises LLM output
│   │   └── date_resolver.py         # Semantic date tokens → real date strings
│   │
│   ├── models/
│   │   └── request_models.py        # All Pydantic request/response models
│   │
│   └── api/
│       └── routes.py                # The 3 endpoints
│
└── tests/
    ├── conftest.py                  # Shared fixtures (MockAIClient)
    ├── test_intent_resolver.py      # 18 tests — all response paths
    ├── test_validator.py            # 14 tests — schema enforcement
    ├── test_date_resolver.py        # 13 tests — date token resolution
    └── test_system_prompt.py        # 8 tests  — prompt correctness
```

---

## Prerequisites

- Python 3.12+
- pip
- Access to one of: Groq API key, AWS credentials (Bedrock), or your internal LLM URL
- Your Java Spring Boot backend running and accessible

---

## Setup & Installation

**1. Clone / unzip the project**

```bash
unzip cms-ai-filter.zip
cd cms-ai-filter
```

**2. Create a virtual environment (recommended)**

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Create your `.env` file**

```bash
cp .env.example .env
```

Then open `.env` and fill in the required values (see [Configuration](#configuration) below).

---

## Configuration

All configuration is via the `.env` file. Here is the full reference:

```env
# ── LLM Adapter ───────────────────────────────────────────────────────────────
# Which LLM provider to use. Options: "groq" | "bedrock" | "custom"
LLM_ADAPTER=groq

# ── Groq ──────────────────────────────────────────────────────────────────────
# Get your key from https://console.groq.com
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# ── AWS Bedrock ────────────────────────────────────────────────────────────────
# Uses your ambient AWS credentials (IAM role, ~/.aws/credentials, or env vars)
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# ── Custom Internal LLM ───────────────────────────────────────────────────────
# Generic HTTP POST adapter — point at your internal LLM's endpoint
CUSTOM_LLM_URL=http://your-internal-llm/v1/chat
CUSTOM_LLM_API_KEY=your_key_if_needed

# ── Java Backend ──────────────────────────────────────────────────────────────
# Your existing Spring Boot service base URL and filter endpoint
JAVA_BACKEND_URL=http://localhost:8080
JAVA_FILTER_ENDPOINT=/api/v1/assets/filter

# ── App ────────────────────────────────────────────────────────────────────────
LOG_LEVEL=INFO
```

### Choosing an Adapter

| Adapter | When to use |
|---|---|
| `groq` | Local development, testing. Fast and cheap. llama-3.3-70b handles this task well. |
| `bedrock` | Production if your infra is on AWS. Uses IAM auth — no key to manage. |
| `custom` | Your internal 70B class LLM. Edit `custom_adapter.py` to match its API shape. |

---

## Running the Service

**Development (with auto-reload):**

```bash
uvicorn main:app --reload --port 8000
```

**Production:**

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Verify it's running:**

```bash
curl http://localhost:8000/ai/health
# → {"status":"ok","adapter":"groq:llama-3.3-70b-versatile"}
```

**Interactive API docs:**

Open `http://localhost:8000/docs` in your browser — FastAPI auto-generates a Swagger UI where you can test all endpoints directly.

---

## API Reference

### `POST /ai/resolve`

Translates a natural language query into a filter payload, or returns a clarifying question.

**Request body:**

```json
{
  "query": "Show me all episodes of Mirzapur in Ready For QC",
  "conversation_history": [],
  "context": {
    "countries": ["IN", "US", "KR"],
    "providers": ["Sony", "Viacom", "Disney"]
  }
}
```

| Field | Type | Description |
|---|---|---|
| `query` | string | The operator's natural language input |
| `conversation_history` | array | Prior turns for multi-step clarification. Empty on first call. |
| `context.countries` | array | Country codes from your existing country API |
| `context.providers` | array | Provider names from your existing provider API |

**Response — Resolved:**

```json
{
  "status": "resolved",
  "payload": {
    "columns": ["CONTENT_ID", "MAIN_TITLE", "SHOW_TITLE", "ASSET_CURRENT_STATUS", "TYPE", "CNTY_CD"],
    "filters": [
      { "key": "TYPE", "type": "filter", "values": ["EPISODE"] },
      { "key": "SHOW_TITLE", "type": "search", "values": ["Mirzapur"] },
      { "key": "ASSET_CURRENT_STATUS", "type": "filter", "values": ["Ready For QC"] }
    ],
    "pagination": { "limit": 100, "offset": 0 }
  },
  "human_summary": "Episodes of Mirzapur with status Ready For QC"
}
```

**Response — Ambiguous:**

```json
{
  "status": "ambiguous",
  "question": "Which season of Mirzapur are you looking for?",
  "options": ["Season 1", "Season 2", "Season 3", "All seasons"],
  "allow_custom": true,
  "conversation_history": [
    { "role": "user", "content": "Show me Mirzapur episodes" },
    { "role": "assistant", "content": "Which season of Mirzapur are you looking for?" }
  ]
}
```

When `allow_custom` is `false`, the options list is exhaustive (e.g. content types, statuses) and the UI should show chips only. When `true`, show chips + a free text input.

On the operator's next message, send the returned `conversation_history` back in the next `/ai/resolve` request so the service has full context.

**Response — Error:**

```json
{
  "status": "error",
  "message": "This query is not related to content management."
}
```

---

### `POST /ai/execute`

Forwards a confirmed filter payload to the Java backend and returns the raw response.

**Request body:**

```json
{
  "payload": {
    "columns": ["CONTENT_ID", "MAIN_TITLE", "ASSET_CURRENT_STATUS"],
    "filters": [
      { "key": "TYPE", "type": "filter", "values": ["EPISODE"] }
    ],
    "pagination": { "limit": 100, "offset": 0 }
  }
}
```

**Response:** The raw JSON response from your Java backend, passed through as-is. Feed this directly to the existing Angular table component.

---

### `GET /ai/health`

```json
{
  "status": "ok",
  "adapter": "groq:llama-3.3-70b-versatile"
}
```

---

## LLM Adapters

### Groq (`groq_adapter.py`)

Uses the official Groq Python SDK. Set `LLM_ADAPTER=groq` and provide `GROQ_API_KEY`.

```python
# config in .env
LLM_ADAPTER=groq
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
```

### AWS Bedrock (`bedrock_adapter.py`)

Uses `boto3`. Authentication uses your standard AWS credential chain (IAM role → `~/.aws/credentials` → environment variables). No key needed in `.env` if running on EC2/ECS with an IAM role.

```python
LLM_ADAPTER=bedrock
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

### Custom Internal LLM (`custom_adapter.py`)

Generic HTTP POST adapter. Open `app/ai/adapters/custom_adapter.py` and adjust the `payload` shape and response parsing to match your internal LLM's API contract:

```python
# Adjust payload to match your LLM's API
payload = {
    "messages": [...],
    "max_tokens": max_tokens,
    "temperature": temperature,
}

# Adjust response parsing to match your LLM's response shape
content = (
    data.get("choices", [{}])[0].get("message", {}).get("content")  # OpenAI-compatible
    or data.get("response")    # common custom shape
    or data.get("output")
    or data.get("text")
)
```

```env
LLM_ADAPTER=custom
CUSTOM_LLM_URL=http://your-internal-llm/v1/chat
CUSTOM_LLM_API_KEY=your_key_if_required
```

---

## Adding a New Adapter

1. Create `app/ai/adapters/your_adapter.py`
2. Extend `AIClient` and implement `complete()` and `adapter_name`

```python
from app.ai.client import AIClient, Message

class YourAdapter(AIClient):

    @property
    def adapter_name(self) -> str:
        return "your_provider:model-name"

    async def complete(
        self,
        system_prompt: str,
        messages: list[Message],
        max_tokens: int = 1024,
        temperature: float = 0.1,
    ) -> str:
        # Call your LLM, return raw text string
        ...
```

3. Register it in `app/ai/factory.py`:

```python
if adapter == "your_provider":
    from app.ai.adapters.your_adapter import YourAdapter
    return YourAdapter()
```

4. Add config values to `config.py` and `.env.example`

That's it. No other files need to change.

---

## Filter Schema

`app/schema/filter_schema.py` is the **single source of truth** for everything the filter API supports. The system prompt is generated dynamically from this file — you never manually edit the prompt.

**When to update it:**

- New filter field added to the portal → add a `FilterKey` entry
- New status value added → update `valid_values` on `ASSET_CURRENT_STATUS`
- New content type added → update `valid_values` on `TYPE`
- New date range filter → add a `FilterKey` with `filter_type="dateRange"`

**Structure of a `FilterKey`:**

```python
FilterKey(
    key="ASSET_CURRENT_STATUS",      # Exact API key name
    filter_type="filter",            # "filter" | "search" | "dateRange"
    aliases=["status", "state", "qc status"],  # NL phrases that map to this key
    valid_values=["Released", "QC Fail", ...], # Empty list = free text
    description="Current workflow status",     # Used in prompt
    notes="Casing must match exactly",         # Optional extra instruction
)
```

**Filter types explained:**

| Type | Behaviour | Example keys |
|---|---|---|
| `filter` | Exact / enum match | `TYPE`, `ASSET_CURRENT_STATUS`, `CNTY_CD` |
| `search` | LIKE / contains match | `SHOW_TITLE`, `CONTENT_ID`, `STARRING` |
| `dateRange` | Two-value date window | `ASSET_INGESTION_RANGE`, `LICENSE_RANGE` |

---

## Running Tests

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run a specific test file
python -m pytest tests/test_intent_resolver.py -v

# Run a specific test
python -m pytest tests/test_validator.py::test_case_insensitive_value_correction -v
```

**Test coverage summary:**

| File | Tests | What's covered |
|---|---|---|
| `test_intent_resolver.py` | 18 | All response paths, multi-turn, validation, malformed JSON, markdown fences |
| `test_validator.py` | 14 | Unknown keys, invalid values, casing correction, type correction, SQL injection |
| `test_date_resolver.py` | 13 | All semantic tokens, passthrough, edge cases, case insensitivity |
| `test_system_prompt.py` | 8 | Prompt content, injected context, schema completeness |
| **Total** | **53** | |

All tests use `MockAIClient` — no real LLM calls, no network required. Tests run in ~0.5 seconds.

**Run live Groq test (requires key in `.env`):**

```bash
python live_test.py
```

---

## Integrating with Angular

The service is designed to slot into the existing Angular portal with minimal new code. Here is the integration contract:

### On component load

Fetch countries and providers from your existing APIs and hold them in the component:

```typescript
// Fetch once on init — same APIs you already use for filter dropdowns
this.countries = await this.assetService.getCountries();
this.providers = await this.assetService.getProviders();
```

### On operator query submit

```typescript
async onQuerySubmit(query: string) {
  const response = await this.aiService.resolve({
    query,
    conversation_history: this.conversationHistory,
    context: { countries: this.countries, providers: this.providers }
  });

  if (response.status === 'resolved') {
    // 1. Show human summary above table
    this.summary = response.human_summary;
    // 2. Execute and feed result to existing table component
    const data = await this.aiService.execute({ payload: response.payload });
    this.tableData = data;   // same format as existing media assets page
    this.showResultsModal = true;

  } else if (response.status === 'ambiguous') {
    // Render clarification chips
    this.clarificationQuestion = response.question;
    this.clarificationOptions = response.options;
    this.allowCustomInput = response.allow_custom;
    // Store updated history for next turn
    this.conversationHistory = response.conversation_history;

  } else if (response.status === 'error') {
    this.showError(response.message);
  }
}
```

### On chip click or custom answer

```typescript
onClarificationAnswer(answer: string) {
  // Answer becomes the next query — history is already tracked
  this.onQuerySubmit(answer);
}
```

### Reset on new session

```typescript
onNewQuery() {
  this.conversationHistory = [];
  this.summary = '';
}
```

---

## Troubleshooting

**`Connection error` when calling LLM**

Check that your LLM provider's domain is reachable from your environment. Some corporate networks or deployment environments block outbound requests — confirm with `curl https://api.groq.com`.

**`401 Unauthorized` from Groq**

Your `GROQ_API_KEY` in `.env` is missing or incorrect. Get a key from [console.groq.com](https://console.groq.com).

**LLM returning non-JSON or markdown-wrapped JSON**

The service handles this automatically (strips markdown fences, extracts JSON from mixed responses). If it still fails, increase the few-shot examples in `system_prompt.py` for your specific model.

**Hallucinated filter keys appearing in output**

The validator in `validator.py` catches and drops these. If you see frequent hallucinations on a specific key, add more aliases for that key in `filter_schema.py` — better alias coverage leads to better LLM classification.

**Date ranges coming back empty**

Check that `ASSET_INGESTION_RANGE` (or whichever date key) is correctly defined in `filter_schema.py` with `filter_type="dateRange"`. The date resolver only runs on `dateRange` type filters.

**Java backend returning 4xx**

The filter payload shape — specifically column names or filter key names — may not match what your Java backend expects. Cross-reference `filter_schema.py` key names against your MyBatis mapper's parameter names.

**Tests failing after schema update**

If you add new valid status values or content types, update `tests/test_validator.py` to cover the new values. The prompt tests (`test_system_prompt.py`) will automatically pick up schema changes since they test against the dynamically built prompt.
