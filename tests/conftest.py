import sys
import os
from pathlib import Path

# Add the project root to the Python path so pytest can find the local modules
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Change working directory to project root for relative imports
os.chdir(project_root)
