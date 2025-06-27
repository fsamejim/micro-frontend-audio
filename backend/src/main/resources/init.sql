-- Create database if not exists
CREATE DATABASE IF NOT EXISTS audiotranslationdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user if not exists and set password
CREATE USER IF NOT EXISTS 'sammy'@'localhost' IDENTIFIED BY 'password123';

-- Grant privileges to sammy user
GRANT ALL PRIVILEGES ON audiotranslationdb.* TO 'sammy'@'localhost';
FLUSH PRIVILEGES;

-- Switch to the new database
USE audiotranslationdb;

-- Create users table if not exists
CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    active BOOLEAN DEFAULT TRUE,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
);

-- Insert initial admin user if not exists
-- Admin credentials: username='admin', password='admin123' (BCrypt hashed below)
INSERT INTO users (username, password, email, active)
SELECT 'admin', '$2a$10$DxDjxrTikQBAybXht4EgXuM1MsdbgSfoUkFqp0bD4Oo.KXq6ht5Uy', 'admin@example.com', true
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE username = 'admin'
); 