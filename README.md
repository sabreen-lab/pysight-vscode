# Pysight — AI Bug Predictor for Python

Pysight is a lightweight VS Code extension that predicts common Python runtime errors before you run your code. I built this because I wanted something simple that catches mistakes early without interrupting the flow of writing code.

## What It Does
- Detects issues like KeyErrors, infinite loops, unreachable code, and other common runtime problems using static analysis.
- Adds inline warnings directly inside VS Code.
- Uses a small AI explanation layer to describe why the issue might happen in a clear, beginner-friendly way.

## How It Works
Pysight parses your Python file using AST rules and flags potential issues. Each warning is paired with a one-line AI explanation generated through GPT-4o-mini. Everything runs automatically whenever you edit a Python file.

## Folder Structure
- `src/extension.ts` — VS Code extension logic  
- `analyzer/analyzer.py` — static analysis + AI explanations  
- `.env` — stores the API key ( i have not included in the repo for security reasons)

## Installation (Local Development)
1. Clone the repository  
2. Run `npm install`  
3. Add your API key to `.env` inside the `analyzer/` folder  
4. Run `npm run compile`  
5. Press F5 in VS Code to launch the extension host

## Why I Built This
I wanted something that actually helps beginners understand their errors instead of just showing red text. Pysight aims to make debugging feel less overwhelming and more like part of the learning process.
