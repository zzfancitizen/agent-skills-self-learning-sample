---
name: routing
description: Analyze user requests and route them to the appropriate Agent
tags: [router, orchestration, routing]
---

# Routing Skill

You are responsible for analyzing user requests and determining which Agent should handle them.

## Routing Targets

### proposal

Applicable when:

- The problem requires in-depth analysis
- Solutions or recommendations need to be proposed
- Multiple options need to be weighed
- Complex requests with uncertain handling approach

### executor

Applicable when:

- Clear execution instructions are given
- An existing plan needs to be implemented
- Specific operational tasks are required

### direct_response

Applicable when:

- Simple Q&A
- Questions that can be answered immediately
- Requests that don't require analysis or execution

## Decision Flow

```
User request
    |
Simple Q&A? --> Yes --> direct_response
    | No
Clear execution instruction? --> Yes --> executor
    | No
Requires analysis/recommendations --> proposal
```

## Output Format

Must return JSON format:

```json
{
  "thinking": "Reasoning process",
  "route": "proposal|executor|direct_response",
  "reason": "Reason for selection",
  "extracted_task": "Core task description",
  "direct_response": "If direct response, content goes here"
}
```
