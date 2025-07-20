import subprocess
import time

def execute_shell_command(command: str) -> dict:
    print(f"\n🚀 Executing: \033[1;36m{command}\033[0m\n")  # Cyan bold

    start_time = time.time()
    output_buffer = ""

    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1  # Line-buffered
        )

        for line in process.stdout:
            line = line.rstrip()
            output_buffer += line + "\n"
            print(line)

        process.wait()
        end_time = time.time()

        return {
            "success": process.returncode == 0,
            "returncode": process.returncode,
            "command": command,
            "stdout": output_buffer.strip(),
            "stderr": "",  # stderr merged into stdout
            "duration": round(end_time - start_time, 2)
        }

    except Exception as e:
        return {
            "success": False,
            "command": command,
            "stdout": output_buffer.strip(),
            "stderr": str(e),
            "returncode": -1,
            "duration": 0.0
        }
