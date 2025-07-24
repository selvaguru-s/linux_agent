import re
import streamlit as st
from agent.command_executor import execute_shell_command
from agent.llm_client import loop_mode
from agent.result_verifier import verify_result_with_llm
from prompt_clean import clean_command_output


def extract_command_from_llm_response(response: str) -> str:
    cleaned = re.sub(r"```(?:bash)?|```", "", response, flags=re.IGNORECASE).strip()

    for line in cleaned.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if " " in line or re.match(r"^[\w\-./]+$", line):
            return line

    return ""


def loop_streamlit(task: str, stdout: str, stderr: str, attempt: int = 1):
    st.subheader(f"🔁 Retry Attempt {attempt}")
    st.info("Retrying the task with help from the LLM...")

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

    st.write("🧠 Asking LLM for a new retry suggestion...")
    llm_response = loop_mode(retry_prompt).strip()
    suggested_command = extract_command_from_llm_response(llm_response)

    if not suggested_command:
        st.error("⚠️ Could not extract a valid shell command from the LLM response.")
        st.text("🔎 Full LLM Response:\n" + llm_response)
        return

    st.subheader("🤖 Suggested Retry Command")
    st.code(suggested_command, language="bash")

    run_retry = st.button(f"✅ Run Retry Command (Attempt {attempt})")
    if run_retry:
        with st.spinner("💻 Executing the retry command..."):
            result = execute_shell_command(suggested_command)

        st.subheader("🧾 Retry Result")
        st.json(result)

        verified = verify_result_with_llm(task, suggested_command, result["stdout"])
        if verified:
            st.success("✅ Retry Successful!")
            st.code(result["stdout"], language="bash")
        else:
            st.warning("❌ Retry Failed.")
            st.code(result["stdout"] or result["stderr"], language="bash")

            # Recursive retry (optional)
            retry_again = st.button(f"🔁 Retry Again (Attempt {attempt + 1})")
            if retry_again:
                loop_streamlit(task, result["stdout"], result["stderr"], attempt + 1)
