# Estágio 1: Build da aplicação React (Vite)
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# A variável de ambiente precisa estar presente no build para o Vite compilar corretamente.
# No entanto, como usaremos o Nginx para fazer o proxy da rota /api, o Vite não precisa
# saber o IP externo real do backend, apenas o caminho relativo.
ENV VITE_API_URL=""
RUN npm run build

# Estágio 2: Servidor Nginx para os arquivos estáticos
FROM nginx:alpine
# Copiar os arquivos gerados no estágio 1
COPY --from=builder /app/dist /usr/share/nginx/html
# Copiar a nossa configuração personalizada do Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
