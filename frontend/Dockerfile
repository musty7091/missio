FROM node:22-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine

ENV MISSIO_BACKEND_API_ORIGIN=https://missio-api-278096126804.europe-west1.run.app
ENV MISSIO_BACKEND_API_HOST=missio-api-278096126804.europe-west1.run.app

COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
