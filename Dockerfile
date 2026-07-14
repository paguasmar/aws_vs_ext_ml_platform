# Use the official lightweight Python image.
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt /app/

# Install Python dependencies
# --no-cache-dir keeps the docker image size as small as possible
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app.py /app/

# Set environment variables for Python and SageMaker
# Python won't buffer stdout so we get logs immediately
ENV PYTHONUNBUFFERED=TRUE
# Prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=TRUE
# The port SageMaker expects us to serve on
ENV AIP_HTTP_PORT=8080

# Expose port 8080
EXPOSE 8080

# Start the FastAPI application
ENTRYPOINT ["python", "app.py"]
