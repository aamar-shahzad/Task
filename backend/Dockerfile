# Use Alpine-based Python image which is smaller and might avoid zlib issues
FROM python:3.10-alpine

# Set working directory
WORKDIR /app

# Install build dependencies for any Python packages that need compilation
RUN apk add --no-cache build-base

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Expose the port the app runs on
EXPOSE 3001

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3001"]