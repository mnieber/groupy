"""The fake claude executable. Instead of asking Claude, it runs the scripted
steps of the request (shell commands, e.g. groupy callback, and file writes),
and records its arguments, the GROUPY_* env vars and the output of each
command. The scripts and the records are in the dir FAKE_CLAUDE_DIR."""

import json
import os
import subprocess
import sys
from pathlib import Path


def main():
    fake_dir = Path(os.environ["FAKE_CLAUDE_DIR"])
    request_id = os.environ["GROUPY_REQUEST_DIR"].split("/.groupy/requests/", 1)[1]
    file_name = request_id.replace("/", "__") + ".json"
    script_path = fake_dir / "scripts" / file_name
    if not script_path.exists():
        sys.stderr.write(f"There is no script for the request {request_id}")
        return 1
    script = json.loads(script_path.read_text())

    outputs = []
    for step in script["steps"]:
        if "write_file" in step:
            Path(step["write_file"]).write_text(step["text"])
            continue
        result = subprocess.run(step["run"], shell=True, capture_output=True, text=True)
        outputs.append(
            {
                "command": step["run"],
                "exit_code": result.returncode,
                "output": result.stdout + result.stderr,
            }
        )

    record = {
        "argv": sys.argv[1:],
        "env": {
            name: value
            for name, value in os.environ.items()
            if name.startswith("GROUPY_")
        },
        "outputs": outputs,
    }
    (fake_dir / "records").mkdir(exist_ok=True)
    (fake_dir / "records" / file_name).write_text(json.dumps(record))
    sys.stderr.write(script["stderr"])
    return script["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
