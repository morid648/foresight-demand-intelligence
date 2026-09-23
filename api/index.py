import sys
import os

# Set up paths
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
service_dir = os.path.join(root_dir, "service")
src_dir = os.path.join(root_dir, "src")

for p in [root_dir, service_dir, src_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from service.main import app
except Exception as e:
    from fastapi import FastAPI
    app = FastAPI(title="Project FORESIGHT API (Fallback)")

    @app.get("/{full_path:path}")
    def fallback_error(full_path: str = ""):
        import traceback
        return {
            "error": "Initialization Error in Serverless Runtime",
            "details": str(e),
            "traceback": traceback.format_exc(),
            "python_path": sys.path,
            "path_requested": full_path
        }
