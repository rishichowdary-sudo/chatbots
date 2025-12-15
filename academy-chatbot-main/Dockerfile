# Use an official Python runtime as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /academy-chatbot-app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code into the container.
COPY . .

# Expose the port that the application listens on.
EXPOSE 8001

# Run the application.
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "wsgi:app"]
