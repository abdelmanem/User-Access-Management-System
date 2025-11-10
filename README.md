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
   cd User Access Management System
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

4. **Set up environment variables**
   Create a `.env` file in the project root with the following content:
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
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
   ```bash
   python manage.py loaddata fixtures/sample_data.json
   ```

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