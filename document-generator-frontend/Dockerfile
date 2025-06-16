# Build stage
FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./
COPY pnpm-lock.yaml ./
COPY . .

RUN npm install -g pnpm \
    && pnpm install \
    && pnpm run build

# Production stage
FROM nginx:1.25-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

CMD ["nginx", "-g", "daemon off;"]
