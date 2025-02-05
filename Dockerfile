# Start from an official Python image.
FROM python:3.12

# Create a directory for the app code inside the container
WORKDIR /app

# Install required system dependencies
RUN apt-get update && apt-get install -y netcat-openbsd cron
RUN rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Expose port 8000 for the Django dev server
EXPOSE 8000

# Set the default command to run the Django development server
#CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
