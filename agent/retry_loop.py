import os
import re
from agent.command_executor import execute_shell_command
from agent.llm_client import loop_mode
from agent.result_verifier import verify_result_with_llm
from prompt_clean import clean_command_output


def extract_command_from_llm_response(response: str) -> str:
    """
    Extract the first valid-looking shell command from an LLM response.
    Ignores markdown formatting, comments, and empty lines.
    """
    # Remove markdown-style code blocks like ```bash or ```
    cleaned = re.sub(r"```(?:bash)?|```", "", response, flags=re.IGNORECASE).strip()

    for line in cleaned.splitlines():
        line = line.strip()
        if not line:
            continue  # skip empty lines
        if line.startswith("#"):
            continue  # skip comments
        if " " in line or re.match(r"^[\w\-./]+$", line):  # shell-like pattern
            return line

    return ""  # No valid command found


def loop(task: str, stdout: str, stderr: str, attempt: int = 1):
    print(f"\n🔁 Retry Attempt {attempt} for task: {task}")

    confirm = input("❓ Do you want to retry this task using the LLM? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❎ Retry aborted by user.")
        return

    # 🧠 Step 1: Build prompt for retry
    retry_prompt = f"""
You are a helpful assistant. The user initially requested this task:

TASK: {task}

The system attempted a shell command, but it did not complete the task successfully.

STDOUT from previous attempt:
{stdout}

STDERR from previous attempt:
{stderr}

This is now a RETRY stage. Please suggest a different or corrected shell command that may resolve the issue.

Respond ONLY with a shell command. No explanation, no formatting like ```bash.
"""



    # 🗣️ Step 2: Ask LLM for a new command
    llm_response = loop_mode(retry_prompt).strip()
    suggested_command = extract_command_from_llm_response(llm_response)
    print("Retry command",suggested_command)

    if not suggested_command:
        print("⚠️ Could not extract a valid shell command from the LLM response.")
        print("🔎 Full response was:\n", llm_response)
        return

    print(f"\n🤖 Suggested Command (Attempt {attempt}):\n{suggested_command}")

    # ✋ Optional user confirmation before executing
    confirm_run = input("💬 Do you want to run this command? (y/n): ").strip().lower()
    if confirm_run != 'y':
        print("⚠️ Command not executed. Aborting retry.")
        return

    # 🖥️ Step 3: Execute the new command
    result = execute_shell_command(suggested_command)

    # ✅ Step 4: Verify again
    if verify_result_with_llm(task, suggested_command, result["stdout"]):
        print("\n✅ Retry Successful:\n" + result["stdout"])
    else:
        print("\n❌ Retry Failed:\n" + (result["stdout"] or result["stderr"]))
        loop(task, result["stdout"], result["stderr"], attempt + 1)
