# tau-bench — Benchmark Guide

> Multi-turn dialogue agent eval — airline/retail/telecom/banking domains.

## Overview

| Item | Value |
|------|-------|
| **Name** | `tau-bench` |
| **Runtime** | Host (no Docker) |
| **Tasks** | Varies (across 4 domains) |
| **Output Type** | `TRAJECTORY` |
| **Output File** | `.epochx/trajectory.json` |
| **Evaluation** | Reward function (simplified: validates JSON) |
| **Resource Profile** | `light` |

## Data Source

Tasks are loaded from:
```
benchmarks/tau-bench/repo/data/tau2/domains/{domain}/tasks.json
```

Domains:
- `airline` — Flight booking and management
- `retail` — Shopping and order handling
- `telecom` — Phone/internet service management
- `banking` — Account and transaction operations

## Task ID Format

Task IDs follow the pattern `{domain}-{index}`:
- `airline-0`, `airline-1`, ...
- `retail-0`, `retail-1`, ...
- `telecom-0`, `banking-5`, etc.

## Quick Start

```bash
# Start a specific task
epochx bench run tau-bench --task airline-0 --json

# Start first available
epochx bench run tau-bench --json
```

## Workspace After Setup

```
{workspace}/
├── .epochx/
│   ├── meta.json
│   ├── prompt.md          # Contains: domain, scenario, instructions, known/unknown info
│   └── trajectory.json    # ← WRITE YOUR DIALOGUE TRAJECTORY HERE
```

No data files are copied — this is an `API_ONLY` workspace type.

## How to Solve

1. **Read the prompt**: `cat {workspace}/.epochx/prompt.md`
   - Specifies the domain (airline/retail/telecom/banking)
   - Contains:
     - `reason_for_call`: Why the user is calling
     - `task_instructions`: What the agent should accomplish
     - `known_info`: Information the user already knows
     - `unknown_info`: Information the user doesn't have

2. **Simulate the dialogue**: Act as the customer service agent, handling the user's request

3. **Write the trajectory** as a JSON array:
   ```bash
   cat > {workspace}/.epochx/trajectory.json << 'EOF'
   [
     {
       "role": "user",
       "content": "Hi, I need to change my flight from NYC to LAX on March 15th."
     },
     {
       "role": "assistant",
       "content": "I'd be happy to help you change your flight. Could you please provide your booking reference number?"
     },
     {
       "role": "user",
       "content": "It's ABC123."
     },
     {
       "role": "assistant",
       "content": "Thank you. I found your booking. I can change your flight to March 15th. The new flight departs at 2:30 PM. Shall I proceed?"
     },
     {
       "role": "user",
       "content": "Yes, please."
     },
     {
       "role": "assistant",
       "content": "Done! Your flight has been changed. Your new confirmation number is XYZ789. Is there anything else I can help with?"
     }
   ]
   EOF
   ```

## Collect + Grade + Stop

```bash
epochx bench collect tau-bench/airline-0
epochx bench grade tau-bench/airline-0     # Validates JSON structure
epochx bench stop tau-bench/airline-0
```

## Trajectory Format

The trajectory must be valid JSON. Expected structure:

```json
[
  {"role": "user", "content": "..."},
  {"role": "assistant", "content": "..."},
  {"role": "user", "content": "..."},
  {"role": "assistant", "content": "..."}
]
```

Or a JSON object with conversation data — the evaluator accepts both forms.

## Task Metadata

Each task includes:
- `domain`: The service domain
- `task_index`: Position within the domain's task list

## Evaluation

- **Current**: Basic validation — checks that valid JSON was produced
- **Full eval** (TODO): Uses the `tau2` reward function framework at `benchmarks/tau-bench/repo/src/tau2/`

## Tips

- **No Docker needed**: This runs directly on the host — no container, no SSH
- **JSON must be valid**: The evaluator will reject malformed JSON
- **Multi-turn**: Produce a realistic multi-turn conversation, not a single response
- **Follow the scenario**: The prompt gives specific user context — stay in character
- **Handle unknown info**: The user may not know certain details — the agent should ask for or look up what's needed
