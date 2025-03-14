# Build stage
FROM node:18 AS build

# Set working directory
WORKDIR /app

# Copy package files for dependency installation
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy all frontend files
COPY . .

# Build the React application
RUN npm run build

# Production stage
FROM nginx:1.24

# Copy built React app to Nginx serve directory
COPY --from=build /app/build /usr/share/nginx/html

# Add nginx configuration to properly handle React router
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/

# Expose port 80
EXPOSE 80

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]