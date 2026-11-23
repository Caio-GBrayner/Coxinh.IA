# Front do Coxinh.IA: o Node compila o React e o nginx serve os arquivos estáticos.
# O nginx também repassa /api para o serviço `api`, como o proxy do Vite faz no
# desenvolvimento. Assim o navegador fala com uma única origem e não precisa de CORS.

FROM node:24-bookworm-slim AS build
WORKDIR /app

# O package-lock.json está fora de sincronia (faltam @emnapi/core e @emnapi/runtime).
# O npm 11.6.2 aceita esse lockfile; versões mais novas recusam o `npm ci`.
# Remover esta linha depois de regenerar o lockfile com `npm install`.
RUN npm install -g npm@11.6.2 --no-audit --no-fund

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .
# Vazio: o cliente usa o padrão /api, servido pelo próprio nginx.
ENV VITE_API_URL=""
RUN npm run build


FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
