#!/bin/sh
# Starts the deal finder on the address it prints (normally http://localhost:8770) and opens it in your browser.
cd "$(dirname "$0")" && exec python3 serve.py "$@"
