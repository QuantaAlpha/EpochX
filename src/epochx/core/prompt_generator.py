"""Prompt generator for task execution."""

from __future__ import annotations

from pathlib import Path

from epochx.core.task import OutputType, Task, WorkspaceInfo


def generate_prompt(task: Task, ws_info: WorkspaceInfo) -> str:
    """Generate a standardized markdown prompt for an agent.

    Sections:
    - Task ID
    - Instructions
    - Workspace path
    - Environment Commands (SSH if docker, direct if host)
    - Available Tools
    - Output instructions (based on OutputType)
    - When Done
    """
    sections: list[str] = []

    # Header
    sections.append(f"# Task: {task.id}\n")

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

    # When Done
    sections.append("## When Done\n")
    sections.append(
        f"Run the following command to collect your output:\n"
    )
    sections.append(f"```bash")
    sections.append(f"epochx bench collect {task.id}")
    sections.append(f"```")

    return "\n".join(sections)


def write_prompt(task: Task, ws_info: WorkspaceInfo) -> Path:
    """Generate prompt and write to workspace/.epochx/prompt.md."""
    content = generate_prompt(task, ws_info)
    prompt_path = Path(ws_info.path) / ".epochx" / "prompt.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(content)
    return prompt_path
