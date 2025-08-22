import os
import argparse

def remove_string_from_files(directory_path, target_string):
    """
    Searches files in the specified directory and removes a target string
    from the top of each file if it exists.
    """
    if not os.path.isdir(directory_path):
        print(f"Error: Directory not found at '{directory_path}'")
        return

    print(f"Searching for files in '{directory_path}' to remove the specified string...")

    for root, _, files in os.walk(directory_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            try:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()

                if content.startswith(target_string):
                    new_content = content[len(target_string):]
                    with open(file_path, 'w', encoding='utf-8') as f: # Always write back as UTF-8
                        f.write(new_content)
                    print(f"Removed string from: {file_path}")
                else:
                    print(f"String not found at the top of: {file_path}")
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove a specific string from the top of files in a directory.")
    parser.add_argument("directory", help="The path to the directory to search.")
    
    args = parser.parse_args()

    # The exact string to be removed
    string_to_remove = """---
---
---
---
---

---
"""

    remove_string_from_files(args.directory, string_to_remove)
    print("\nProcess completed.")
