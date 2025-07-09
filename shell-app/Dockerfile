# Multi-stage Dockerfile for Shell App (Host MF)
FROM node:18-alpine AS builder

WORKDIR /workspace

# Copy workspace root files
COPY package*.json ./

# Copy all workspace packages for dependency resolution
COPY shell-app/package*.json ./shell-app/
COPY auth-mf/package*.json ./auth-mf/
COPY audio-mf/package*.json ./audio-mf/
COPY dashboard-mf/package*.json ./dashboard-mf/

# Install all workspace dependencies (including dev for build)
RUN npm ci

# Copy shell-app source code
COPY shell-app/ ./shell-app/

# Build the shell app
WORKDIR /workspace/shell-app
RUN npm run build

# Production stage - serve with nginx
FROM nginx:alpine

# Copy built assets from builder stage
COPY --from=builder /workspace/shell-app/dist /usr/share/nginx/html

# Copy custom nginx configuration for SPA
COPY shell-app/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]