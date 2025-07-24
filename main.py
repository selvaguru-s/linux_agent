
from agent.context import collect_system_context
from agent.prompt_engineer import build_prompt
from agent.llm_client import get_command_from_llm
from agent.command_executor import execute_shell_command
from agent.result_summarizer import summarize_result
from agent.result_verifier import verify_result_with_llm
from agent.logger import log
from agent.retry_loop import loop
from prompt_clean import clean_command_output
from agent.memory_manager import store_memory, retrieve_similar_tasks, is_continuation_semantic

def main():
    while True:
        task = input("📝 Enter the task you want to perform: ")
        if task.lower() in ('exit', 'quit'):
            print("👋 Exiting. Goodbye!")
            break

        # Step 1: Collect context
        context = collect_system_context()

        # Step 1.5: Memory + threading check
        related_tasks = retrieve_similar_tasks(task)
        memory_snippets = "\n".join([
            f"- Task: {m['task']}\n  Result: {m['result'][:200].strip().replace('\n', ' ')}"
            for m in related_tasks
        ])

        if memory_snippets:
            print("\n📚 Recalling relevant past tasks:\n", memory_snippets)

        # Check if this is a continuation of something
        parent = is_continuation_semantic(task)
        parent_id = parent["task"] if parent else None
        if parent_id:
            print(f"\n🔗 Continuing from previous task: {parent_id}")
        # Step 2: Prompt building
        prompt = build_prompt(task, context, memory_snippets)
        command = get_command_from_llm(prompt)

        print("\n🤖 Suggested Shell Command:")
        print(f"\n🔸 {command}\n")

        cleaned_command = clean_command_output(command)
        print("cleaned output :", cleaned_command)

        confirm = input("Do you want to execute this? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Aborted.")
            continue

        # Step 3: Execution
        result = execute_shell_command(cleaned_command)

        # Step 4: Verify result
        verified = verify_result_with_llm(task, cleaned_command, result["stdout"])

        if verified:
            print("\nstdout_output\n" + result["stdout"])

                    # Step 5: Summarize and store
            summary = summarize_result(
                task=task,
                command=cleaned_command,
                stdout=result["stdout"],
                stderr=result["stderr"],
                success=verified
            )
            print(("✅ Output:",summary))

        else:
            loop(task, result["stdout"], result["stderr"])
            print("\n❌ Error:\n" + (result["stdout"] or result["stderr"]))


        store_memory(task, cleaned_command, summary, success=verified, parent_task=parent_id)
        log(task, cleaned_command, result, verified)

if __name__ == "__main__":
    main()