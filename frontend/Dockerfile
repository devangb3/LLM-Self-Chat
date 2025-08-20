# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Define the build argument
ARG REACT_APP_API_URL

# Set the environment variable for the build process
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built app from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration template
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Expose port
EXPOSE 8080

# Start nginx
CMD ["nginx", "-g", "daemon off;"] 