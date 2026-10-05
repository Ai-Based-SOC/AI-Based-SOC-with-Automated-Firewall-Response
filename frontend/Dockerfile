FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./

RUN npm ci --include=optional && npm install --no-save @rollup/rollup-linux-x64-musl@4.60.0

COPY . .

ARG VITE_API_URL=/api/v1
ARG VITE_WS_BASE_URL=

ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_WS_BASE_URL=${VITE_WS_BASE_URL}

RUN npm run build


FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]