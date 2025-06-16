# ========= STAGE 1: Build =========
# Gebruik een officiële Node.js image om de React-applicatie te bouwen.
FROM node:20-alpine AS build

# Zet de werkdirectory in de container
WORKDIR /app

# Kopieer de dependency-bestanden en installeer pnpm
COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm

# Installeer de project-dependencies
RUN pnpm install --frozen-lockfile

# Kopieer de rest van de applicatiecode
COPY . .

# Bouw de applicatie voor productie
# De output komt in de /app/dist map
RUN pnpm run build

# ========= STAGE 2: Serve =========
# Gebruik een slanke, officiële NGINX image om de statische bestanden te serveren.
FROM nginx:1.25-alpine

# Kopieer de custom NGINX-configuratie
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Kopieer de gebouwde bestanden uit de vorige "build" stage
COPY --from=build /app/dist /usr/share/nginx/html

# Maak poort 8080 beschikbaar voor NGINX
EXPOSE 8080

# Start NGINX op de voorgrond wanneer de container start
CMD ["nginx", "-g", "daemon off;"]
