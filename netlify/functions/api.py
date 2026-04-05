"""
Netlify Function — wraps FastAPI app with Mangum (ASGI→Lambda adapter).
Bundles all Python dependencies from the lib/ directory alongside this file.
"""
import sys, os

# Bundled deps (Linux wheels unpacked alongside this function)
_here = os.path.dirname(__file__)
_lib  = os.path.join(_here, "lib")
if _lib not in sys.path:
    sys.path.insert(0, _lib)

# Project root (two levels up: netlify/functions/ → project root)
_root = os.path.abspath(os.path.join(_here, "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from mangum import Mangum
from main import app

handler = Mangum(app, lifespan="off", api_gateway_base_path="/api")
