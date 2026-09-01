#!/bin/bash
# Run database migrations
python manage.py migrate --noinput

# Start the Daphne server
exec daphne -b 0.0.0.0 -p 8080 config.asgi:application
