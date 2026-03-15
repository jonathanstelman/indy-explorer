import os
import sys

# Ensure pipeline/ is on sys.path so bare module imports resolve to pipeline/xxx.py
PIPELINE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pipeline"))
if PIPELINE not in sys.path:
    sys.path.insert(0, PIPELINE)
