---
name: verify-changes
description: Verify code changes do not break the project by running tests, linter checks, and import validation. Use after making any code changes, editing Python files, modifying imports, updating dependencies, or refactoring.
---

# Verify Changes

Run this verification workflow after every code change to ensure nothing is broken.

## Verification Checklist

Copy and track progress:

```
Verification:
- [ ] Step 1: Import check
- [ ] Step 2: Linter check
- [ ] Step 3: Test suite
```

## Step 1: Import Check

Run a quick import validation on all changed Python files:

```bash
uv run python -c "import src.main; import src.graph; import src.agents; import src.skills"
```

If this fails, there are broken imports. Fix them before continuing.

## Step 2: Linter Check

Use the `ReadLints` tool on all files you edited in this session. Fix any linter errors you introduced (ignore pre-existing ones).

## Step 3: Test Suite

Run the project test suite:

```bash
uv run src/main.py --test
```

**Expected output must include:**
- "Workflow created successfully"
- "Loaded 3 skills"
- "All tests passed"

If any step fails, fix the issue and re-run from that step.

## When to Run

Run this **every time** after:
- Editing any `.py` file under `src/`
- Adding, removing, or renaming files
- Changing `pyproject.toml` dependencies
- Modifying SKILL.md files in agent directories
