# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project called "open-rag-search" that appears to be in early development phase. The project is intended to implement RAG (Retrieval-Augmented Generation) search functionality.

## Development Environment

- **Python Version**: 3.11+ (specified in pyproject.toml, .python-version)
- **Package Management**: Uses standard pip with pyproject.toml
- **Project Structure**: Currently minimal with just main.py as entry point

## Common Commands

### Running the Application
```bash
python main.py
```

### Package Management
```bash
# Install the project in development mode
pip install -e .

# Install dependencies (when they exist)
pip install -r requirements.txt  # or pip install .
```

### Development Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .
```

## Project Structure

- `main.py`: Entry point with basic "Hello World" functionality
- `pyproject.toml`: Project configuration and metadata
- `.python-version`: Specifies Python 3.11 requirement
- `.gitignore`: Standard Python gitignore patterns

## Architecture Notes

This project is currently in its initial setup phase. The main.py file contains only a basic hello world function, indicating this is a greenfield project ready for RAG search implementation.