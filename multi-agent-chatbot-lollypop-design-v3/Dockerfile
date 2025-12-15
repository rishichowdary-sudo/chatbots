# Use an official Python runtime as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /multi-agent-chatbot

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port your app will run on
EXPOSE 8000

# Command to run the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "wsgi:app"]