#!/bin/bash
echo "Packaging Django Starter for Gumroad..."
zip -r django_starter.zip . \
  -x "*.venv*" \
  -x "*__pycache__*" \
  -x "*.git*" \
  -x "*.env" \
  -x "*.sqlite3" \
  -x "*mnt*" \
  -x "*.pytest_cache*" \
  -x "*package_for_gumroad.sh*"
echo "Packaging complete: django_starter.zip"
