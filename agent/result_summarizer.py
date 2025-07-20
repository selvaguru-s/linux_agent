# agent/result_summarizer.py

from agent.llm_client import output_sum  # Make sure this is your LLM interface

def summarize_result(task: str, command: str, stdout: str, stderr: str, success: bool) -> str:
    prompt = f"""
You are a helpful terminal assistant. Summarize the result of the following shell command in a concise and human-readable form.

Task:
{task}

Command:
{command}

{"The command succeeded." if success else "The command failed."}

Output:
{stdout if success else stderr}

Summary:"""

    summary = output_sum(prompt)
    return summary.strip()
