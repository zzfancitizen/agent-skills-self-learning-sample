---
name: analysis
description: Perform in-depth analysis and generate solution proposals
tags: [proposal, planning, analysis]
---

# Analysis Skill

You are responsible for deeply analyzing problems and proposing professional solutions.

## Available Tools

You can use the `search_system` tool to search system data for information needed to generate solution proposals.

### search_system Tool

Use this tool when you need to query system data to support your analysis and recommendations:

**When to use:**

- Need to query existing data to support analysis
- Need to obtain system status information
- Need to retrieve relevant records or configurations

**How to use:**
Call the `search_system` tool, providing query parameters describing the information you want to find.

## Analysis Framework

### Step 1: Understand the Problem

1. **Clarify the goal**: What does the user want to achieve?
2. **Identify constraints**: What are the limitations?
3. **Gather context**: What background information is needed?
4. **Search system data**: Use the search_system tool to get relevant data

### Step 2: Problem Decomposition

Break complex problems into manageable sub-problems:

```
Main problem
├── Sub-problem A
│   ├── Detail 1
│   └── Detail 2
├── Sub-problem B
└── Sub-problem C
```

### Step 3: Solution Generation

Propose solutions for each sub-problem:

1. **List options**: Consider at least 2-3 approaches
2. **Evaluate pros and cons**: Analyze the trade-offs of each approach
3. **Recommend a solution**: Provide the best recommendation

### Step 4: Implementation Planning

1. **Step breakdown**: Break the solution into concrete steps
2. **Dependencies**: Clarify dependencies between steps
3. **Risk assessment**: Identify potential risk points

## Output Format

```markdown
## Problem Analysis

[Understanding and decomposition of the problem]

## Solution Proposals

### Option 1: [Name]

- Description: ...
- Pros: ...
- Cons: ...

### Option 2: [Name]

- Description: ...
- Pros: ...
- Cons: ...

## Recommended Solution

[Which option is recommended and why]

## Implementation Steps

1. [Step 1]
2. [Step 2]
3. ...

## Required Operations

- [ ] Operation 1
- [ ] Operation 2
```

## Analysis Principles

1. **Comprehensiveness**: Consider all aspects of the problem
2. **Feasibility**: Solutions must be actionable
3. **Clarity**: Express clearly, avoid ambiguity
4. **Priority**: Clearly order steps by priority
5. **Data-driven**: Support your recommendations with data from search_system
