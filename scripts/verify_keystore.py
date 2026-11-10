import subprocess
import os

env = {}
with open(".env") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip("\"'").strip()

expected = env.get("DEPLOYER_ADDRESS", "").lower()

try:
    passfile = os.path.expanduser("~/.foundry/.halfway-pass")
    res = subprocess.run(
        ["/home/gaurav/.foundry/bin/cast", "wallet", "address", "--account", "deployer", "--password-file", passfile],
        capture_output=True, text=True, check=True
    )
    actual = res.stdout.strip().lower()
    print("Keystore 'deployer' matches DEPLOYER_ADDRESS:", actual == expected)
except Exception as e:
    print("Keystore check error:", e)
