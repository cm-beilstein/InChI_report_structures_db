# Use an official Python runtime as a parent image
FROM python:3.12-slim

RUN apt-get update && apt-get install -y gunicorn openssl

# Set the working directory in the container
WORKDIR /app

RUN openssl req -newkey rsa:2048 -nodes -keyout /app/server.key \
    -x509 -out /app/server.crt -days 365 \
    -subj "/C=DE/ST=Hessen/L=Frankfurt/O=Beilstein/CN=localhost"

# Copy the requirements file into the container
COPY requirements.txt .
COPY db_con.env .
COPY tokens.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY app .

ENV INCHI_WS_APP_PORT=8612

EXPOSE 8612

# Define environment variable to not buffer python output
ENV PYTHONUNBUFFERED=1

CMD ["python", "app_ws.py"]
