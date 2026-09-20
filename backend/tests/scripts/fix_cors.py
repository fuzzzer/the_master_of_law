with open('app/main.py', 'r') as f:
    lines = f.readlines()
with open('app/main.py', 'w') as f:
    for line in lines:
        if "allow_credentials=True," in line:
            f.write(line.replace("allow_credentials=True,", "allow_credentials=False,"))
        else:
            f.write(line)
