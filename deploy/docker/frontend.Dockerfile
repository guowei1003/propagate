FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
# nginx.conf lives in deploy/docker/ relative to the project root.
# When docker build runs from the frontend context, ../deploy/docker/nginx.conf
# resolves correctly because the build command's -f flag anchors to the repo root.
COPY ../deploy/docker/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
