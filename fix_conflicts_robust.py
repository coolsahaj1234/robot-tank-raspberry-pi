
import re
import sys
import os

def resolve_file(filepath):
    print(f"Processing {filepath}...")
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Regex to find conflict blocks
        # Matches <<<<<<< HEAD ... ======= ... >>>>>>> ...
        # We want to keep the content between ======= and >>>>>>>
        
        pattern = re.compile(r'<<<<<<< HEAD\n.*?\n=======\n(.*?)\n>>>>>>> .*?\n', re.DOTALL)
        
        # Function to replace with the second group (incoming)
        def replace_match(match):
            # match.group(0) is the whole block
            # match.group(1) is the content we want
            print(f"Resolved a conflict block in {filepath}")
            return match.group(1) + '\n' # Ensure we have a clean newline
        
        new_content = pattern.sub(replace_match, content)
        
        # Also clean up any potential leftover markers if regex didn't match perfectly (e.g. edge cases)
        # But for now, let's trust the regex for standard markers.
        
        if new_content != content:
            with open(filepath, 'w') as f:
                f.write(new_content)
            print(f"Fixed conflicts in {filepath}")
        else:
            print(f"No conflicts found matching pattern in {filepath}")
            
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

if __name__ == "__main__":
    files = [
        "web_robot_controller/ai_service/ai_processor.py",
        "web_robot_controller/ai_service/server.py"
    ]
    for f in files:
        resolve_file(f)
