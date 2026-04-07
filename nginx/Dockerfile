# STEP 1: Build React app
FROM node:18 AS build

WORKDIR /app
COPY frontend ./frontend
WORKDIR /app/frontend

RUN npm install
RUN npm run build

# STEP 2: Serve with Nginx
FROM nginx:alpine

COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/build /usr/share/nginx/html