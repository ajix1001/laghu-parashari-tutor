"""
Netlify Function — FastAPI wrapped with Mangum.
Dependencies are bundled into lib/ by GitHub Actions before deploy.
"""
import sys, os

_here = os.path.dirname(os.path.abspath(__file__))

# 1. Bundled pip deps (installed by CI into netlify/functions/lib/)
_lib = os.path.join(_here, "lib")
if os.path.isdir(_lib) and _lib not in sys.path:
    sys.path.insert(0, _lib)

# 2. Project root  (so `from main import app`, `from engines import ...` etc. all work)
_root = os.path.abspath(os.path.join(_here, "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from mangum import Mangum
from main import app

handler = Mangum(app, lifespan="off", api_gateway_base_path="/api")
