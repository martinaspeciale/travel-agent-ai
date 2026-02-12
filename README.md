# AI Travel Architect

> **An autonomous AI agent for travel planning, built following the principles of "Agentic AI: From Architecture to Orchestration".**

This project implements a **stateful graph-based agent workflow** powered by *LangGraph*, designed to orchestrate complex decision-making through a *persistent shared state*. Unlike linear systems, this architecture enables *Self-Correction Loops* between Planning and Critic nodes, real-world *grounding* via external APIs, and full *trajectory observability* through a custom tracing layer.

---

## Theoretical Architecture vs. Implementation

This project is the implementation counterpart of the course slides. The table below reflects the **current runtime architecture**.

| Slide concept | In this project |
| :--- | :--- |
| **Stateful orchestration** | LangGraph workflow with persistent `TravelAgentState` shared across nodes ([`app/graph.py`](./app/graph.py), [`app/core/state.py`](./app/core/state.py)). |
| **Intent routing** | `ROUTER` infers travel style and normalizes intent before planning ([`app/engine/nodes.py`](./app/engine/nodes.py)). |
| **Tool-grounded action space** | `FLIGHT_SEARCH` uses SerpApi + local IATA seed; `FINDER` validates places via Google Maps ([`app/tools/search.py`](./app/tools/search.py), [`app/tools/maps.py`](./app/tools/maps.py), [`app/data/cities_airports_seed.csv`](./app/data/cities_airports_seed.csv)). |
| **Planning under constraints** | `PLANNER` drafts itinerary conditioned on destination, dates, budget, and companion profile ([`app/engine/prompts.py`](./app/engine/prompts.py)). |
| **Post-action verification** | `FINDER` rewrites places as verified/non-verified based on tool responses ([`app/engine/nodes.py`](./app/engine/nodes.py)). |
| **Confidence as control signal** | `CONFIDENCE` computes score from verified-place ratio; this controls HITL routing ([`app/engine/nodes.py`](./app/engine/nodes.py), [`app/graph.py`](./app/graph.py)). |
| **Human-in-the-Loop gating** | If confidence `< 0.7`, `ASK_HUMAN` can approve continuation or force re-planning ([`app/graph.py`](./app/graph.py)). |
| **Self-correction loop** | `CRITIC` can reject and return feedback; planner retries up to max attempts, then `FAILURE_HANDLER` ([`app/graph.py`](./app/graph.py)). |
| **Artifact-oriented output** | Final state is published as terminal summary + HTML + DOCX ([`app/tools/publisher.py`](./app/tools/publisher.py)). |
| **Observability** | Structured logs track thought/action/tool/result events for each node ([`app/core/logger.py`](./app/core/logger.py)). |

---

## Key Features

* **Date-first planning flow:** Departure is required, return is optional; trip length is auto-derived from valid dates or requested explicitly.
* **Flight proposal loop:** SerpApi + local IATA seed resolve routes and suggest best outbound/return options with user confirmation.
* **Planner-Critic retry loop:** The planner drafts, the critic validates feasibility, and rejected plans are retried with feedback (up to max attempts).
* **Deterministic confidence gate:** Reliability is computed from verified-place ratio after Google Maps grounding, then used to trigger HITL (`< 0.7`).
* **Real-world grounding:** Google Maps Places validation reduces location hallucinations (address/rating verification).
* **Artifact publishing:** Final approved results are exported as terminal summary, **HTML**, and **DOCX** reports.
* **Observability:** Structured, color-coded logs expose node actions, tool calls, and decision transitions.

---

## Installation and Setup

### 1. Clone the repository
```bash
git clone https://github.com/martinaspeciale/travel-agent-ai.git
cd travel-agent-ai
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Keys
Create a `.env` file in the project root and add your keys:
```env
# Required
GROQ_API_KEY=gsk_...
GOOGLE_MAPS_API_KEY=AIza...
SERPAPI_API_KEY=...

# Optional
# MISTRAL_API_KEY=... (Optional fallback)
```
API keys used to run the agent can be found here:
* **Groq API:** [console.groq.com](https://console.groq.com/keys)
* **Google Maps API:** [console.cloud.google.com](https://console.cloud.google.com/google/maps-apis/credentials)
* **SerpApi:** [serpapi.com](https://serpapi.com/)
* **Mistral API:** [console.mistral.ai](https://console.mistral.ai/api-keys/)

---

## Usage

Run the agent from the terminal using the main entry point:

```bash
python main.py
```

Follow the on-screen instructions, entering:
1.  **Destination** 
2.  **Interests** 
3.  **Total Budget (EUR)**
4.  **Travelers**
5.  **Flight origin (optional)**
6.  **Departure date (required, format `YYYY-MM-DD`)**
7.  **Return date (optional, format `YYYY-MM-DD`)**

`days` is derived automatically when both dates are valid; otherwise it is requested explicitly.

The agent will start the reasoning process (displayed in logs) and eventually generate:
1.  A detailed itinerary in the terminal.
2.  An HTML file in the project folder.
3.  A Word Document (.docx) 

---

## Graph Flow (Visual)

```text
INIT
  |
  v
ROUTER
  |
  v
FLIGHT_SEARCH
  |
  v
PLANNER
  |
  v
FINDER (Google Maps place validation)
  |
  v
CONFIDENCE (post-verification)
  | \
  |  \-- if low confidence --> ASK_HUMAN
  |                                | 
  |                                +-- approve --> CRITIC
  |                                +-- reject  --> PLANNER
  v
CRITIC
  | \
  |  \-- if approved --> PUBLISHER --> END
  |
  \-- if rejected --> PLANNER (retry up to 3) --> FAILURE_HANDLER --> END
```

## Project Structure

```text
travel-agent-ai/
├── main.py             # Application Entry Point
├── app/
│   ├── graph.py        # Orchestrator (LangGraph Workflow)
│   ├── core/           # Infrastructure Layer
│   │   ├── state.py    # Memory Definition (TypedDict)
│   │   ├── model.py    # LLM Configuration
│   │   ├── logger.py   # Observability System
│   │   └── utils.py    # Shared Utilities
│   ├── engine/         # Cognitive Layer
│   │   ├── nodes.py    # Decision Logic (Router, Planner, Critic)
│   │   └── prompts.py  # System Prompts
│   ├── tools/          # Interface Layer
│   │   ├── maps.py     # Google Maps API Wrapper
│   │   ├── search.py   # SerpApi Google Flights Wrapper + IATA resolution
│   │   └── publisher.py# Report Generator (HTML & DOCX)
│   └── data/
│       └── cities_airports_seed.csv  # Local city->IATA seed used for flight normalization
├── requirements.txt    # Python Dependencies
└── .env                # Environment Variables (API Keys)
```

---

## Course Slides

An integral part of this course project was preparing and evolving the slide material alongside the implementation.

* **Baseline deck:** [`slides/agentic-ai-seai-v0.tex`](./slides/agentic-ai-seai-v0.tex)
* **Enhanced course deck:** [`slides/agentic-ai-seai.tex`](./slides/agentic-ai-seai.tex)
* **Project deep dive deck:** [`slides/travel-agent-ai-project.tex`](./slides/travel-agent-ai-project.tex)
    
