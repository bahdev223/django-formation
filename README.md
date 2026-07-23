# django-formation

Universal training center management engine for Django.

Manages: establishments, learners, training programs, sessions, and enrollments.

## Installation

```bash
pip install django-formation
```

## Quick Start

```python
INSTALLED_APPS = [
    ...
    "rest_framework",
    "django_filters",
    "django_formation",
]

urlpatterns = [
    path("api/v1/formation/", include("django_formation.urls")),
]
```

```bash
python manage.py migrate formation
```

## License

MIT
