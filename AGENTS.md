# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview
农机检测小程序后端 - Agricultural Machinery Inspection System backend. A Django-based system for managing agricultural vehicle inspection records with OCR recognition and Word document export capabilities.

## Common Commands

### Development
```bash
# Run development server
uv run python manage.py runserver

# Run on specific port
uv run python manage.py runserver 0.0.0.0:8000

# Create database migrations
uv run python manage.py makemigrations

# Apply database migrations
uv run python manage.py migrate

# Create superuser
uv run python manage.py createsuperuser

# Collect static files
uv run python manage.py collectstatic --noinput

# Django shell
uv run python manage.py shell
```

### Dependency Management (uses uv)
```bash
# Install dependencies
uv sync

# Add new dependency
uv add <package>

# Add dev dependency
uv add --dev <package>
```

### Production Deployment
```bash
# Full deployment (on server)
./03-deploy.sh

# Just restart service
./03-deploy.sh restart

# Check service status
./03-deploy.sh status

# View logs
./03-deploy.sh logs
```

## Architecture

### Tech Stack
- **Backend**: Django 4.2 + Django REST Framework
- **Database**: SQLite (development), same for production currently
- **Admin UI**: Django Admin (no simpleui despite being in deps)
- **Authentication**: Token-based (DRF TokenAuthentication)
- **OCR**: Alibaba Cloud OCR API (行驶证识别、车牌识别)
- **Document Export**: docxtpl for Word template rendering

### App Structure
```
apps/
├── users/          # User management, authentication, system config
│   ├── models.py   # User (custom), SystemConfig (OCR credentials)
│   └── ...
└── inspection/     # Core inspection record functionality
    ├── models.py   # InspectionRecord
    ├── services.py # OCRService, WordExportService
    ├── admin.py    # Admin interface with OCR button, export actions
    └── templates/  # Word document template (inspection_template.docx)
```

### Key Services

**OCRService** (`apps/inspection/services.py`):
- Uses Alibaba Cloud OCR API
- Credentials stored in database (`SystemConfig` model), not env vars
- Methods: `recognize_vehicle_license()`, `recognize_car_number()`

**WordExportService** (`apps/inspection/services.py`):
- Uses docxtpl template engine
- Template at `apps/inspection/templates/inspection_template.docx`
- Supports single export and batch export (ZIP)
- Image sizing controlled by `_get_image_size()` method

### User Roles & Permissions
- **Superuser**: Full access to all records and OCR
- **OCR用户 (ocr_user)**: Can use OCR recognition feature
- **普通用户 (normal_user)**: Can only view/edit own records, no OCR

Permission check: `user.can_use_ocr` property determines OCR access.

### API Endpoints
- `/admin/` - Django Admin interface
- `/api/v1/` - REST API (includes users and inspection endpoints)

### Important Notes
- OCR API credentials are managed in Admin → OCR配置, only one can be active
- Word export uses `filename*=UTF-8''` encoding for Chinese filenames
- Data ownership: users can only see their own InspectionRecord entries (except superuser)
