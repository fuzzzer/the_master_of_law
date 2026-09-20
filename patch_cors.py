import sys
path = 'backend/app/main.py'
with open(path, 'r') as f:
    content = f.read()

# Replace the CORSMiddleware block with a completely permissive one just to debug
new_cors = """
    print(f"CORS ORIGINS: {settings.cors_origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
"""
import re
content = re.sub(r'app\.add_middleware\(\s*CORSMiddleware,[^\)]+\)', new_cors.strip(), content)

with open(path, 'w') as f:
    f.write(content)
