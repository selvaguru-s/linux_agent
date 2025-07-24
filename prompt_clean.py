import re

def clean_command_output(response: str) -> str:
    """
    Extracts shell command(s) from a raw LLM response.
    Handles code blocks and cleans out explanation or markdown noise.
    """
    # 1. Try to extract fenced code block first (e.g., ```bash ... ```)
    code_block_match = re.search(r"```(?:bash)?\s*(.*?)\s*```", response, re.DOTALL | re.IGNORECASE)
    if code_block_match:
        return code_block_match.group(1).strip()

    # 2. Fallback: clean and filter lines
    cleaned_lines = []
    for line in response.strip().splitlines():
        line = line.strip()

        # Skip markdown or explanation lines
        if not line:
            continue
        if line.startswith("```") or line.startswith("#"):
            continue
        if re.match(r'^[A-Za-z\s]+:$', line):  # e.g., "Try this:" or "Command:"
            continue

        # Heuristic: plausible shell command line
        if re.match(r'^(\$?\s*[a-zA-Z0-9_\-./]+)(\s+.+)?$', line):
            cleaned_lines.append(re.sub(r'^\$\s*', '', line))  # Remove leading "$" if present

    return "\n".join(cleaned_lines).strip()
