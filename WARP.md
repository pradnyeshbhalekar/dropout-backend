# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a Flask-based REST API backend for a student dropout prediction system. It uses MongoDB with MongoEngine ODM for data persistence and implements JWT-based authentication.

## Common Development Commands

### Environment Setup
```bash
# Create virtual environment
python3 -m venv env

# Activate virtual environment
source env/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (copy from envexample)
cp envexample .env
# Edit .env to add your MongoDB URI and secret keys
```

### Running the Application
```bash
# Start the Flask development server
python app.py

# The server runs on http://localhost:5000 by default with debug mode enabled
```

### Database Management
```bash
# MongoDB connection is configured via environment variables:
# MONGO_URI - MongoDB connection string
# DB_NAME - Database name (defaults to "SIH")
```

### Dependency Management
```bash
# Install a new package
pip install <package-name>

# Update requirements.txt after installing new packages
pip freeze > requirements.txt
```

### Testing with Sample Data
The `test_files/` directory contains CSV files for bulk data import:
- `students.csv` - Student profile data
- `academic.csv` - Academic records
- `attendance.csv` - Attendance records
- `financial.csv` - Financial records
- `curricular.csv` - Curricular unit records

## Architecture Overview

### Application Structure

The application follows a modular Flask architecture with clear separation of concerns:

#### Core Application (`app.py`)
- Flask app initialization with MongoEngine connection
- Blueprint registration for modular routing
- Bcrypt initialization for password hashing
- All API routes are prefixed: auth routes under `/auth`, all other routes under `/api`

#### Configuration (`config.py`)
- Environment-based configuration using python-dotenv
- Manages SECRET_KEY, MONGO_URI, and DB_NAME from environment variables

#### Authentication System (`routes/auth.py`)
- JWT-based authentication with configurable expiry
- Endpoints: `/auth/signup`, `/auth/signin`, `/auth/logout`, `/auth/profile`
- Password reset flow: `/auth/forgot-password`, `/auth/reset-password`
- User ID generation follows pattern: `{ROLE_PREFIX}-{UUID}` (e.g., STU-3F9C1A2B for students)
- Supports three user roles: student, counselor, admin

#### Data Models (MongoEngine Documents)

The system uses a reference-based document structure:

1. **User Model** (`models/user.py`)
   - Core user authentication and profile data
   - Referenced by StudentProfile

2. **StudentProfile** (`models/student.py`)
   - Extended student information including demographics and enrollment data
   - Includes risk_label field for dropout prediction (low/medium/high)
   - References User model

3. **Academic Records** (`models/academic.py`)
   - Semester-wise GPA and backlogs
   - References StudentProfile

4. **Attendance** (`models/attendance.py`)
   - Semester-wise attendance tracking
   - References StudentProfile

5. **Financial Records** (`models/financial.py`)
   - Tuition status, scholarship, and loan dependency
   - References StudentProfile

6. **Curricular Units** (`models/curricular.py`)
   - Semester-wise enrolled/approved units and grades
   - References StudentProfile

#### API Routes

Each model has corresponding route handlers:
- `routes/student_routes.py` - Student profile CRUD and CSV import
- `routes/academic_routes.py` - Academic record management
- `routes/attendance_routes.py` - Attendance tracking
- `routes/financial_routes.py` - Financial record management
- `routes/curricular_routes.py` - Curricular unit management

All routes support:
- CSV bulk import at `/{entity}/csv` endpoints
- Individual CRUD operations
- Patching for partial updates

#### Utilities (`utils/utils.py`)
- User ID generation with role-based prefixes
- Email and user ID uniqueness validation

### Key Design Patterns

1. **Blueprint-based Routing**: Each domain has its own blueprint for modular organization
2. **Reference-based Document Relations**: Uses MongoEngine references for relationships between documents
3. **JWT Token Authentication**: Stateless authentication with configurable expiry
4. **CSV Bulk Import**: All data models support CSV import for batch operations
5. **Consistent Error Handling**: Standardized JSON error responses with appropriate HTTP status codes

### Environment Variables Required

Create a `.env` file with:
```
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_here
MONGO_URI=mongodb://localhost:27017/  # Or your MongoDB connection string
DB_NAME=SIH  # Optional, defaults to "SIH"
JWT_EXPIRY=3600  # Optional, token expiry in seconds
```

### API Authentication Flow

1. User signs up via `/auth/signup` with name, password, and role
2. System generates unique userId (e.g., STU-XXXXXXXX)
3. User signs in via `/auth/signin` with userId/email and password
4. Server returns JWT token for authenticated requests
5. Include token in Authorization header: `Bearer <token>`
6. Protected endpoints validate token and extract user context