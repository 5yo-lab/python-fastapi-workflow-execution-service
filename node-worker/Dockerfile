FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --include=dev
COPY . .
RUN npm run build
RUN npm prune --omit=dev
CMD ["npm", "start"]