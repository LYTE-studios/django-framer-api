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
- Comprehensive test suite

## Setup

1. Install dependencies:
```bash
pipenv install
```

2. Create and configure your .env file:
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

4. Run the test suite to verify everything is working:
```bash
python manage.py test blogs
```

5. Start the development server:
```bash
# Terminal 1: Django server
python manage.py runserver

# Terminal 2: Celery worker
celery -A api worker --loglevel=info

# Terminal 3: Celery beat (scheduler)
celery -A api beat --loglevel=info
```

## Tests

The project includes a comprehensive test suite that covers:

- Model functionality
  - Client creation and post scheduling
  - Blog post creation and status management
- API endpoints
  - Authentication
  - Client management
  - Blog post generation
- Background tasks
  - Automated post generation
  - Error handling and retries

Run the tests with:
```bash
python manage.py test blogs
```

For verbose output:
```bash
python manage.py test blogs -v 2
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

3. In your Framer site, fetch and display the posts using the API endpoints

## License

MIT
