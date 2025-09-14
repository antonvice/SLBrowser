# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

SelfTUI is a modern Terminal User Interface application built with Python that combines web scraping, AI-powered content analysis, and beautiful terminal interfaces. It allows users to search the web, fetch webpage content, and get AI-generated summaries displayed in sleek, colorful terminal cards.

### Core Technology Stack
- **Textual**: Modern Python TUI framework for the interface
- **Rich**: Advanced terminal formatting and styling
- **Pydantic AI**: Structured AI outputs with streaming support
- **Google Gemini**: AI model for content analysis
- **httpx**: Async HTTP client for web requests
- **BeautifulSoup4**: HTML parsing and content extraction
- **DuckDuckGo Search**: Web search functionality

## Architecture

### Directory Structure
```
SelfTUI/
├── selftui/           # Main package
│   ├── __init__.py
│   ├── models.py      # Pydantic models and schemas
│   ├── ai.py         # Pydantic AI integration with Gemini
│   ├── web.py        # Web scraping and content fetching
│   ├── search.py     # Search functionality
│   ├── tui.py        # Main Textual application
│   └── styles.css    # TUI styling
├── tests/            # Test suite
├── TASKS/           # Development task tracking
└── requirements.txt # Dependencies
```

### Key Components

1. **Models (`models.py`)**: Pydantic models for structured data
   - `WebCard`: Represents parsed webpage data
   - `SearchResult`: Search result structure
   - `AIResponse`: Structured AI analysis output

2. **AI Integration (`ai.py`)**: Pydantic AI agents for content analysis
   - Uses structured outputs for reliable parsing
   - Implements streaming responses for real-time feedback
   - Handles Gemini API interactions with proper error handling

3. **Web Layer (`web.py`)**: Async web operations
   - Uses httpx for modern async HTTP requests
   - BeautifulSoup for content extraction
   - Retry logic and rate limiting

4. **TUI (`tui.py`)**: Main Textual application
   - Command-driven interface (`/key`, `/search`, `/open`)
   - Real-time streaming updates
   - Rich formatting for beautiful displays

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Running the Application
```bash
# Run from project root
python -m selftui

# Or after installation
selftui
```

### Development Tasks
```bash
# Run tests
pytest tests/ -v

# Type checking
mypy selftui/

# Linting
ruff check selftui/

# Formatting
ruff format selftui/
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=selftui --cov-report=html

# Run specific test file
pytest tests/test_ai.py -v

# Run tests with streaming output
pytest -s tests/test_streaming.py
```

## Coding Standards

### Type Annotations
- All functions must have complete type annotations
- Use `from __future__ import annotations` for forward references
- Prefer `list[T]` over `List[T]` (Python 3.9+)

### Pydantic AI Usage
- Use Pydantic AI agents for all AI interactions
- Implement structured outputs with proper validation
- Use streaming where possible for better UX
- Handle errors gracefully with fallback responses

### Async/Await
- Use async/await for all I/O operations
- Web requests, AI calls, and file operations should be async
- Use `asyncio.gather()` for concurrent operations

### Documentation
- All public functions require comprehensive docstrings
- Include examples for complex functions
- Document streaming behavior and async patterns

### Error Handling
- Use custom exceptions for domain-specific errors
- Log errors with structured logging
- Provide meaningful error messages to users
- Implement retry logic for network operations

## Task Management

Development tasks are tracked in the `TASKS/` directory:
- `00_BACKLOG.md`: High-level epics and features
- `01_TODO.md`: Current sprint tasks
- `99_DONE.md`: Completed tasks with dates

Mark tasks with `- [x]` when completed and move to appropriate sections.

## AI Integration Guidelines

### Pydantic AI Patterns
```python
# Use structured outputs
from pydantic_ai import Agent
from pydantic import BaseModel

class WebAnalysis(BaseModel):
    title: str
    summary: str
    key_points: list[str]

agent = Agent(model='gemini-pro', result_type=WebAnalysis)
result = await agent.run("Analyze this content...")
```

### Streaming Implementation
```python
# For real-time updates in TUI
async for chunk in agent.run_stream("query"):
    # Update TUI with partial results
    await update_display(chunk)
```

## TUI Design Principles

1. **Responsive Layout**: Works in various terminal sizes
2. **Keyboard Navigation**: Full keyboard accessibility
3. **Visual Hierarchy**: Clear information organization
4. **Real-time Updates**: Streaming responses for better UX
5. **Error States**: Graceful handling of failures

## Environment Variables

```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional
SELFTUI_LOG_LEVEL=INFO
SELFTUI_MAX_RESULTS=10
SELFTUI_REQUEST_TIMEOUT=30
```

## Common Patterns

### Adding New Models
1. Define in `models.py` with proper validation
2. Add corresponding AI agent in `ai.py`
3. Update TUI display logic
4. Write comprehensive tests

### Implementing Streaming
1. Use Pydantic AI streaming agents
2. Update TUI progressively
3. Handle partial data gracefully
4. Provide visual feedback to users

### Error Recovery
1. Implement exponential backoff for retries
2. Provide fallback content when AI fails
3. Log errors with context
4. Show user-friendly error messages

This architecture supports modern Python practices with async operations, structured AI outputs, and beautiful terminal interfaces.
