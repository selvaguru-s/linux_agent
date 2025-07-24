import streamlit as st
from agent.context import collect_system_context
from agent.prompt_engineer import build_prompt
from agent.llm_client import get_command_from_llm
from agent.command_executor import execute_shell_command
from agent.result_summarizer import summarize_result
from agent.result_verifier import verify_result_with_llm
from agent.logger import log
from agent.retry_loop import loop_streamlit
from prompt_clean import clean_command_output
from agent.memory_manager import store_memory, retrieve_similar_tasks, is_continuation_semantic


def main():
    st.set_page_config(page_title="🧠 AI Shell Assistant", layout="centered")
    st.title("🤖 AI Shell Assistant")

    # 🧹 Clear state if reset is flagged
    if st.session_state.get("reset_flag"):
        for key in [
            "task", "context", "related_tasks", "memory_snippets",
            "command", "prompt", "parent_id", "reset_flag"
        ]:
            st.session_state.pop(key, None)

    # 📝 Input task
    task = st.text_input("📝 Enter the task you want to perform:")

    # 🚀 Run Task button
    if st.button("🚀 Run Task"):
        try:
            st.session_state["task"] = task
            st.info("🔄 Collecting system context...")
            st.session_state["context"] = collect_system_context()

            st.info("📚 Retrieving similar tasks from memory...")
            st.session_state["related_tasks"] = retrieve_similar_tasks(task)
            st.session_state["memory_snippets"] = "\n".join([
                f"- Task: {m['task']}\n  Result: {m['result'][:200].strip().replace('\n', ' ')}"
                for m in st.session_state["related_tasks"]
            ])

            if st.session_state["memory_snippets"]:
                st.subheader("📚 Recalling Relevant Past Tasks")
                st.text(st.session_state["memory_snippets"])

            parent = is_continuation_semantic(task)
            st.session_state["parent_id"] = parent["task"] if parent else None
            if st.session_state["parent_id"]:
                st.info(f"🔗 Continuing from previous task: {st.session_state['parent_id']}")

            st.info("✍️ Building prompt for LLM...")
            st.session_state["prompt"] = build_prompt(
                task,
                st.session_state["context"],
                st.session_state["memory_snippets"]
            )

            st.info("🤖 Getting command suggestion from LLM...")
            command = get_command_from_llm(st.session_state["prompt"])
            st.session_state["command"] = clean_command_output(command)

        except Exception as e:
            st.error("🚨 Fatal error in task processing.")
            st.exception(e)

    # 🧠 Show Suggested Shell Command
    if "command" in st.session_state:
        st.subheader("🧠 Suggested Shell Command")
        st.code(st.session_state["command"], language="bash")

        # ✅ Execute Command
        if st.button("✅ Execute Command"):
            st.write("🔧 Executing command...")

            try:
                result = execute_shell_command(st.session_state["command"])
                st.write("🔧 Command executed. Raw result:")
                st.json(result)

                st.write("🔍 Verifying result with LLM...")
                verified = verify_result_with_llm(
                    st.session_state["task"],
                    st.session_state["command"],
                    result["stdout"]
                )
                st.write("✅ Verified:", verified)

                if verified:
                    st.success("✅ Command executed successfully!")
                    st.code(result["stdout"], language="bash")

                    summary = summarize_result(
                        task=st.session_state["task"],
                        command=st.session_state["command"],
                        stdout=result["stdout"],
                        stderr=result["stderr"],
                        success=True
                    )
                    st.subheader("📋 Summary")
                    st.text(summary)
                else:
                    st.error("❌ Command failed verification.")
                    st.code(result["stdout"] or result["stderr"], language="bash")
                    loop_streamlit(
                        st.session_state["task"],
                        result["stdout"],
                        result["stderr"]
                    )
                    summary = "Execution failed."

                store_memory(
                    st.session_state["task"],
                    st.session_state["command"],
                    summary,
                    success=verified,
                    parent_task=st.session_state.get("parent_id")
                )

                log(
                    st.session_state["task"],
                    st.session_state["command"],
                    result,
                    verified
                )

            except Exception as e:
                st.error("🚨 Error during command execution.")
                st.exception(e)

    # 🔄 Reset button (safely triggers rerun)
    if st.button("🔄 Reset"):
        st.session_state["reset_flag"] = True
        st.rerun()


if __name__ == "__main__":
    main()
