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


# Start the server using Daphne (production)
echo "Starting the server with Daphne..."
exec daphne -b 0.0.0.0 -p 8000 air_service.asgi:application

