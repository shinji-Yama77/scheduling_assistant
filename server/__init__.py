# Initialize the server package
# This makes the server directory a proper Python package

from .autho_code_server import get_auth_code, run_server

__all__ = ['get_auth_code']
