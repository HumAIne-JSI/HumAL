# Fase di build (Node.js)
FROM node:22-alpine3.19 AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
# Fase di produzione (Nginx)
FROM nginx:1.19.0-alpine AS production
# Copia i file generati dalla fase di build (Node.js)
COPY --from=build /app/dist /app/
#COPY ./dist /app/va2fest
# Copia il file di configurazione nginx.conf
COPY nginx.conf /etc/nginx/nginx.conf
# Esponi la porta su cui nginx ascolta
EXPOSE 80
# Comando per avviare nginx
CMD ["nginx", "-g", "daemon off;"]


### 1. Autenticati sul registry Harbor
## docker login harbor.gftinnovation.eu

### 2. Builda l'immagine
## docker build -t humaine-smart-ticketing-fe:1.1.2 .

### 3. Tagga l'immagine per il registry Harbor
## docker tag humaine-smart-ticketing-fe:1.1.2 harbor.gftinnovation.eu/humaine/humaine-smart-ticketing-fe:1.1.2

### 4. Esegui il push
## docker push harbor.gftinnovation.eu/humaine/humaine-smart-ticketing-fe:1.1.2