# Dead Code Cleaner with CrewAI + FastMCP

This app provides an automated toolchain to detect and remove dead code, unused imports, and irrelevant comments from Python source files using CrewAI agents and FastMCP protocol.

### Agent Roles

- **Code Structure Analyzer**: Extracts imports, functions, comments.
- **Unused Function Detector**: Detects the functions that are dead in the code.
- **Unused Imports Detector**: Detects imports that are never invoked in the code.
- **Comment Relevance Analyzer**: Checks if comments are actually valuable.

### Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

Environment variables required:
Set OpenAI API Key in app.py

### Usage

Run the app using:

```bash
npx @modelcontextprotocol/inspector

Command: fastmcp
Arguments: run app.py:server
```
