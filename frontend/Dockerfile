# Multi-stage build for React application
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files first for dependency caching
COPY package*.json ./

# Install dependencies (need dev dependencies for build)
RUN npm ci

# Copy source code
COPY . .

# Build the React application
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built React app from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Create non-root user for security
RUN addgroup -g 1001 -S nginx-group && \
    adduser -S nginx-user -u 1001 -G nginx-group

# Update nginx.conf to run as non-root user
RUN sed -i 's/user nginx;/user nginx-user;/' /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]