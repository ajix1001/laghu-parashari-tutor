"""
Netlify Function — wraps FastAPI app with Mangum (ASGI→Lambda adapter).
Strips the /.netlify/functions/api prefix so FastAPI sees clean paths.
"""
import sys, os

# Add project root to path so all imports resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mangum import Mangum
from main import app

handler = Mangum(app, lifespan="off", api_gateway_base_path="/api")
