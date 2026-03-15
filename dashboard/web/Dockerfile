FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN corepack enable && yarn global add serve && yarn install --non-interactive

COPY . .

RUN yarn build

EXPOSE 3000

CMD ["sh", "-c", "serve -s dist -l ${PORT:-3000}"]
