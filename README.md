# Deal Memory Agent

An AI-powered sales assistant that uses **agent memory** to remember customers, deals, conversations, preferences, and previous interactions.

The goal is simple: instead of treating every conversation as a fresh interaction, the agent can retain useful information and recall it when making decisions about a customer or deal.

## What It Does

Deal Memory Agent helps sales teams work with customer and deal information through a conversational AI interface.

The agent can:

* Remember important customer and deal information
* Recall previously stored information during later interactions
* Use past context when responding to new questions
* Analyze deal-related information
* Maintain continuity across conversations
* Provide a more personalized sales-assistance experience

## Why Memory Matters

A normal AI assistant can answer questions from the current conversation, but it may lose important context when the conversation ends.

For example:

**Without memory:**

> User: What did the customer say about the budget?

The agent may not know if that information was mentioned in an earlier interaction.

**With memory:**

> User: What did the customer say about the budget?

The agent can retrieve the relevant information from previous interactions and use it to answer the question.

This project uses **Hindsight agent memory** to provide this persistent context.

## Architecture

```text
                    ┌─────────────────────┐
                    │       User          │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Agent / App      │
                    │      app.py         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    AI Engine        │
                    │   ai_engine.py      │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
          ┌──────────────────┐   ┌──────────────────┐
          │ Hindsight Memory │   │   Deal Data      │
          │  Retain / Recall │   │ deal_data.json   │
          └──────────────────┘   └──────────────────┘
                    │
                    ▼
          ┌──────────────────────┐
          │ Context-aware Agent  │
          │      Response       │
          └──────────────────────┘
```

## Hindsight Integration

Hindsight provides the memory layer for the agent.

The project uses the memory system to:

1. Store useful information from interactions.
2. Retrieve relevant information later.
3. Give the AI agent additional context.
4. Use historical information when generating responses.

This allows the agent to maintain continuity instead of relying only on the current conversation.

Learn more:

* [Hindsight GitHub Repository](https://github.com/vectorize-io/hindsight)
* [Hindsight Documentation](https://hindsight.vectorize.io/)
* [Vectorize Agent Memory](https://vectorize.io/what-is-agent-memory)

## Project Structure

```text
deal-memory-agent/
│
├── agent/
│   └── Agent-related modules
│
├── components/
│   └── Application UI components
│
├── data/
│   └── Project data
│
├── pages/
│   └── Application pages
│
├── .env.example
│   └── Example environment configuration
│
├── .gitignore
│   └── Files excluded from Git
│
├── agent.py
│   └── Agent logic
│
├── ai_engine.py
│   └── AI processing and response generation
│
├── app.py
│   └── Main application
│
├── deal_data.json
│   └── Deal/customer data used by the application
│
├── requirements.txt
│   └── Python dependencies
│
├── seed.py
│   └── Data initialization/seeding
│
└── voice.py
    └── Voice-related functionality
```

## Technologies Used

* Python
* AI/LLM-based agent
* Hindsight Agent Memory
* Streamlit/application UI
* JSON-based deal data
* Python environment management

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/JeyRam957/deal-memory-agent.git
cd deal-memory-agent
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file based on `.env.example`.

```text
HINDSIGHT_API_KEY=your_api_key
OPENAI_API_KEY=your_api_key
```

Do **not** commit your `.env` file to GitHub.

### 5. Initialize project data

If required by the application:

```powershell
python seed.py
```

### 6. Run the application

```powershell
streamlit run app.py
```

The application should then be available through the local Streamlit URL shown in the terminal.

## Example Workflow

A typical interaction looks like this:

```text
User
  │
  │  Provides customer/deal information
  ▼
Agent
  │
  │  Stores useful information
  ▼
Hindsight Memory
  │
  │  Later interaction
  ▼
Agent
  │
  │  Recalls relevant information
  ▼
Context-aware response
```

## Key Idea

The main idea behind this project is that **memory changes how an AI agent behaves over time**.

Instead of building an assistant that only responds to the current prompt, we build an assistant that can use information from previous interactions to provide more contextual responses.

## Future Improvements

Potential improvements include:

* More advanced deal analytics
* Better customer profiling
* Improved memory retrieval
* Automated follow-up recommendations
* CRM integration
* Voice-based sales interactions
* Multi-user support
* More detailed deal forecasting
* Production deployment

## Project Status

This project is actively being developed.

The current implementation focuses on demonstrating how persistent agent memory can be integrated into a sales/deal-oriented AI assistant.

## Author

**Jey Ram Vignan**

GitHub: [JeyRam957](https://github.com/JeyRam957)

## License

This project is intended for educational and experimental purposes.
