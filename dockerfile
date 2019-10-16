# Use an official Python runtime as a parent image
FROM python:3.7-slim

# Set the working directory to /app
WORKDIR /

# Copy the current directory contents into the container at /app
COPY . /

# Install libmysqlclient-dev
RUN apt-get clean && \
    apt-get update && \
    apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV NAME World
ENV FLASK_APP tbot.py
ENV FLASK_DEBUG 1

# Run app.py when the container launches
ENTRYPOINT flask run --port=5000 --host=0.0.0.0