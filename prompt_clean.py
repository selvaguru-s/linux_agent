import re

def clean_command_output(response: str) -> str:
    # Try to extract from a fenced code block first
    code_block = re.search(r"```(?:bash)?\s*(.*?)\s*```", response, re.DOTALL)
    if code_block:
        return code_block.group(1).strip()

    # Otherwise, remove markdown/explanation and find first valid command-looking line
    lines = response.strip().splitlines()
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Remove explanations or markdown
        if line.startswith("```") or line.lower().startswith("the single") or "command you need" in line.lower():
            continue
        # Simple heuristic: shell-like lines (start with command or $)
        if re.match(r'^([a-zA-Z0-9_/.\-]+|\$)', line):
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()
