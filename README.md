# CrewAI Multi-Agent Research System

Streamlit app for running a YAML-configured CrewAI research department with
sequential, hierarchical, and Flow-based orchestration. The app includes an
unreliable custom tool, retry handling, SQLite memory, execution stats, FlowState
visualization, and history review.

## Prerequisites

- Python 3.12 or 3.13. CrewAI does not currently support Python 3.14.
- OpenAI API key or OpenRouter API key.
- Serper.dev API key.

## Installation

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
```

If Python 3.12 is not installed, use Python 3.13 instead.

## Environment Setup

Create `.env` from `.env.example`:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=openai/gpt-3.5-turbo
SERPER_API_KEY=...
```

OpenAI is selected first when `OPENAI_API_KEY` is present. OpenRouter is used
when only `OPENROUTER_API_KEY` is available.

## Launch The App

```powershell
streamlit run app.py
```

Or with Make:

```powershell
make ui
```

In the app, enter a research topic, choose `sequential`, `hierarchical`, or
`flow`, then click **Run research**. Results are shown in agent output sections,
with a final document and a download button.

## Contradiction Experiment

`config/agents.yaml` gives the Researcher a source-citation backstory.
`config/tasks.yaml` defines the concrete expected output for each task. In
CrewAI, task `expected_output` is the run-specific instruction and should
dominate when it conflicts with broader persona text.

## Architecture Overview

- `app.py`: Streamlit entrypoint.
- `config/agents.yaml`: external agent roles, goals, backstories, and tool ids.
- `config/tasks.yaml`: external task prompts and expected outputs.
- `src/agents/factory.py`: constructs agents and attaches Serper plus the
  retry-wrapped unreliable tool.
- `src/ui/`: Streamlit components, stats panel, FlowState view, and history view.
- `src/workflows/`: sequential, hierarchical, and flow execution backends.
- `src/memory/manager.py`: SQLite memory in `data/memory.db`.

## Running Tests

```powershell
python -m pytest tests/ -v -p no:cacheprovider
mypy src/
flake8 src/ tests/
black --check src/ tests/
```
