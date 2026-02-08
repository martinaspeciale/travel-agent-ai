# Agentic AI — Slide Deck

## Files

- `agentic-ai-seai-v0.tex`  
  Original slide deck (**baseline**).

- `agentic-ai-seai.tex`  
  Revised and extended version.

---
## Baseline-to-Revised Slide Mapping

The table below provides a conceptual mapping from each baseline slide (v0) to its corresponding location in the revised slide deck.  
All baseline content is preserved; changes are limited to explicit fixes or extensions as documented below.

**Status legend**

- **Unchanged**: content preserved conceptually and structurally.
- **Clarified / Refined**: same concepts, improved precision or terminology.
- **Reinterpreted**: same pedagogical intent, different conceptual framing.
- **Extended**: new material not present in the baseline.


| Baseline slide (v0) | Corresponding slide(s) in revised deck | Status | Notes |
|--------------------|-----------------------------------------|--------|-------|
| Course title / motivation | Course title / motivation | Unchanged | Same high-level motivation and learning objectives; only layout and phrasing adjustments |
| What is an AI Agent? | What is an AI Agent? | Clarified (F5) | Explicitly frames the agent as a runtime decision-making system and delineates its execution-time scope |
| From LLMs to Agents | From LLMs to Agents | Unchanged | Original conceptual progression from single LLM calls to agentic workflows is preserved |
| Anatomy of an Agent | Anatomy of an Agent (revised) | Refined (F1, F4, F6) | Presents an explicit separation between decision policy, controller logic, memory, and tools within the agent architecture |
| The Brain (LLM) | Decision Policy (LLM) | Refined (F1, F6) | Specifies the LLM’s role as a decision policy responsible for reasoning and action proposal |
| Planning Module | Decision Policy (Reasoning / Planning behavior) | Reinterpreted (F4) | Frames planning as a form of policy behavior rather than as a standalone architectural component |
| Memory (State) | Memory, Observations, Environment State | Refined (F2) | Introduces explicit terminology distinguishing environment state, observations, and internal agent memory |
| Tools | Tools as Action Space | Refined (F3) | Describes tools as actions available to the agent through the environment interface |
| Tool-Augmented Agents | Tool-Augmented Agents | Clarified / Refined (F3, F4) | Existing concept, made explicit through structured interaction patterns |
| Agent Loop (implicit) | Explicit Agent Loop | Clarified / Refined (F5) | Implicit execution loop made explicit without changing semantics |
| Single-Agent Setting | Single-Agent Setting | Unchanged | Scope and assumptions remain unchanged |
| Examples / Use Cases | Examples / Use Cases | Unchanged | Same illustrative examples retained |
| Limitations | Limitations | Unchanged | Original limitations and scope preserved |
| Summary | Summary + Architecture Map | Extended (E10) | Adds an explicit mapping between architectural components and their responsibilities |
| — | MDP / POMDP grounding | New (E2) | Introduces formal sequential decision-making models as background |
| — | Belief and history | New (E3) | Extends the memory discussion with belief- and history-based interpretations |
| — | LangChain abstractions | New (E5) | Provides a framework-specific illustration of agent abstractions |
| — | Graph-based orchestration (LangGraph) | New (E6) | Demonstrates graph-based execution as a realization of controller logic |
| — | Model Context Protocol (MCP) | New (E7) | Introduces standardized interfaces for tool and context integration |
| — | Agent-to-Agent interaction (A2A) | New (E8) | Extends the discussion to multi-agent communication and coordination |
| — | Robustness and recovery | New (E9) | Introduces architectural mechanisms for retries, fallbacks, and error handling |

## 1:1 Mapping

| Baseline slide # | Revised slide # | Status | Notes |
|---:|---:|---|---|
| 1 | 1 | Clarified / Refined | Title page updated (layout/metadata only); no conceptual change |
| 2 | 2 | Unchanged | Agenda preserved |
| 3 | 3 | Unchanged | “Era of Agentic AI” content preserved |
| 4 | 8 | Clarified / Refined | “Anatomy of an Agent” refined to make policy–controller separation explicit (F1, F6); planning not treated as standalone module (F4) |
| 5 | 9 | Unchanged | “Cognitive Architectures” preserved (ReAct, CoT, ToT, Reflexion) |
| 6 | 10 | Clarified / Refined | “Planning Strategies” preserved; planning framed as policy behavior rather than architectural component (F4) |
| 7 | 11 | Unchanged | “Memory Systems” preserved |
| 8 | 15 | Unchanged | “Tool Use & Function Calling” workflow preserved |
| 9 | 16 | Reinterpreted | RAG reframed as a memory read-path rather than a read-only tool, preserving knowledge-augmentation intent (F2, F3) |
| 10 | 19 | Unchanged | “Architectural Anti-Patterns” preserved |
| 11 | 20 | Clarified / Refined | MAS scaling law wording refined; scope clarified without changing intent |
| 12 | 21 | Unchanged | Router pattern preserved |
| 13 | 22 | Unchanged | Hierarchical teams preserved |
| 14 | 23 | Unchanged | Sequential handoffs preserved |
| 15 | 24 | Clarified / Refined | Inter-agent communication risks clarified; framing aligned with agent–environment interaction (F6) |
| 16 | 25 | Unchanged | Orchestration state management preserved (checkpointing, “time travel”) |
| 17 | 26 | Unchanged | Resilience & error recovery preserved (validation node, circuit breakers, critic pattern) |
| 18 | 27 | Unchanged | Observability introduction preserved (kitchen analogy; three pillars) |
| 19 | 28 | Clarified / Refined | Logging slide refined to avoid raw chain-of-thought exposure; observability intent preserved (F6) |
| 20 | 29 | Unchanged | Tracing slide preserved (OpenTelemetry, spans, root-cause analysis) |
| 21 | 30 | Unchanged | Metrics slide preserved (system vs quality metrics) |
| 22 | 32 | Unchanged | Outside-in evaluation framework preserved (four pillars; trajectory focus) |
| 23 | 33 | Unchanged | Black-box vs glass-box hierarchy preserved |
| 24 | 34 | Unchanged | Automated metrics slide preserved |
| 25 | 35 | Unchanged | LLM-as-a-Judge slide preserved |
| 26 | 36 | Unchanged | Agent-as-a-Judge slide preserved |
| 27 | 37 | Clarified / Refined | HITL slide refined to emphasize structured traces over raw reasoning artifacts (F6) |
| 28 | 38 | Clarified / Refined | Safety slide wording refined; threats and mitigations preserved (F6) |
| 29 | 50 | Unchanged | Agent Quality Flywheel preserved |
| 30 | 51 | Unchanged | Golden dataset concept preserved |
| 31 | 52 | Unchanged | Deployment strategies preserved |
| 32 | 53 | Unchanged | Future trends preserved |
| 33 | 54 | Unchanged | Conclusion and takeaways preserved |
| 34 | 58 | Unchanged | Acknowledgements preserved |


---

## Fixes 
Changes applied to the baseline version.

| ID | Topic | Location in v0 | Refinement Introduced | Motivation |
|----|------|----------------|----------------------|------------|
| F1 | Policy vs Controller distinction | *Anatomy of an Agent* | Made explicit the conceptual distinction between **Decision Policy (LLM)** and **Controller (runtime orchestration)**; clarified the role of reasoning traces (e.g. Chain-of-Thought) as internal policy behavior; noted that in graph-based frameworks (e.g. LangGraph), the graph structure and execution runtime can be interpreted as realizing the controller role | Improves conceptual precision by making explicit responsibility boundaries that are implicit in standard agent–environment formulations |
| F2 | State, observation, and memory | *Memory (State)* | Refined the terminology by distinguishing **environment state**, **observations**, and **agent memory** (short-term and long-term) | Aligns the presentation with MDP/POMDP terminology while preserving the original high-level intuition |
| F3 | Tools within the agent model | *Tools / Action Space* | Clarified the interpretation of tools as elements of the **action space**, invoked via the agent interface rather than as intrinsic model capabilities | Makes explicit the standard abstraction used in agent-based formulations |
| F4 | Planning and reasoning | *Planning / Reasoning* | Reinterpreted planning as a behavior of the decision policy, rather than as a separate architectural module | Maintains consistency with policy-based views of reasoning while retaining the pedagogical intent of the baseline |
| F5 | Agent execution vs training | *Agent definition / diagrams* | Explicitly distinguished the **runtime agent loop** from **training or fine-tuning procedures** | Prevents ambiguity between deployment-time behavior and learning-time processes |
| F6 | Allocation of responsibilities | *LLM role description* | Clarified which responsibilities are handled by the surrounding architecture (e.g. validation, retries, termination) versus those of the decision policy | Makes architectural assumptions explicit without altering the baseline narrative |

---

## Enhancements 
New content added beyond the baseline.

| ID | Topic | Location in revised version | Description |
|----|------|-----------------------------|-------------|
| E1 | Formal agent loop | Agent overview section | Explicit step-based formulation of the agent–environment interaction loop (observe → decide → act → update), made explicit for analytical clarity |
| E2 | MDP / POMDP grounding | Formal background slides | Explicit connection between agentic systems and classical MDP/POMDP models, including partial observability and history-based policies |
| E3 | Belief and history representations | Memory section | Introduction of belief- and history-based interpretations of agent memory in partially observable settings |
| E4 | Tool-augmented reasoning patterns | Reasoning slides | Discussion of structured interaction patterns such as tool-calling and ReAct-style loops as instances of policy behavior |
| E5 | LangChain-based agent abstractions | Architecture examples | Introduction of LangChain-style agent abstractions as a concrete realization of policy–controller separation |
| E6 | Graph-based orchestration (LangGraph) | Architecture examples | Presentation of graph-based execution models, where graph structure and runtime implement the controller and orchestrate the agent loop |
| E7 | Model Context Protocol (MCP) | Tooling and integration slides | Introduction of MCP as a standardized interface for tool and context integration in agentic systems |
| E8 | Agent-to-Agent (A2A) interaction | Multi-agent slides | Discussion of A2A communication patterns and coordination mechanisms as extensions beyond single-agent settings |
| E9 | Robustness and recovery mechanisms | Agent robustness slides | Discussion of retries, fallbacks, error handling, and control logic at the architectural level |
| E10 | Architectural responsibility mapping | Summary slides | Explicit summary mapping responsibilities across decision policy, controller, memory, and tools |

---

## Unmodified Content

All material not referenced in the **Fixes** or **Enhancements** tables is conceptually identical to the baseline version.
