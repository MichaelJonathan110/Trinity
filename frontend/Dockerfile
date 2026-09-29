# Frontend image for `docker compose up --build` (dev server with HMR).
# Production hosting is Vercel (static build); this image is for local/full-stack
# Compose runs only.
FROM node:22-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
