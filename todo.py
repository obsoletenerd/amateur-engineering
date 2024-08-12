## TODO ##
# FILE: app.bak.py
# -  Needs a route to load a single post by ID with a URL like /post/title-of-post (Line 28)
# -  Figure out pagination at some point, but for now just show all posts (Line 34)
# -  Either strip the first H1 from the markdown text, or modify the template to not show the first H1 (Line 65)
# -  Finish these functions and refactor the other code to suit. (Line 266)
# -  This breaks because we're trying to get the WWW url and need to convert it to the API one again (Line 320)
# -  ... so need to break out the get_github and get_gitlab functions to have convert_github_url and convert_gitlab_url functions then fix all the associated crap (Line 321)
#
# FILE: app.py
# -  Figure out pagination at some point, but for now just show all posts (Line 32)
# -  Either strip the first H1 from the markdown text, or modify the template to not show the first H1 (Line 66)
# -  This crashes because get_members() is broken. (Line 82)
# -  One day find a better way to do this than nuking the entire DB every time :P (Line 94)
# -  Only add users if they've actually got posts to add. (Line 103)
# -  For each markdown file the user has, get the contents and insert them into the database - import_post(user_id, markdown_url) (Line 118)
# -  This function is very broken. (Line 248)
# -  Get the title from the first H1 in the markdown, or the filename if no H1 (Line 466)
# -  Convert the markdown into HTML using markdown.markdown() (Line 467)
#
## /TODO ##

# TODO Builder v1.0
# Author: Sen (https://www.github.com/senwerks/todo.py/)
# Description: This script scans all .py files in the current directory for TODO comments and inserts them above.
# Usage: Run this script in the same directory as the .py files you want to scan. The file MUST have the TODO and /TODO tags as shown above or the universe will implode.

import os
import re

# File name of the script itself
script_file_name = "todo.py"

# Read the entire script
with open(script_file_name, "r") as file:
    lines = file.readlines()

# Find the start and end of the existing TODO section
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if "## TODO ##" in line:
        start_idx = i + 1
    elif "## /TODO ##" in line:
        end_idx = i
        break

# Initialize a dictionary to store TODO items by file
todo_items_by_file = {}

# Loop through all .py files in the current directory
for file in os.listdir("."):
    if (
        file.endswith(".py") and file != script_file_name
    ):  # Ignore the script file itself
        with open(file, "r") as f:
            file_lines = f.readlines()
            # Find TODOs and include line number
            for index, line in enumerate(file_lines):
                if re.match(r"^# TODO:", line.strip()):
                    todo_text = line.strip()[7:]  # Strip the "# TODO:" prefix
                    # Append the todo item with its line number to the list of todos for this file
                    if file not in todo_items_by_file:
                        todo_items_by_file[file] = []
                    todo_items_by_file[file].append((todo_text, index + 1))

# Construct the new TODO section
new_todo_section = []
for file, todos in todo_items_by_file.items():
    new_todo_section.append(f"# FILE: {file}\n")
    for todo_text, line_number in todos:
        new_todo_section.append(f"# - {todo_text} (Line {line_number})\n")
    new_todo_section.append("#\n")

# Replace the old TODO section with the new one in the script
if start_idx is not None and end_idx is not None:
    lines[start_idx:end_idx] = new_todo_section

# Write the modified script back to file
with open(script_file_name, "w") as file:
    file.writelines(lines)
