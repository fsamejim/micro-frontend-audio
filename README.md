# Audio Translation Web Application

A full-stack web application with React frontend and Spring Boot backend, featuring user authentication and JWT-based security. This application is fully containerized using Docker for easy deployment and development.

## Features

- 🔐 User authentication with JWT tokens
- 👤 User registration and login system
- 🛡️ Secure password storage using BCrypt
- 🔒 Protected routes in frontend
- 🐳 Full Docker containerization
- 📊 Health checks and monitoring
- 🎨 Modern React UI with responsive design

## Project Structure

```
audio-translation-web/
├── docker-compose.yml         # Docker orchestration
├── docker-test.sh            # Docker testing script
│
├── frontend/                  # React frontend application
│   ├── Dockerfile            # Frontend container build
│   ├── nginx.conf           # Production web server config
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── auth/       # Authentication components
│   │   │   │   ├── Login.tsx
│   │   │   │   ├── Register.tsx
│   │   │   │   └── ProtectedRoute.tsx
│   │   │   └── Dashboard.tsx
│   │   ├── contexts/        # React contexts
│   │   │   └── AuthContext.tsx
│   │   ├── services/        # API services
│   │   │   └── authService.ts
│   │   ├── types/           # TypeScript types
│   │   │   └── auth.ts
│   │   └── App.tsx
│   └── package.json
│
├── backend/                   # Spring Boot backend application
│   ├── Dockerfile            # Backend container build
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/example/frontbackweb/
│   │   │   │   ├── config/         # Configuration classes
│   │   │   │   ├── controller/     # REST controllers
│   │   │   │   ├── model/          # Data models
│   │   │   │   ├── repository/     # Data access layer
│   │   │   │   ├── security/       # JWT security
│   │   │   │   └── service/        # Business logic
│   │   │   └── resources/
│   │   │       ├── application.properties     # Default config
│   │   │       ├── application-docker.properties  # Docker config
│   │   │       └── init.sql       # Database initialization
│   │   └── test/               # Test classes
│   ├── build.gradle           # Backend dependencies
│   └── gradlew               # Gradle wrapper
│
├── translation-service/        # Python FastAPI translation service
│   ├── Dockerfile            # Translation service container build
│   ├── app/
│   │   ├── main.py           # FastAPI application entry point
│   │   ├── models/           # Data models
│   │   │   └── translation_job.py
│   │   └── services/         # Translation pipeline services
│   │       ├── audio_preprocessing_service.py
│   │       ├── transcription_service.py
│   │       ├── text_formatting_service.py
│   │       ├── translation_service.py
│   │       ├── chunk_merging_service.py
│   │       ├── text_cleaning_service.py
│   │       └── tts_service.py
│   ├── requirements.txt      # Python dependencies
│   ├── README.md             # Translation service documentation
│   ├── .env.example         # Environment variables template
│   └── google-credentials.json  # Google Cloud service account key
│
└── README.md                 # Project documentation
```

## Quick Start

### Option 1: Docker (Recommended)

1. Start the application with Docker Compose:
   ```bash
   docker-compose up --build
   ```

2. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8080/api
   - Database: localhost:3307 (MySQL)

3. Default admin credentials:
   - Username: `admin`
   - Password: `admin123`

4. Stop the application:
   ```bash
   docker-compose down
   ```

### Option 2: Local Development

For development without Docker (requires local setup):

1. **Backend**: 
   ```bash
   cd backend
   ./gradlew bootRun
   ```

2. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm start
   ```

3. **Database**: Set up local MySQL with credentials in `application.properties`
   
## Docker Deployment

### Prerequisites
- Docker and Docker Compose installed
- No local MySQL or other services running on ports 3000, 8080, or 3307

### Services Overview
The Docker setup includes three services:
- **Frontend**: React app served by Nginx (port 3000)
- **Backend**: Spring Boot API (port 8080)  
- **Database**: MySQL 8.0 (port 3307)

### Docker Commands

```bash
# Start all services (builds images if needed)
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f [service-name]

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes database data)
docker-compose down -v

# Rebuild specific service
docker-compose build [service-name]
docker-compose up [service-name]

# Execute commands in running containers
docker-compose exec backend bash
docker-compose exec database mysql -u sammy -p audiotranslationdb
```

### Docker Troubleshooting

**Port conflicts:**
```bash
# Check what's using ports
lsof -i :3000
lsof -i :8080  
lsof -i :3307

# Kill conflicting processes
sudo kill -9 <PID>
```

**Database issues:**
```bash
# Reset database volume
docker-compose down -v
docker-compose up database

# Connect to database directly
docker-compose exec database mysql -u root -prootpassword123
```

**Application logs:**
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs database
```

## Architecture

### Services Overview
The application consists of three containerized services:

1. **Frontend** (React + Nginx)
   - Modern React application with TypeScript
   - JWT-based authentication
   - Responsive Material-UI components
   - Production-ready Nginx server

2. **Backend** (Spring Boot)
   - RESTful API with Spring Security
   - JWT token authentication
   - JPA/Hibernate for database access
   - Health checks and monitoring endpoints

3. **Database** (MySQL 8.0)
   - Persistent data storage
   - Automatic initialization with sample data
   - Health checks and connection pooling
   
4. **Translation-Service**
   Please see the detail at: translation-service/README.md

## Authentication Flow

1. **Registration**:
   - User clicks "Register here" on login page
   - Enters username, email, and password
   - On successful registration, redirected to login page

2. **Login**:
   - User enters credentials
   - JWT token is stored in localStorage
   - User is redirected to dashboard

3. **Protected Routes**:
   - Routes are protected using `ProtectedRoute` component
   - Unauthenticated users are redirected to login
   - JWT token is validated on each request

## API Endpoints

All API endpoints are available at `http://localhost:8080/api`:

- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration  
- `GET /api/auth/me` - Get current user (requires JWT)
- `GET /actuator/health` - Application health check

## Troubleshooting

### Docker Issues

**Services won't start:**
```bash
# Check container status
docker-compose ps

# View container logs
docker-compose logs [service-name]

# Restart services
docker-compose restart [service-name]
```

**Port conflicts:**
```bash
# Check what's using the ports
lsof -i :3000  # Frontend
lsof -i :8080  # Backend
lsof -i :3307  # Database

# Kill conflicting processes
sudo kill -9 <PID>
```

**Database issues:**
```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v

# Connect directly to database
docker-compose exec database mysql -u sammy -ppassword123 audiotranslationdb
```

**Clean restart:**
```bash
# Remove all containers and networks
docker-compose down --remove-orphans

# Remove all images and rebuild
docker-compose build --no-cache
docker-compose up
```

## Prerequisites

**For Docker deployment (recommended):**
- Docker Desktop
- Docker Compose

**For local development:**
- Java 21+ (for backend development)
- Node.js 18+ (for frontend development)
- MySQL 8.0+ (for local database)

## Technology Stack

- **Frontend**: React 19, TypeScript, Material-UI, Axios
- **Backend**: Spring Boot 3.2, Spring Security, JWT, JPA/Hibernate
- **Database**: MySQL 8.0
- **Infrastructure**: Docker, Docker Compose, Nginx
- **Build Tools**: Gradle 8.x, npm

## Development Workflow

### Getting Started
1. **Clone and start the application:**
   ```bash
   git clone <repository-url>
   cd audio-translation-web
   docker-compose up --build
   ```

2. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8080/api
   - Database: localhost:3307

3. **Default login credentials:**
   - Username: `admin`
   - Password: `admin123`

### Development Commands

**View logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend  
docker-compose logs -f database
```

**Database access:**
```bash
# Connect to database
docker-compose exec database mysql -u sammy -ppassword123 audiotranslationdb

# Run SQL queries
docker-compose exec database mysql -u sammy -ppassword123 -e "SELECT * FROM users;"
```

**Development cycle:**
```bash
# Stop services
docker-compose down

# Rebuild after code changes
docker-compose build [service-name]

# Start with fresh build
docker-compose up --build
```

## Configuration

The application uses Docker environment variables and configuration files:

- **`docker-compose.yml`**: Service orchestration and environment variables
- **`application-docker.properties`**: Docker-specific Spring Boot configuration
- **`init.sql`**: Database initialization script (auto-executed)

### Key Configuration Points

- **Database**: Automatically initialized with sample admin user
- **JWT Secret**: Configured via environment variables
- **CORS**: Configured to allow frontend-backend communication
- **Health Checks**: All services include health monitoring

## Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature-name`  
3. **Make changes and test**: `docker-compose up --build`
4. **Commit changes**: `git commit -m "Add feature"`
5. **Push to branch**: `git push origin feature-name`
6. **Create Pull Request**

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ using Docker, Spring Boot, and React**



