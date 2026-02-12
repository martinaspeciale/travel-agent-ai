# AI Travel Architect

> **An autonomous AI agent for travel planning, built following the principles of "Agentic AI: From Architecture to Orchestration".**

This project implements a **Stateful Multi-Agent Cognitive Architecture** powered by *LangGraph*, designed to orchestrate complex decision-making flows through a *persistent shared state*. Unlike linear systems, this architecture enables *Self-Correction Loops* between Planning and Critic nodes, ensuring real-world *grounding* via external APIs and full *trajectory observability* through a custom-built Tracing system.

---

## Theoretical Architecture vs. Implementation

This project was developed as a practical case study based on concepts covered in the **SEAI - Agentic AI** course. Below is the mapping between the theoretical concepts and the codebase:

| Theoretical Concept | Description | Code Implementation |
| :--- | :--- | :--- |
| **Anatomy of an Agent** | The agent is a system composed of Brain (LLM), Memory, Tools, and Planning. | [**`nodes.py`**](./app/engine/nodes.py) (Brain), [**`state.py`**](./app/core/state.py) (Memory), [**`maps.py`**](./app/tools/maps.py) (Tools). |
| **Cognitive Architectures: Planner** | Generates an itinerary proposal based on style, budget, and constraints. | [**`nodes.py`**](./app/engine/nodes.py) (using [**`prompts.py`**](./app/engine/prompts.py)) produces the initial itinerary proposal. |
| **Memory & State Management** | Maintaining context across steps (User input, drafts, feedback). | [**`state.py`**](./app/core/state.py) defines the `TravelAgentState` (TypedDict) which persists data in the graph. |
| **Tool Use & Function Calling** | Ability to act in the real world via deterministic APIs. | [**`maps.py`**](./app/tools/maps.py) integrates Google Maps API to fetch real places, addresses, and ratings. |
| **The Artifact** | The output is not just text, but a structured and usable object. | [**`publisher.py`**](./app/tools/publisher.py) generates professional **Word (.docx)** and **HTML** reports. |
| **Resilience & Self-Correction** | Error handling and feedback loops if the result is invalid. | [**`graph.py`**](./app/graph.py) (Critic loop) and [**`utils.py`**](./app/core/utils.py) (robust JSON parsing). |
| **Observability: "The Kitchen"** | Monitoring the "thought process" (Reasoning) vs. Action. | [**`logger.py`**](./app/core/logger.py) tracks structured events (`THOUGHT` vs. `ACTION`) with color coding for debugging. |
| **Grounding & Tools** | Using external APIs to anchor the agent to real-world facts (places, flights). | [**`maps.py`**](./app/tools/maps.py) uses Google Maps for place validation; [**`search.py`**](./app/tools/search.py) uses **SerpApi (Google Flights)** + local IATA seed for flight suggestions. |
| **Metacognition** | The agent evaluates confidence after place verification to reduce hallucinations. | [**`nodes.py`**](./app/engine/nodes.py) calculates a `confidence_score` post-Finder. |
| **Human-in-the-Loop (HITL)** | Manual intervention when the agent is uncertain. | [**`graph.py`**](./app/graph.py) implements an interruption point (`ask_human`) when confidence is `< 0.7`. |
| **Robustness** | Managing edge cases like extreme budgets, multipliers, or ambiguous inputs. | [**`utils.py`**](./app/core/utils.py) implements regex-based budget parsing (e.g., "100k", "1 milione"). |

---

## Key Features

* **Planner + Critic Loop:** Generates an itinerary and retries when constraints are not satisfied.
* **Flight Proposal Loop:** Searches outbound/return options via SerpApi, proposes best option, and asks user confirmation before proceeding.
* **Critic-in-the-Loop:** A "Critic" node evaluates logistics (distances, timing) and rejects impossible itineraries, forcing the Planner to retry.
* **Real-World Data:** Uses Google Maps Places API to find real addresses, ratings, and reviews (preventing location hallucinations).
* **Dual-Format Artifacts:** Automatically generates both a **Word Document (.docx)** for editing and an **HTML Report** with visual maps.
* **Observability:** Real-time color-coded terminal logs show exactly what the AI is "thinking" and when it is using a tool.

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
GROQ_API_KEY=gsk_...
GOOGLE_MAPS_API_KEY=AIza...
SERPAPI_API_KEY=...
# MISTRAL_API_KEY=... (Optional fallback)
# TAVILY_API_KEY=tvly-... (Optional / legacy helper)
```
API keys used to run the agent can be found here:
* **Groq API:** [console.groq.com](https://console.groq.com/keys)
* **Google Maps API:** [console.cloud.google.com](https://console.cloud.google.com/google/maps-apis/credentials)
* **SerpApi:** [serpapi.com](https://serpapi.com/)
* **Mistral API:** [console.mistral.ai](https://console.mistral.ai/api-keys/)
* **Tavily Search API (optional):** [app.tavily.com](https://app.tavily.com/home)

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
6.  **Departure date (required)**
7.  **Return date (optional)**

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

<!---

## Test Scenarios & Edge Cases

These scenarios are designed to stress-test the architecture and demonstrate the core pillars of **Robustness** and **Metacognition**.

### 1. The "Survival" Test (Extreme Budget)
* **Input:** `Venezia, 2 days, 30 EUR, Couple`
* **Purpose:** Verifies **Safety & Grounding**. 
* **Expected Behavior:** The **Critic** must reject expensive attractions (e.g., Doge's Palace) using real-time **Tavily** data. It forces the **Planner** to pivot toward free activities like the *Rialto Market* or walking tours to stay within the €15/day limit.

### 2. The "Ambiguity" Test (Human-in-the-Loop)
* **Input:** `An exotic place, 5 days, Medium, Solo`
* **Purpose:** Verifies **Metacognition & HITL**.
* **Expected Behavior:** Due to the missing destination, the agent assigns a `confidence_score < 0.7`. It triggers the `ask_human_node`, pausing the graph execution to ask the user for clarification before wasting API tokens.

### 3. The "Millionaire" Test (Robust Parsing)
* **Input:** `Dubai, 3 days, 100k, Luxury, Family`
* **Purpose:** Verifies **Robustness & Efficiency**.
* **Expected Behavior:** The `extract_budget_number` utility must correctly parse "100k" into `100000.0`. The system bypasses low-budget web searches (Efficiency) and focuses on high-end hospitality and exclusive experiences.

### 4. The "Teleportation" Test (Logical Reasoning)
* **Input:** `Tokyo and New York, 1 day, Luxury, Solo`
* **Purpose:** Verifies **Logical Consistency**.
* **Expected Behavior:** Even with an unlimited budget, the **Critic** must reject the itinerary. It identifies the physical impossibility of visiting both cities in 24 hours, demonstrating that the agent understands spatial and temporal constraints beyond simple text generation.
-->

---

## Reference Material

The architectural decisions, patterns, and observability pillars implemented in this project are based on the following lecture notes:

* 📄 **[Agentic AI: From Architecture to Orchestration and Quality](./Agentic%20AI%20-%20SEAI.pdf)**
    * *Author:* prof. Marco Cococcioni 
    
