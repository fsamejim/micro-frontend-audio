# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a full-stack web application consisting of:
1. **Frontend**: React application with TypeScript, using React Router for navigation and JWT for authentication
2. **Backend**: Spring Boot 3.2.3 Java application with Spring Security, JPA, and JWT authentication
3. **Database**: MySQL database for data persistence

## Commands Reference

### Backend (Spring Boot) Commands

Run these commands from the `backend/` directory:

```bash
# Build the project
./gradlew build

# Run the Spring Boot application directly
./gradlew bootRun

# Build WAR file only
./gradlew war

# Run tests
./gradlew test

# Run specific test
./gradlew test --tests "com.example.frontbackweb.PasswordHashTest"

# Generate password hash
./gradlew run -PmainClass=com.example.frontbackweb.util.PasswordHashGenerator

# Clean build directory
./gradlew clean

# Show project dependencies
./gradlew dependencies

# Build without running tests
./gradlew build -x test
```

### Frontend (React) Commands

Run these commands from the `frontend/` directory:

```bash
# Install dependencies
npm install

# Start development server
npm start

# Run tests
npm test

# Build for production
npm run build
```

### Docker Commands

Run these commands from the root directory:

```bash
# Start all services (builds images if needed)
docker-compose up --build

# Start in background
docker-compose up -d

# Stop all services  
docker-compose down

# View logs
docker-compose logs -f [service-name]

# Rebuild specific service
docker-compose build [service-name]

# Execute commands in running containers
docker-compose exec backend bash
docker-compose exec database mysql -u sammy -p audiotranslationdb
```

### Database Commands

```bash
# Connect to database in Docker
docker-compose exec database mysql -u sammy -ppassword123 audiotranslationdb

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up database

# View database logs
docker-compose logs database
```

## Architecture Overview

### Authentication Flow

1. **Frontend Authentication**: The frontend uses React Context (AuthContext) to manage authentication state
   - JWT tokens are stored in localStorage
   - Protected routes require authentication
   - Authentication state is maintained across page refreshes

2. **Backend Security**: The backend uses Spring Security with JWT for authentication
   - JWT tokens are generated on login/register
   - Tokens are validated for protected endpoints
   - User passwords are encrypted with BCrypt

3. **API Endpoints** (available at http://localhost:8080):
   - `/api/auth/login`: Authenticate user and return JWT
   - `/api/auth/register`: Register new user and return JWT
   - `/api/auth/me`: Get current user information (requires authentication)
   - `/actuator/health`: Health check endpoint

### Component Structure

1. **Frontend**:
   - React components in `/frontend/src/components/`
   - Authentication context in `/frontend/src/contexts/AuthContext.tsx`
   - API services in `/frontend/src/services/`
   - Type definitions in `/frontend/src/types/`

2. **Backend**:
   - Java controllers in `/backend/src/main/java/com/example/frontbackweb/controller/`
   - Models in `/backend/src/main/java/com/example/frontbackweb/model/`
   - Security configuration in `/backend/src/main/java/com/example/frontbackweb/config/`
   - JWT implementation in `/backend/src/main/java/com/example/frontbackweb/security/`

## Database Configuration

The application uses a MySQL database running in Docker with the following configuration:
- Database name: `audiotranslationdb`
- Username: `sammy`
- Password: `password123`
- **Docker internal URL**: `jdbc:mysql://database:3306/audiotranslationdb`
- **External access**: `localhost:3307` (mapped from container port 3306)

The database schema is managed manually, not through Hibernate's auto-generation. Database initialization happens automatically via Docker volume mount of `init.sql`.

## Development Environment

**For Docker deployment (recommended):**
- Docker Desktop
- Docker Compose

**For local development:**
- Java 21 or newer (for backend development)
- Node.js (latest LTS version) (for frontend development)
- IDE of choice (IntelliJ IDEA, VS Code, etc.)