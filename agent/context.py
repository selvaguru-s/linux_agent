import os
import getpass
import platform

def collect_system_context():
    return {
        "user": getpass.getuser(),
        "os": platform.system(),
        "os_version": platform.version(),
        #"env": dict(os.environ),
    }

# Collect the context
context = collect_system_context()

# Print OS and OS version
print(f"Operating System: {context['os']}")
print(f"OS Version: {context['os_version']}")
