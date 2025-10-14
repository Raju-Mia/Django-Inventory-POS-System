#!/bin/bash

# Print usage if no argument is given
if [ -z "$1" ]; then
  echo "Usage: ./run.sh [number]"
  echo "1 = Run server"
  echo "2 = Make migrations"
  echo "3 = Migrate"
  echo "4 = Create superuser"
  exit 1
fi

case $1 in
  1)
    echo "🚀 Running server..."
    python manage.py runserver 0.0.0.0:9090
    ;;
  2)
    echo "📦 Making migrations..."
    python manage.py makemigrations
    ;;
  3)
    echo "🗃️ Applying migrations..."
    python manage.py migrate
    ;;
  4)
    echo "👤 Creating superuser..."
    python manage.py createsuperuser
    ;;
  *)
    echo "❌ Invalid option. Use 1–4."
    exit 1
    ;;
esac
