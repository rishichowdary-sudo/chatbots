# ----------- Builder Stage -----------
# Use an official Python runtime as the base image
FROM python:3.12-slim AS builder

# CleanUp
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /terralogic-chatbot-app

# # Virtual Env
# RUN python -m venv /opt/venv
# ENV PATH="/opt/venv/bin:$PATH"

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# ----------- Final Stage -----------
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /terralogic-chatbot-app

# Copy installed packages from builder
COPY --from=builder /install /usr/local
# ENV PATH="/opt/venv/bin:$PATH"

# Copy the rest of the application code
COPY . .

# Expose the port your app will run on
EXPOSE 8002

# Command to run the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8002", "wsgi:app"]