# AI Travel Architect

> **An autonomous AI agent for travel planning, built following the principles of "Agentic AI: From Architecture to Orchestration".**

This project implements a **Multi-Step Reasoning** architecture using **LangGraph** to orchestrate a complex cognitive flow (Router → Planner → Finder → Critic). It integrates **Llama 3** (via Groq) and the **Google Maps API** to generate real, navigable itineraries.

---

## Theoretical Architecture vs. Implementation

This project was developed as a practical case study based on concepts covered in the **SEAI - Agentic AI** course. Below is the mapping between the theoretical concepts (Slides) and the codebase:

| Theoretical Concept (Slide) | Description | Code Implementation |
| :--- | :--- | :--- |
| **Anatomy of an Agent** (Slide 4) | The agent is a system composed of Brain (LLM), Memory, Tools, and Planning. | [**`nodes.py`**](./app/engine/nodes.py) (Brain), [**`state.py`**](./app/core/state.py) (Memory), [**`maps.py`**](./app/tools/maps.py) (Tools). |
| **Cognitive Architectures: Tree of Thoughts** (Slide 5) | Generating multiple options (A, B, C) and evaluating them before selection. | [**`nodes.py`**](./app/engine/nodes.py) (using [**`prompts.py`**](./app/engine/prompts.py)) generates 3 drafts and selects the best one. |
| **Memory & State Management** (Slide 7, 16) | Maintaining context across steps (User input, drafts, feedback). | [**`state.py`**](./app/core/state.py) defines the `TravelAgentState` (TypedDict) which persists data in the graph. |
| **Tool Use & Function Calling** (Slide 8) | Ability to act in the real world via deterministic APIs. | [**`maps.py`**](./app/tools/maps.py) integrates Google Maps API to fetch real places, addresses, and ratings. |
| **The Artifact** (Slide 14) | The output is not just text, but a structured and usable object. | [**`publisher.py`**](./app/tools/publisher.py) generates an **HTML Report** with navigable links and a visual layout. |
| **Resilience & Self-Correction** (Slide 17) | Error handling and feedback loops if the result is invalid. | [**`graph.py`**](./app/graph.py) (Critic loop) and [**`utils.py`**](./app/core/utils.py) (robust JSON parsing). |
| **Observability: "The Kitchen"** (Slide 18-19) | Monitoring the "thought process" (Reasoning) vs. Action. | [**`logger.py`**](./app/core/logger.py) tracks structured events (`THOUGHT` vs. `ACTION`) with color coding for debugging. |

---

## Key Features

* **Tree of Thoughts Planning:** Rejects the first output; generates alternatives based on travel style (Relax, Cultural, Adventure).
* **Critic-in-the-Loop:** A "Critic" node evaluates logistics (distances, timing) and rejects impossible itineraries, forcing the Planner to retry.
* **Real-World Data:** Uses Google Maps Places API to find real addresses, ratings, and reviews (preventing location hallucinations).
* **Structured Artifacts:** Automatically generates a `trip_destination.html` file with a visual itinerary and direct Google Maps links.
* **Observability:** Real-time color-coded terminal logs show exactly what the AI is "thinking" and when it is using a tool.

---

## Installation and Setup

### 1. Clone the repository
```bash
git clone git clone https://github.com/martinaspeciale/travel-agent-ai.git
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
# MISTRAL_API_KEY=... (Optional fallback)
```
API keys used to run the agent can be found here:
* **Groq API:** [console.groq.com](https://console.groq.com/keys)
* **Google Maps API:** [console.cloud.google.com](https://console.cloud.google.com/google/maps-apis/credentials)
* **Mistral AI:** [console.mistral.ai](https://console.mistral.ai/api-keys/)

---

## Usage

Run the agent from the terminal using the main entry point:

```bash
python main.py
```

Follow the on-screen instructions:
1.  Enter **Destination** (e.g., "Tokyo").
2.  Enter **Days** (e.g., "3").
3.  Enter **Interests** (e.g., "Anime, Sushi, Ancient Temples").

The agent will start the reasoning process (displayed in logs) and eventually generate:
1.  A detailed itinerary in the terminal.
2.  An HTML file in the project folder.

---

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
│   └── tools/          # Interface Layer
│       ├── maps.py     # Google Maps API Wrapper
│       └── publisher.py# HTML Report Generator
├── requirements.txt    # Python Dependencies
└── .env                # Environment Variables (API Keys)
```

---

## Reference Material

The architectural decisions, patterns, and observability pillars implemented in this project are based on the following lecture notes:

* 📄 **[Agentic AI: From Architecture to Orchestration and Quality](./Agentic%20AI%20-%20SEAI.pdf)**
    * *Author:* prof. Marco Cococcioni 
    
