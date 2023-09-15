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

echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser(os.environ.get('DJANGO_SUPERUSER_NAME_M'), os.environ.get('DJANGO_SUPERUSER_EMAIL_M'), os.environ.get('DJANGO_SUPERUSER_PASSWORD_M')) if not User.objects.filter(username=os.environ.get('DJANGO_SUPERUSER_NAME_M')).exists() else None" | python manage.py shell
echo "Superuser is created!"

# Start the server using Daphne (production)
echo "Starting the server with Daphne..."
exec daphne -b 0.0.0.0 -p 8000 air_service.asgi:application

