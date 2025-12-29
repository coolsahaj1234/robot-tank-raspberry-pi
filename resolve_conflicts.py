import re
import sys

def resolve_conflicts(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Regex to find conflict blocks
    # Matches <<<<<<< HEAD ... ======= ... >>>>>>> ...
    # We want to keep the content between ======= and >>>>>>>
    
    pattern = re.compile(r'<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> .*?\n', re.DOTALL)
    
    def replacer(match):
        # Return the second group (the incoming change)
        return match.group(2) + '\n'

    new_content = pattern.sub(replacer, content)

    with open(filepath, 'w') as f:
        f.write(new_content)
    
    print(f"Resolved conflicts in {filepath}")

if __name__ == "__main__":
    resolve_conflicts(sys.argv[1])
