import sys
import os

# Ensure project root and service directory are in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
service_dir = os.path.join(root_dir, "service")
for p in [root_dir, service_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from service.main import app
