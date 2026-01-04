# Multi-stage Dockerfile for Web Robot Controller
# Optimized for low RAM usage (4GB constraint)

# Stage 1: Build React Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/client
COPY client/package*.json ./
RUN npm ci --only=production
COPY client/ ./
RUN npm run build

# Stage 2: Backend + AI Service Runtime
FROM python:3.11-slim AS runtime

# Install Node.js for the backend server
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies for AI service (CPU-only PyTorch for memory efficiency)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install AI service requirements
COPY ai_service/requirements.txt /app/ai_service/
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r /app/ai_service/requirements.txt

# Copy AI service code and model
COPY ai_service/ /app/ai_service/

# Copy Node.js backend dependencies and code
COPY package*.json ./
RUN npm ci --only=production

COPY server/ ./server/

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/client/dist ./client/dist

# Create startup script
RUN echo '#!/bin/bash\n\
# Start AI service in background\n\
cd /app/ai_service && python3 server.py &\n\
AI_PID=$!\n\
\n\
# Start Node.js backend\n\
cd /app && node server/index.js &\n\
NODE_PID=$!\n\
\n\
# Wait for both processes\n\
wait $AI_PID $NODE_PID\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose ports
EXPOSE 8080 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8080/ || exit 1

CMD ["/app/start.sh"]
