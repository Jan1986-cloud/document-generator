# ========= STAGE 1: Build =========
# Gebruik een officiële Node.js image om de React-applicatie te bouwen.
FROM node:20-alpine AS build

# Zet de werkdirectory in de container
WORKDIR /app

# Kopieer de dependency-bestanden
COPY package.json pnpm-lock.yaml ./

# Installeer pnpm en de project-dependencies.
# We gebruiken --no-frozen-lockfile om compatibiliteitsproblemen in de CI-omgeving te voorkomen.
RUN npm install -g pnpm
RUN pnpm install --no-frozen-lockfile

# Kopieer de rest van de applicatiecode
COPY . .

# Bouw de applicatie voor productie
RUN pnpm run build

# ========= STAGE 2: Serve =========
# Gebruik een slanke, officiële NGINX image om de statische bestanden te serveren.
FROM nginx:1.25-alpine

# Kopieer de custom NGINX-configuratie
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Kopieer de gebouwde bestanden uit de vorige "build" stage
COPY --from=build /app/dist /usr/share/nginx/html

# Maak poort 80 beschikbaar voor NGINX
EXPOSE 80

# Start NGINX op de voorgrond wanneer de container start
CMD ["nginx", "-g", "daemon off;"]