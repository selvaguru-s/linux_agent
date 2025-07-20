import json
import re
from agent.llm_client import chat_completion

def verify_result_with_llm(task: str, command: str, output: str) -> bool:
    prompt = f"""
You are a smart assistant. A user asked to perform the following task:

TASK: {task}

The system executed this shell command:
{command}

And got the following output:
{output}

Based on the task and output, did the command successfully complete the user's task?

Respond ONLY with a JSON object like one of the following:
{{"success": true}} or {{"success": false}}
Do not include any explanation or extra text.
"""

    response = chat_completion(prompt)
    raw = response.strip()

    # Remove Markdown code block wrappers like ```json ... ```
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\s*", "", raw)  # remove ```json or ```text
        raw = raw.rstrip("`").strip()

    try:
        result = json.loads(raw)
        return result.get("success", False)
    except Exception as e:
        print(f"⚠️ Could not parse LLM response as JSON. Error: {e}")
        print("LLM response:", response)
        return False
