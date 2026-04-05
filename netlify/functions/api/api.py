"""
Netlify Python Function — FastAPI wrapped with Mangum.

Directory layout after CI build:
  netlify/functions/api/
    api.py           ← this file (handler entry point)
    requirements.txt
    lib/             ← pip deps installed here by CI
    src/             ← project source (main.py, engines/, data/, etc.)
"""
import sys, os

_here = os.path.dirname(os.path.abspath(__file__))

# 1. Bundled pip deps
_lib = os.path.join(_here, "lib")
if os.path.isdir(_lib) and _lib not in sys.path:
    sys.path.insert(0, _lib)

# 2. Project source files (copied here by CI)
_src = os.path.join(_here, "src")
if os.path.isdir(_src) and _src not in sys.path:
    sys.path.insert(0, _src)

from mangum import Mangum
from main import app

handler = Mangum(app, lifespan="off", api_gateway_base_path="/api")
