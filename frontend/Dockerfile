FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .

RUN npm run build

EXPOSE 3000

# Production mode — Next.js serves the build output.
# For local development without Docker, use `npm run dev` instead.
CMD ["npm", "run", "start", "--", "-p", "3000"]
