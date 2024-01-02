import subprocess, os

interpreter = "pypy" if "pypy" in os.environ["PATH"] else "python"

engine_process = subprocess.Popen(
    f"{interpreter} ../uci.py",
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
    shell=True,
)

while True:
    command = input().strip()
    engine_process.stdin.write(f"{command}\n")
    engine_process.stdin.flush()

    response = engine_process.stdout.readline().strip()
    while response != "Done":
        print(response)
        response = engine_process.stdout.readline().strip()
