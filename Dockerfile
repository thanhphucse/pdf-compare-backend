# # Select a base image that includes Python
# FROM python:3.12.7-slim

# # Set up a working directory in the container for your application
# WORKDIR /app

# # Copy the backend code into the container
# COPY . /app

# # Install any Python dependencies listed in 'requirements.txt'
# RUN pip install --no-cache-dir -r requirements.txt

# # Expose the port the app runs on
# EXPOSE 5000

# # Set the command to run your application
# # (Be sure to replace './your_app_script.py' with the relative path to the Python file that starts your application)
# # CMD ["python", "./manage.py"]
# CMD ["gunicorn", "--bind", ":5000", "pdf_compare.wsgi:application"]

# Select a base image that includes Python
FROM python:3.12.7-slim

# Set up a working directory in the container for your application
WORKDIR /app

# Install system dependencies required for PyMuPDF and OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the backend code into the container
COPY . /app

# Install Python dependencies listed in 'requirements.txt'
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 5000

# Run your Django application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "pdf_compare.wsgi:application"]
