# User Access Management System (UAMS)

A comprehensive Django-based web application for managing user access to various systems within an organization. This system provides features for user management, department organization, system administration, access assignment, and detailed access history tracking.

## Features

### Core Functionality
- **User Management**: Create, update, and manage user accounts with role-based access
- **Department Management**: Organize users into departments for better access control
- **System Management**: Define and manage various systems that users can access
- **Access Assignment**: Grant or revoke user access to specific systems with different permission levels
- **Access History**: Track all access events with detailed logs and timestamps
- **Search Functionality**: Search across users, departments, systems, and access records

### Advanced Features
- **Modern Responsive UI**: Clean, modern interface with responsive design
- **Dashboard Analytics**: Visual charts showing access trends and system usage
- **Data Import/Export**: Bulk import/export functionality for users, departments, systems, and access data
- **Admin Interface**: Django admin interface for system administration
- **Security Features**: CSRF protection, secure authentication, and access logging

## Technology Stack

- **Backend**: Django 5.2.8
- **Frontend**: HTML5, CSS3, Bootstrap 4, JavaScript, Chart.js
- **Database**: SQLite (development), PostgreSQL (production ready)
- **PostgreSQL driver**: psycopg (v3, binary wheels)
- **Authentication**: Django's built-in authentication system
- **Icons**: Font Awesome

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Virtual environment (recommended)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd User-Access-Management-System
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   - Note for Windows/Python 3.13: We use psycopg (v3) with binary wheels to avoid compiler toolchains.

4. **Set up environment variables**
   Copy `env.example` to `.env` and adjust as needed:
   ```bash
   copy env.example .env   # Windows
   # or
   cp env.example .env     # macOS/Linux
   ```
   Generate and write a strong SECRET_KEY into your `.env`:
   ```bash
   # Windows
   python generate_secret_key.py
   # Ubuntu/macOS
   python3 generate_secret_key.py
   ```

5. **Run database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser account**
   ```bash
   python manage.py createsuperuser
   ```

7. **Load sample data (optional)**
   No default fixtures are provided. You can create your own with `dumpdata`.

8. **Run the development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
   - Main application: http://127.0.0.1:8000/
   - Admin interface: http://127.0.0.1:8000/admin/
   - Dashboard: http://127.0.0.1:8000/dashboard/

## Usage

### Getting Started
1. **Login**: Use your superuser credentials to log in
2. **Dashboard**: View system statistics and access trends
3. **Navigation**: Use the navigation menu to access different sections

### Managing Users
1. Navigate to the Users section
2. Click "Add User" to create new user accounts
3. Edit user details, assign to departments, and manage access levels

### Managing Departments
1. Go to the Departments section
2. Create new departments with descriptions
3. Assign users to departments for organized access control

### Managing Systems
1. Access the Systems section
2. Add new systems with descriptions and owners
3. Configure system-specific access requirements

### Access Assignment
1. Navigate to Access Management
2. Create access assignments linking users to systems
3. Set access types (Read, Write, Admin) and priorities
4. Approve or reject access requests

### Data Import/Export
1. Go to Data Import/Export section
2. **Export**: Click on any export link to download data as CSV
3. **Import**: Upload CSV files to bulk import users, departments, or systems

### Viewing Access History
1. Access the Access History section
2. View detailed logs of all access events
3. Filter by user, system, or date range
4. Export history data for analysis

## Data Import/Export Format

### Users CSV Format
```csv
username,email,first_name,last_name,is_active
doe_john,john.doe@company.com,John,Doe,true
smith_jane,jane.smith@company.com,Jane,Smith,true
```

### Departments CSV Format
```csv
name,description,is_active
IT Department,Information Technology,true
HR Department,Human Resources,true
```

### Systems CSV Format
```csv
name,description,owner,is_active
CRM System,Customer Relationship Management,john.doe,true
ERP System,Enterprise Resource Planning,jane.smith,true
```

## Project Structure

```
User Access Management System/
├── accounts/                 # User management app
├── departments/              # Department management app
├── systems/                  # System management app
├── access_management/        # Access assignment and history
├── dashboard/                # Dashboard and analytics
├── data_import_export/       # Import/export functionality
├── search/                   # Search functionality
├── templates/                # HTML templates
├── static/                   # CSS, JavaScript, images
├── utils/                    # Utility functions (importers, exporters)
├── user_access_management/     # Main project settings
├── media/                    # Uploaded files
├── requirements.txt          # Python dependencies
└── manage.py                 # Django management script
```

## Security Considerations

- Always use HTTPS in production
- Keep your SECRET_KEY secure and unique
- Regularly update dependencies
- Implement proper backup strategies
- Monitor access logs for suspicious activity
- Use strong passwords and consider implementing password policies

## Production Deployment

1. Environment variables
   - Use `env.prod.example` as a template in production environments.
   - Ensure `DEBUG=False` and set a strong `SECRET_KEY`.
   - Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to your domains.

2. Database
   - Provision PostgreSQL and set `DATABASE_URL` (e.g., `postgres://user:pass@host:5432/db`).
   - psycopg (v3) is already included; no OS build tools needed on Windows.
   - Alternative configuration using individual environment variables (set `DJANGO_DB=postgres`):
     ```env
     # PostgreSQL Settings (only used when DJANGO_DB=postgres)
     DJANGO_DB=postgres
     POSTGRES_DB=UAMS
     POSTGRES_USER=UAMS_user
     POSTGRES_PASSWORD=***************
     POSTGRES_HOST=localhost
     POSTGRES_PORT=5432
     ```

3. Static files
   - Set `USE_WHITENOISE=True` (or serve static via your web server).
   - Run `python manage.py collectstatic`.

4. Security headers
   - With `DEBUG=False`, HSTS and secure cookies are enabled by default.

5. Run the app
   - Use a WSGI server (e.g., gunicorn/uwsgi) behind a reverse proxy.
   - Entry point: `user_access_management.wsgi:application`.

## Production Installation (Step-by-step)

1. System prerequisites
   - Python 3.12+
   - PostgreSQL 14+ (or managed Postgres)
   - A reverse proxy (e.g., Nginx) with HTTPS enabled
   - Ubuntu quick setup:
     ```bash
     sudo apt update
     sudo apt install -y python3-venv python3-pip nginx
     # If building native packages in future: sudo apt install -y build-essential libpq-dev
     ```

2. Get the code and set up a virtual environment
   ```bash
   git clone <repository-url>
   cd User-Access-Management-System
   python -m venv venv
   source venv/bin/activate   # Windows: venv\\Scripts\\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Configure environment variables
   ```bash
   cp env.prod.example .env
   # Edit .env and set:
   # - SECRET_KEY=<a long random string>
   # - DEBUG=False
   # - ALLOWED_HOSTS=yourdomain.com
   # - CSRF_TRUSTED_ORIGINS=https://yourdomain.com
   # - DATABASE_URL=postgres://user:pass@host:5432/dbname
   # - USE_WHITENOISE=True
   ```
   Optionally, auto-generate and write a strong SECRET_KEY:
   ```bash
   # Ubuntu/macOS
   python3 generate_secret_key.py
   # Windows
   python generate_secret_key.py
   ```

4. Initialize the database and collect static files
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py createsuperuser
   ```

5. Start the application with Gunicorn (example)
   ```bash
   # From project root
   gunicorn --bind 0.0.0.0:8000 user_access_management.wsgi:application
   ```
   - Behind Nginx, proxy requests to `127.0.0.1:8000`.
   - Ensure Nginx serves HTTPS and sets appropriate proxy headers.

6. Health check
   - Verify the app: `curl -fsS http://127.0.0.1:8000/healthz` → `{"status":"ok","db":true}`

7. Optional: run with Docker Compose
   ```bash
   docker compose up --build -d
   # Add/override env vars by pointing compose to a prod .env file
   ```

Notes
- When `DEBUG=False`, make sure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` match your public domain(s).
- If using external static serving (CDN or Nginx), you can disable WhiteNoise and serve `staticfiles/` directly.
- Set `SENTRY_DSN` in the environment to enable error monitoring.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation and FAQ

## Changelog

### Version 1.0.0
- Initial release with core functionality
- User, department, and system management
- Access assignment and history tracking
- Dashboard with analytics
- Data import/export functionality
- Modern responsive UI