import os
import sys
import subprocess

with open(".env") as f:
    env = dict(line.strip().split("=", 1) for line in f if "=" in line and not line.startswith("#"))

for k, v in env.items():
    env[k] = v.strip().strip("\"'").strip()

os.environ["PATH"] = f"/home/gaurav/.foundry/bin:{os.environ.get('PATH', '')}"

forge_cmd = ["/home/gaurav/.foundry/bin/forge"]
for arg in sys.argv[1:]:
    clean = arg.strip("\"'")
    if clean.startswith("$") and clean[1:] in env:
        forge_cmd.append(env[clean[1:]])
    elif clean in env:
        forge_cmd.append(env[clean])
    else:
        forge_cmd.append(clean)

res = subprocess.run(forge_cmd, env={**os.environ, **env})
sys.exit(res.returncode)
