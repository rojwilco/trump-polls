# Use an official Python 3.13 image as a base
FROM python:3.13-slim

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port the app will run on
EXPOSE 8080

# Run the command to start the app when the container launches
# see https://docs.railway.com/guides/start-command
CMD ["/bin/sh", "-c", "gunicorn wsgi:wsgi_app --bind [::]:$PORT --workers 4 "]    