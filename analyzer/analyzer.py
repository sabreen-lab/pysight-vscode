#!/usr/bin/env python3
import ast, json, sys
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load API key from .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

diags = []


# -------------------------------------------------
# AI EXPLANATION FUNCTION
# -------------------------------------------------
def ai_explain(message):
    """
    Calls OpenAI GPT-4o-mini to generate a one-line explanation.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Explain Python runtime risks in one short, simple sentence."},
                {"role": "user", "content": f"Explain why this is risky: {message}"}
            ],
            max_tokens=40,
            temperature=0.3,
        )

        return response.choices[0].message.content.strip()

    except Exception:
        return "AI explanation unavailable."


# -------------------------------------------------
# COLLECT DIAGNOSTICS
# -------------------------------------------------
def add(line, col, msg, severity="warning", confidence=0.7):
    ai_msg = ai_explain(msg)
    diags.append({
        "line": line,
        "col": col,
        "severity": severity,
        "confidence": confidence,
        "message": f"{msg} — AI: {ai_msg}"
    })


# -------------------------------------------------
# READ CODE FROM stdin
# -------------------------------------------------
source = ""
try:
    payload = json.load(sys.stdin)
    source = payload.get("text", "")
except Exception:
    source = ""


# -------------------------------------------------
# PARSE CODE
# -------------------------------------------------
try:
    tree = ast.parse(source)
except SyntaxError as e:
    add(e.lineno or 1, e.offset or 1, f"SyntaxError: {e.msg}", "error", 0.99)
    print(json.dumps(diags))
    sys.exit(0)


# -------------------------------------------------
# AST RULES
# -------------------------------------------------

# 1. Detect d["x"] → possible KeyError
class DictAccessVisitor(ast.NodeVisitor):
    def visit_Subscript(self, node):
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            add(node.lineno, node.col_offset + 1,
                f"Possible KeyError: dictionary key '{node.slice.value}' may not exist",
                "warning", 0.55)
        self.generic_visit(node)


# 2. Detect while True without break → infinite loop
class WhileVisitor(ast.NodeVisitor):
    def visit_While(self, node):
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            has_break = any(isinstance(n, ast.Break) for n in ast.walk(node))
            if not has_break:
                add(node.lineno, node.col_offset + 1,
                    "Possible infinite loop: `while True` has no break",
                    "warning", 0.65)
        self.generic_visit(node)


# 3. Detect unreachable code after return
class ReturnVisitor(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        for i, stmt in enumerate(node.body[:-1]):
            if isinstance(stmt, ast.Return):
                next_stmt = node.body[i+1]
                add(next_stmt.lineno, next_stmt.col_offset + 1,
                    "Unreachable code: this will never run after return",
                    "info", 0.8)
        self.generic_visit(node)


# Run visitors
DictAccessVisitor().visit(tree)
WhileVisitor().visit(tree)
ReturnVisitor().visit(tree)


# -------------------------------------------------
# OUTPUT JSON EXPECTED BY VS CODE EXTENSION
# -------------------------------------------------
print(json.dumps(diags))
