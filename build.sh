#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# Create staticfiles directory if it doesn't exist
mkdir -p staticfiles

python manage.py collectstatic --no-input
python manage.py migrate
