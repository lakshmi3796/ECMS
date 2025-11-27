1. Create a project folder-
   - mkdir <project_folder_name>
3. Create a virtual environment using python -
  - python3 -m venv <env_name>
4. Activate virtual environment-
   - source env/bin/activate
5. Install module registered in requirements.txt via pip-
   - pip install -r requirements.txt
6. Create django project-
   - django-admin startproject <project_name>
7. Goto inside project folder-
  - cd <project_name>
8. Create django app-
  - python manage.py startapp <app_name>
9. Register your app in your django project's settings.py inside INSTALLED_APPS-
  - INSTALLED_APPS[...,<app_name>,]
10. Install and start postgres-
  - brew install postgresql
  - brew services start postgresql
11. Connect postgres and create DB and a user-
  - psql postgres
  - CREATE USER <your_user> WITH PASSWORD 'your_password';
  - CREATE DATABASE <your_db>;
  - GRANT ALL PRIVILEGES ON DATABASE  <your_db> TO  <your_user>;
  - ALTER USER  <your_user> WITH SUPERUSER;
  - \q
12. Update database in django-project's settings.py-
  - DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env("DB_NAME"),
            'USER': env("DB_USER"), 
            'PASSWORD': env("DB_PASSWORD"),
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }
    ** I used environment variable to secure my db creds. **
13. Add SMTP configuration for send mail-
  - EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "smtp-relay.brevo.com"
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_USE_SSL = False
    EMAIL_HOST_USER = env("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

    ** I used brevo for free email service. **
14. Add celery & redis config in setting.py-
    CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://localhost:6379/1")
15. Add models as per project requirements in django_app/models.py-
  - Recipients, Campaigns,EmailLog
16. After that migrate db-
  - python manage.py makemigrations
  - python manage.py migrate
17. Run the server-
  - python manage.py runserver
18. Create superuser/admin-
  - python manage.py createsuperuser
19. Run Redis and celery-
  - brew services start redis
  - celery -A <project_name> beat -l info


** Basic server start at localhost:8000 **
