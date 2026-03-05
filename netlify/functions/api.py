"""Netlify serverless function entry point.

Wraps the FastAPI app with Mangum so it can run as an
AWS Lambda-compatible handler (which Netlify Functions use).
"""
import sys
import os

# Add project root to path so `app` and `main` packages resolve
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from mangum import Mangum
from main import app

# The redirect sends /api/audit → /.netlify/functions/api/api/audit
# Mangum strips the api_gateway_base_path, leaving /api/audit for FastAPI
handler = Mangum(app, lifespan="off", api_gateway_base_path="/.netlify/functions/api")
