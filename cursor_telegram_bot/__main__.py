# Compatibility shim: redirect to openab CLI
# Prefer: python -m openab
from openab.cli.main import app

if __name__ == "__main__":
    app()
