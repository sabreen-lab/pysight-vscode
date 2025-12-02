import * as vscode from "vscode";
import { spawn } from "child_process";
import path = require("path");

export function activate(context: vscode.ExtensionContext) {
  const diagnostics = vscode.languages.createDiagnosticCollection("pysight");
  context.subscriptions.push(diagnostics);

  // Windows uses "python", mac/Linux use "python3"
  const pythonCmd = process.platform === "win32" ? "python" : "python3";

  function analyze(doc: vscode.TextDocument) {
    // Only analyze Python files
    if (doc.languageId !== "python") return;

    const analyzerPath = path.join(
      context.extensionPath,
      "analyzer",
      "analyzer.py"
    );

    const child = spawn(pythonCmd, [analyzerPath, "--json"], {
      cwd: context.extensionPath,
    });

    let output = "";
    let errorOutput = "";

    child.stdout.on("data", (data: Buffer) => {
      output += data.toString();
    });

    child.stderr.on("data", (data: Buffer) => {
      errorOutput += data.toString();
    });

    child.on("close", () => {
      if (errorOutput && !output) {
        console.error("Analyzer error:", errorOutput);
        return;
      }

      let results: any[] = [];

      try {
        results = JSON.parse(output || "[]");
      } catch (err) {
        console.error("JSON parse error:", err);
        return;
      }

      const diagList: vscode.Diagnostic[] = results.map((item) => {
        const line = Math.max(0, (item.line ?? 1) - 1);
        const col = Math.max(0, (item.col ?? 1) - 1);

        const range = new vscode.Range(
          new vscode.Position(line, col),
          new vscode.Position(line, col + 1)
        );

        let severity = vscode.DiagnosticSeverity.Information;
        if (item.severity === "error") severity = vscode.DiagnosticSeverity.Error;
        else if (item.severity === "warning")
          severity = vscode.DiagnosticSeverity.Warning;

        const message = `${item.message} (confidence ${Math.round(
          (item.confidence ?? 0) * 100
        )}%)`;

        const diag = new vscode.Diagnostic(range, message, severity);
        diag.source = "Pysight";
        return diag;
      });

      diagnostics.set(doc.uri, diagList);
    });

    // Send the code text to the analyzer
    child.stdin.write(JSON.stringify({ text: doc.getText() }));
    child.stdin.end();
  }

  // Run analyze when:
  context.subscriptions.push(
    vscode.workspace.onDidOpenTextDocument(analyze)
  );

  context.subscriptions.push(
    vscode.workspace.onDidChangeTextDocument((e) => analyze(e.document))
  );

  context.subscriptions.push(
    vscode.workspace.onDidCloseTextDocument((doc) => diagnostics.delete(doc.uri))
  );

  // Analyze already opened docs
  vscode.workspace.textDocuments.forEach(analyze);
}

export function deactivate() {}
