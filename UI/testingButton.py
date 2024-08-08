import time

# Sleep for 3 seconds
time.sleep(3)

# Mock content to write to the file
mock_content = """
# Mock Content

This is a mock paragraph written to the file after a delay.
"""

# File path
file_path = "/Users/lakshhkhatri/Desktop/WiproProject/UI /insights_outputs/insights_workday.md"

# Write the mock content to the file
with open(file_path, "w") as file:
    file.write(mock_content)

print(f"Mock content has been written to {file_path}")