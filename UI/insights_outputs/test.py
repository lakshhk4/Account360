import re

def process_markdown(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    processed_lines = ["<!---\n\n"]  # Add `<!---` at the very top
    
    # Combine lines where question number and text are on different lines
    combined_lines = []
    i = 0
    while i < len(lines):
        if re.match(r"### Question \d+:\n", lines[i]) and i + 1 < len(lines):
            combined_lines.append(re.sub(r"### Question (\d+):\n", r"### Question \1: ", lines[i]) + lines[i + 1])
            i += 2
        else:
            combined_lines.append(lines[i])
            i += 1
    
    processed_lines.extend(combined_lines)

    with open(file_path, 'w') as file:
        file.writelines(processed_lines)
# Example usage:
file_path = '/Users/lakshhkhatri/Desktop/WiproProject/UI /insights_outputs/insights_workday.md'
process_markdown(file_path)
