import subprocess

engine_process = subprocess.Popen(
    "pypy D:/Users/Islam/Documents/CS/karlpy/uci.py",
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
    shell=True
)

while True:
    command = input().strip()
    engine_process.stdin.write(f"{command}\n")
    engine_process.stdin.flush()

    response = engine_process.stdout.readline().strip()
    while response != "Done":
        print(response)
        response = engine_process.stdout.readline().strip()
        