import sys
import os

sys.exit(os.environ.get("linting_status", "failed") == "failed")
