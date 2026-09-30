import sys
import os

root_dir = os.path.dirname(os.path.abspath(__file__))

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Add all relevant subdirectories to sys.path so modules can be imported
# even if their parent folder names have hyphens.
for folder in ['document-processing', 'ai-workflows', 'data-schemas']:
    path = os.path.join(root_dir, folder)
    if path not in sys.path:
        sys.path.insert(0, path)
