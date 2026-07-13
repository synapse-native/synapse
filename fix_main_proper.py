# Read the file
with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix the indentation error by properly placing the no_std check
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    # Find the problematic section and fix it
    if "if stmt.ruta.startswith('std.'):" in line and i > 0 and "except FileNotFoundError:" in lines[i-1]:
        # This is the wrong location - skip the incorrectly placed code
        # Skip lines 474-482 (the misplaced no_std check)
        i += 9  # Skip to after the misplaced code
        new_lines.append(line)  # Add the original if stmt.ruta.startswith line
        i += 1
        new_lines.append(lines[i])  # Add the codigo = line
        i += 1
    else:
        new_lines.append(line)
        i += 1

# Write back
with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Fixed main.py by removing misplaced code')
