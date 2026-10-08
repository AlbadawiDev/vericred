"""Check production configuration without logging a real secret or changing data."""
import os
from pathlib import Path
import secrets
import subprocess
import sys

env = dict(os.environ, DEBUG='0', SECRET_KEY=secrets.token_urlsafe(64),
           ALLOWED_HOSTS='verify.example.com', PUBLIC_BASE_URL='https://verify.example.com')
result = subprocess.run([sys.executable, 'manage.py', 'check', '--deploy', '--fail-level', 'WARNING'],
                        cwd=Path(__file__).resolve().parents[1], env=env, check=False)
raise SystemExit(result.returncode)
