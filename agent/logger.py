import datetime
from agent.config import CONFIG

def log(prompt: str, command: str, result: dict, success: bool):
    with open(CONFIG["LOG_FILE"], "a") as log_file:
        log_file.write(f"\n--- {datetime.datetime.now()} ---\n")
        log_file.write(f"Prompt: {prompt}\n")
        log_file.write(f"Command: {command}\n")
        log_file.write(f"Success: {success}\n")
        log_file.write(f"Output:\n{result['stdout']}\n")
        log_file.write(f"Error:\n{result['stderr']}\n")
