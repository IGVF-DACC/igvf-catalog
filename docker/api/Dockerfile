# Development Dockerfile for local development
# Use Node.js 20.12-bookworm-slim as base image
FROM node:20.12-bookworm-slim

# Set working directory
WORKDIR /docker

COPY ./docker/api/entrypoint.sh .
RUN chmod +x ./entrypoint.sh

WORKDIR /catalog-api
# Copy package files
COPY package*.json ./
# Install all dependencies (including dev dependencies for build)
RUN npm ci

# Copy source code
COPY src/ ./src/
COPY config/ ./config/
COPY static/ ./static/
COPY data/schema-config.yaml ./data/schema-config.yaml
COPY tsconfig.json ./
COPY babel.config.js ./

# Expose port
EXPOSE 2023

ENTRYPOINT ["/docker/entrypoint.sh"]

# Start the application
CMD ["npm", "run", "dev:server"]
