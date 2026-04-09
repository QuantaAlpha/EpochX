"""Prompt generator for task execution."""

from __future__ import annotations

from pathlib import Path

from epochx.core.task import OutputType, Task, WorkspaceInfo


def _skill_name(task: Task) -> str:
    """Generate a skill name from benchmark + task external_id.

    e.g. "swebench-verified-django-11099"
    """
    parts = task.external_id.replace("__", "-").replace("_", "-").lower()
    return f"{task.benchmark}-{parts}"


def generate_prompt(task: Task, ws_info: WorkspaceInfo) -> str:
    """Generate a standardized markdown prompt for an agent.

    Sections:
    - Task ID
    - Before You Start (search for existing skills)
    - Instructions
    - Workspace path
    - Environment Commands (SSH if docker, direct if host)
    - Available Tools
    - Output instructions (based on OutputType)
    - After Completion (distill & publish skill)
    - When Done
    """
    sections: list[str] = []

    skill_name = _skill_name(task)

    # Header
    sections.append(f"# Task: {task.id}\n")

    # Before You Start — search for skills
    sections.append("## Before You Start\n")
    sections.append(
        "Search the EpochX skill marketplace for existing solutions or strategies "
        "that might help with this task:\n"
    )
    sections.append("```bash")
    sections.append(f"epochx skill search \"{task.benchmark} {task.external_id}\"")
    sections.append("```\n")
    sections.append(
        "If relevant skills are found (score > 0.3), download and review them — "
        "especially the `references/` directory which may contain trajectories "
        "from previous successful attempts:\n"
    )
    sections.append("```bash")
    sections.append("epochx skill use <skill_id> --out ./skill-ref")
    sections.append("```\n")
    sections.append(
        "Use any helpful patterns, but solve the task independently. "
        "Do not blindly copy solutions."
    )
    sections.append("")

    # Instructions
    sections.append("## Instructions\n")
    sections.append(task.prompt)
    sections.append("")

    # Workspace
    sections.append("## Workspace\n")
    sections.append(f"Path: `{ws_info.path}`")
    sections.append("")

    # Environment Commands
    sections.append("## Environment Commands\n")
    if ws_info.ssh_host:
        sections.append(
            f"This task runs in a Docker container. Use SSH to execute commands:\n"
        )
        sections.append(f"```bash")
        sections.append(f"ssh {ws_info.ssh_host}")
        sections.append(f"```\n")
        workdir = ws_info.container_workdir or "/testbed"
        sections.append(f"- SSH host: `{ws_info.ssh_host}`")
        sections.append(f"- SSH port: `{ws_info.ssh_port}`")
        sections.append(f"- Working directory inside container: `{workdir}`")
    else:
        sections.append(
            "This task runs directly on the host. Execute commands in the workspace directory:\n"
        )
        sections.append(f"```bash")
        sections.append(f"cd {ws_info.path}")
        sections.append(f"```")
    sections.append("")

    # Available Tools
    if task.workspace.available_commands:
        sections.append("## Available Tools\n")
        for cmd in task.workspace.available_commands:
            sections.append(f"- `{cmd}`")
        sections.append("")

    # Output Instructions
    sections.append("## Output\n")
    output_type = task.output_spec.type
    if output_type == OutputType.GIT_DIFF:
        sections.append(
            "Submit your solution as a git diff. Make your changes and commit them."
        )
    elif output_type == OutputType.FILE_CONTENT:
        output_file = task.output_spec.output_file or "output.txt"
        sections.append(
            f"Write your answer to `{output_file}` in the workspace."
        )
    elif output_type == OutputType.ANSWER_STRING:
        output_file = task.output_spec.output_file or "answer.txt"
        fmt = task.output_spec.answer_format or "plain text"
        sections.append(
            f"Write your answer as {fmt} to `{output_file}` in the workspace."
        )
    elif output_type == OutputType.TRAJECTORY:
        sections.append(
            "Your execution trajectory will be recorded automatically."
        )
    elif output_type == OutputType.SNAPSHOT_DIFF:
        sections.append(
            "A snapshot of workspace changes will be collected automatically."
        )
    sections.append("")

    # Trajectory
    sections.append("## Trajectory (optional)\n")
    sections.append(
        "Your SSH commands are logged automatically. "
        "For richer trajectory data (reasoning, tool choices), "
        "append JSONL to `/.epochx/trajectory.jsonl` inside the container:\n"
    )
    sections.append("```json")
    sections.append('{"step":1,"type":"thought","content":"analyzing the issue..."}')
    sections.append('{"step":2,"type":"tool_call","tool_name":"grep","tool_input":"grep -r pattern .","tool_output":"..."}')
    sections.append("```")
    sections.append("")

    # After Completion — distill skill
    sections.append("## After Completion — Publish Skill\n")
    sections.append(
        "After solving the task, distill your approach into a reusable skill "
        "so future agents can learn from your experience.\n"
    )
    sections.append(
        "**Step 1.** Create the skill directory in the workspace:\n"
    )
    sections.append("```bash")
    sections.append(f"mkdir -p {ws_info.path}/skill/references")
    sections.append("```\n")
    sections.append(
        "**Step 2.** Write a SKILL.md summarizing your approach:\n"
    )
    sections.append("```bash")
    sections.append(f"cat > {ws_info.path}/skill/SKILL.md << 'SKILLEOF'")
    sections.append(f"# {skill_name}\n")
    sections.append(f"## Task\n{task.benchmark} / {task.external_id}\n")
    sections.append("## Approach\n(Describe your strategy: what you looked at, "
                     "what the root cause was, how you fixed it)\n")
    sections.append("## Key Insight\n(One-line takeaway that helps future agents)\n")
    sections.append("## Files Changed\n(List the files you modified and why)")
    sections.append("SKILLEOF")
    sections.append("```\n")
    sections.append(
        "**Step 3.** Copy the trajectory (auto-recorded) into the skill:\n"
    )
    sections.append("```bash")
    epochx_dir = f"{ws_info.path}/.epochx"
    sections.append(
        f"cp {epochx_dir}/trajectory_collected.json "
        f"{ws_info.path}/skill/references/trajectory.json 2>/dev/null || true"
    )
    sections.append(
        f"cp {epochx_dir}/output.txt "
        f"{ws_info.path}/skill/references/output.txt 2>/dev/null || true"
    )
    sections.append("```\n")
    sections.append(
        "**Step 4.** Publish the skill to EpochX:\n"
    )
    sections.append("```bash")
    sections.append(
        f"epochx skill submit --name \"{skill_name}\" "
        f"--dir {ws_info.path}/skill"
    )
    sections.append("```")
    sections.append("")

    # When Done
    sections.append("## When Done\n")
    sections.append(
        f"Run these commands in order:\n"
    )
    sections.append("```bash")
    sections.append(f"# 1. Collect your solution output")
    sections.append(f"epochx-bench collect {task.id}")
    sections.append(f"")
    sections.append(f"# 2. Then publish skill (after collect, so trajectory is available)")
    sections.append(f"# Follow the 'After Completion' steps above")
    sections.append(f"```")

    return "\n".join(sections)


def write_prompt(task: Task, ws_info: WorkspaceInfo) -> Path:
    """Generate prompt and write to workspace/.epochx/prompt.md."""
    content = generate_prompt(task, ws_info)
    prompt_path = Path(ws_info.path) / ".epochx" / "prompt.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(content)
    return prompt_path
