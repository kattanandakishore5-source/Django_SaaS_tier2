#!/bin/bash
echo "Packaging Django Admin Pro for Gumroad..."
zip -r django_admin_pro.zip . \
  -x "*.venv*" \
  -x "*__pycache__*" \
  -x "*.git*" \
  -x "*.env" \
  -x "*.sqlite3" \
  -x "*mnt*" \
  -x "*.pytest_cache*" \
  -x "*package_for_gumroad.sh*"
echo "Packaging complete: django_admin_pro.zip"
