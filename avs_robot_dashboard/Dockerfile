# Multi-stage Dockerfile for AVS Robot Dashboard
# Optimized for low RAM usage (4GB constraint)

# Stage 1: Build React Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./
COPY frontend/config-overrides.js ./

# Install dependencies
RUN npm ci --only=production

# Copy frontend source
COPY frontend/public ./public
COPY frontend/src ./src

# Build the frontend
RUN npm run build

# Stage 2: Python Backend Runtime
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install system dependencies for OpenCV and other libraries
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python dependencies
# Use CPU-only PyTorch to save memory
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend code
COPY backend/ /app/backend/

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/frontend/build /app/frontend/build

# Install simple HTTP server to serve frontend
RUN pip install --no-cache-dir aiohttp

# Create startup script
RUN echo '#!/bin/bash\n\
# Start Python backend\n\
cd /app/backend && python3 main.py &\n\
BACKEND_PID=$!\n\
\n\
# Start frontend server\n\
cd /app/frontend/build && python3 -m http.server 3000 &\n\
FRONTEND_PID=$!\n\
\n\
# Wait for both processes\n\
wait $BACKEND_PID $FRONTEND_PID\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose ports
EXPOSE 8081 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python3 -c "import socket; s=socket.socket(); s.connect(('\''localhost'\'', 8081)); s.close()" || exit 1

CMD ["/app/start.sh"]
