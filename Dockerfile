FROM python:3.10-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=main.py
ENV FLASK_DEBUG=0
# Clear any proxy settings that might interfere with OpenAI
ENV HTTP_PROXY=""
ENV HTTPS_PROXY=""

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY main.py .
COPY static/ ./static/

# Create necessary directories
RUN mkdir -p uploads
RUN mkdir -p static/img

# Set upload folder permissions
RUN chmod 777 uploads

# Copy and prepare environment file
COPY .env.example ./.env
RUN sed -i 's/FLASK_DEBUG=True/FLASK_DEBUG=False/g' ./.env

# Expose port
EXPOSE 5050

# Run the application
CMD ["python", "main.py"] 