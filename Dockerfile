# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set environment variables to prevent Python from buffering stdout and writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies necessary for MySQL and Python development
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file to the container
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt -vvv  # Use verbose output to troubleshoot

# Copy the entire Django project to the container
COPY . /app/

# Set environment variables for Django
ENV DJANGO_SETTINGS_MODULE=TalentHunt.settings
ENV PYTHONPATH=/app

# Collect static files (only needed in production)
RUN python manage.py collectstatic --noinput

# Expose port 8000 to allow access to the Django development server
EXPOSE 8000

# Run database migrations
RUN python manage.py migrate

# Start the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
