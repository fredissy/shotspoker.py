FROM python:3.14-slim

# Set working directory
WORKDIR /app

# app version set as environment variable
ARG APP_VERSION
ENV APP_VERSION=${APP_VERSION}

COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

RUN chmod +x entrypoint.sh

# Expose port
EXPOSE 5000

# Run the application
CMD ["./entrypoint.sh"]
