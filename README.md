# Django Framer Blog Generator API

An automated blog post generation system that creates content for Framer websites using ChatGPT. The system allows you to manage clients, set custom GPT prompts for their tone of voice, and automatically generate blog posts at specified intervals.

## Features

- Client management through Django Admin interface
- Custom GPT prompts per client
- Automated blog post generation at configurable intervals
- REST API endpoints for integration with Framer
- Token-based authentication
- Automatic retry for failed generations
- CORS support for frontend integration
- SQLite database for simple setup
- Docker support for easy deployment

## Local Development Setup

1. Install dependencies:
```bash
pipenv install
```

2. Create and configure your .env file:v
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

3. Set up the database and create admin user:
```bash
cd api
python manage.py migrate
python manage.py createsuperuser
```

4. Run the test suite:
```bash
python manage.py test blogs
```

## Docker Setup

1. Build and start all services:
```bash
docker-compose up --build
```

2. Run migrations:
```bash
docker-compose exec web python manage.py migrate
```

3. Create a superuser:
```bash
docker-compose exec web python manage.py createsuperuser
```

### Updating Dependencies

If you need to update dependencies:

1. Update the Pipfile:
```bash
# Add or modify dependencies in Pipfile
pipenv install <new-package>
```

2. Lock the dependencies:
```bash
pipenv lock
```

3. Rebuild the Docker containers:
```bash
docker-compose down
docker-compose up --build
```

## Usage

1. Access the admin interface at `http://localhost:8000/admin/`
2. Create a new client with:
   - Name
   - GPT prompt for tone of voice
   - Post generation interval

3. The system will automatically generate posts at the specified intervals

## API Endpoints

- `/api/clients/` - Client management
- `/api/posts/` - Blog post management
- `/api/clients/{id}/generate_post/` - Trigger immediate post generation
- `/api-token-auth/` - Get authentication token

## Environment Variables

Required:
- `OPENAI_API_KEY` - Your OpenAI API key

Optional:
- `DJANGO_SECRET_KEY` - Django secret key (default provided for development)
- `DJANGO_DEBUG` - Debug mode (defaults to True)
- `DJANGO_ALLOWED_HOSTS` - Allowed hosts (defaults to *)
- `CORS_ALLOWED_ORIGINS` - Allowed CORS origins

## Docker Services

The application runs with the following services:

- `web`: Django application with Gunicorn
- `celery_worker`: Processes background tasks
- `celery_beat`: Schedules periodic tasks
- `redis`: Message broker for Celery

## Tests

Run the tests with:
```bash
# Local development
python manage.py test blogs

# In Docker
docker-compose exec web python manage.py test blogs
```

## Framer Integration

1. Get an authentication token:
```bash
curl -X POST http://localhost:8000/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

2. Use the token to fetch blog posts:
```bash
curl http://localhost:8000/api/posts/ \
  -H "Authorization: Token your_token_here"
```

## License

MIT
