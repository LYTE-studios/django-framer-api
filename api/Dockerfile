FROM python:3.12-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install pipenv
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir pipenv

# Copy dependency files
COPY Pipfile ./

# Install dependencies
RUN pipenv lock && \
    pipenv install --system --deploy

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p media staticfiles

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "api.wsgi:application"]