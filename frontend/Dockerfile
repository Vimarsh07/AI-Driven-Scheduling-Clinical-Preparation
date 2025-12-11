# frontend/Dockerfile

FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the frontend source
COPY . .

# Vite dev server port
EXPOSE 5173

# For MVP we run the dev server inside the container.
# In production you'd likely use a static build + nginx.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
