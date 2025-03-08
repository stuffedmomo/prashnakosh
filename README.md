# Prashnakosh - AI-Powered Interview Question Generator

Prashnakosh is a web application that uses AI to generate tailored interview questions based on a user's resume. The name "Prashnakosh" combines "Prashna" (question) and "Kosh" (treasury) in Sanskrit, signifying a treasury of questions.

## Features

- **Resume Upload**: Support for PDF, DOC, and DOCX file formats
- **AI-Powered Analysis**: Extracts key information from resumes using natural language processing
- **Custom Question Generation**: Creates tailored interview questions based on the user's skills and experience
- **Key Term Identification**: Highlights frequent terms from the resume
- **Modern UI**: Clean, responsive design with a forest green theme
- **Privacy-Focused**: Processes resumes without permanent storage

## Technology Stack

- **Framework**: Django 5.0
- **Frontend**: HTML, CSS (Tailwind CSS), JavaScript
- **Database**: PostgreSQL (Supabase)
- **AI Model**: LLaMA 3.2 (1B) via Ollama
- **Document Processing**: PyMuPDF for PDF, python-docx for DOCX
- **Deployment**: Gunicorn, Whitenoise
- **Monitoring**: Sentry

## Local Development Setup

1. **Clone the repository**:
   ```
   git clone https://github.com/stuffedmomo/prashnakosh.git
   cd prashnakosh
   ```

2. **Create and activate a virtual environment**:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   - Copy `.env.example` to `.env`
   - Update the values in `.env` with your configuration

5. **Run migrations**:
   ```
   python manage.py migrate
   ```

6. **Run the development server**:
   ```
   python manage.py runserver
   ```

7. **Access the application**:
   Open your browser and go to http://localhost:8000

## Production Deployment

### Prerequisites

- PostgreSQL database (Supabase recommended)
- Web server (Nginx recommended)
- Domain name and SSL certificate
- Ollama server with LLaMA 3.2 installed

### Deployment Steps

1. **Set up environment variables**:
   - Configure all production variables in your server environment

2. **Install requirements**:
   ```
   pip install -r requirements.txt
   ```

3. **Collect static files**:
   ```
   python manage.py collectstatic --settings=prashnakosh.settings_production
   ```

4. **Run migrations**:
   ```
   python manage.py migrate --settings=prashnakosh.settings_production
   ```

5. **Configure Gunicorn**:
   Use the provided Procfile or run:
   ```
   gunicorn prashnakosh.wsgi_production:application
   ```

6. **Set up Nginx**:
   Configure Nginx to proxy requests to Gunicorn and serve static files.
   Sample configuration:
   ```
   server {
       listen 80;
       server_name prashnakosh.in www.prashnakosh.in;
       
       location = /favicon.ico { access_log off; log_not_found off; }
       
       location /static/ {
           alias /path/to/staticfiles/;
       }
       
       location /media/ {
           alias /path/to/mediafiles/;
       }
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

7. **Set up SSL with Certbot**:
   ```
   sudo certbot --nginx -d prashnakosh.in -d www.prashnakosh.in
   ```

## Monitoring and Maintenance

- Set up Sentry for error tracking
- Configure regular database backups
- Set up application and server monitoring 
- Implement a log rotation strategy

## Project Structure

```
prashnakosh/
│
├── manage.py                   # Django command-line utility
├── db.sqlite3                  # SQLite database (dev only)
│
├── prashnakosh/                # Main project configuration
│   ├── __init__.py
│   ├── settings.py             # Base settings
│   ├── settings_dev.py         # Development settings
│   ├── settings_staging.py     # Staging settings
│   ├── settings_production.py  # Production settings
│   ├── urls.py                 # URL configuration
│   ├── wsgi.py                 # WSGI configuration
│   ├── wsgi_production.py      # Production WSGI configuration
│   └── asgi.py                 # ASGI configuration
│
├── resume_app/                 # Main application
│   ├── __init__.py
│   ├── admin.py                # Admin configuration
│   ├── apps.py                 # App configuration
│   ├── context_processors.py   # Context processors for templates
│   ├── models.py               # Data models
│   ├── tests.py                # Tests
│   ├── views.py                # View functions
│   │
│   ├── migrations/             # Database migrations
│   └── templates/              # HTML templates
│       ├── base.html           # Base template
│       ├── upload.html         # Resume upload page
│       ├── questions.html      # Results page
│       ├── privacy.html        # Privacy policy
│       └── terms.html          # Terms of service
│
├── static/                     # Static files
│   └── styles.css              # Custom CSS
│
├── media/                      # User uploaded files (temporary)
│
├── logs/                       # Log files
│
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore file
├── Procfile                    # Deployment configuration
└── README.md                   # Project documentation
```

## License

© 2024 Prashnakosh. All rights reserved.

## Contact

For questions or support, please contact support@prashnakosh.in

### Database Setup with Supabase

This project uses Supabase for PostgreSQL database hosting:

1. **Connection details**:
   - The connection details are stored in the `.env` file
   - Make sure to update the password and host if you're setting up your own instance

2. **Running migrations**:
   ```
   python manage.py migrate
   ```

3. **Database schema**:
   - The application doesn't use extensive database models
   - Tables are created for Django's internal operations 