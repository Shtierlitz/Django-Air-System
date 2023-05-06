#!/bin/sh

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Call default data and group creation functions
#if [ ! -f "data_initialized" ]; then
#  echo "Creating default data and groups..."
#  python -c "from flights.default_data import create_default_data, create_groups; create_default_data(); create_groups()"
#  # Create a file to mark that the data was initialized
#  touch data_initialized
#fi

# Start the server (only for dev docker-compose up)
echo "Starting the server..."
exec python manage.py runserver 0.0.0.0:8000
