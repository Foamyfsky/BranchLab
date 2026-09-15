# BranchLab — Observe, Infer, Intervene

BranchLab is a small research pilot for studying decisions in a network whose full state cannot be observed. The intended work is to define a transparent model, compare state inference with known ground truth, and test interventions under explicit assumptions.

## Research question

When we observe only part of a network's state, can we infer the hidden state and choose better interventions? When does this fail?

## Current capabilities

This repository is a Python package skeleton. It supports an editable local install and importing branchlab. It has no network model, observations, inference method, intervention logic, experiment, or results yet.

## Local setup and verification (PowerShell)

Use Python 3.11 or newer. On this computer, the Codex-bundled Python 3.12 executable is at the path below; replace it with your own Python executable if preferred. Run these commands from this directory:

    $Python = 'C:\Users\22246\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    & $Python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -e .
    .\.venv\Scripts\python.exe -c "import branchlab; print(branchlab.__name__)"
    .\.venv\Scripts\python.exe -m compileall -q src
    git status --short

The import command should print branchlab; compileall should exit successfully without output. After setup, select .venv\Scripts\python.exe as the Python interpreter in VS Code. The virtual environment and generated files are ignored by Git.
