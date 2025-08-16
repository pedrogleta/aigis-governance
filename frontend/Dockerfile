FROM node:22-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy rest of the source
COPY . .

EXPOSE 5173

# Run Vite in dev mode, binding to all interfaces so host can access it
CMD ["npm", "run", "dev", "--", "--host"]
