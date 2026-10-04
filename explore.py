import os

base = r"c:\Users\abhishek\Downloads\ai-based soc"

# List key directories
print("Top-level items:")
for item in sorted(os.listdir(base)):
    full = os.path.join(base, item)
    if os.path.isdir(full):
        print("  [DIR] " + item)
    else:
        print("  [FILE] " + item)

print("\nBackend files:")
backend = os.path.join(base, "backend")
if os.path.isdir(backend):
    for root, dirs, files in os.walk(backend):
        for f in sorted(files)[:20]:
            print("  " + os.path.join(root, f))

print("\nFrontend files:")
frontend = os.path.join(base, "frontend")
if os.path.isdir(frontend):
    for root, dirs, files in os.walk(frontend):
        for f in sorted(files)[:20]:
            print("  " + os.path.join(root, f))