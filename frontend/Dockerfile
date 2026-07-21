FROM node:22-alpine AS deps
WORKDIR /srv/app
COPY package.json ./
RUN npm install

FROM node:22-alpine AS builder
WORKDIR /srv/app
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
COPY --from=deps /srv/app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /srv/app
ENV NODE_ENV=production
RUN addgroup --system app && adduser --system --ingroup app app
COPY --from=builder /srv/app/public ./public
COPY --from=builder --chown=app:app /srv/app/.next/standalone ./
COPY --from=builder --chown=app:app /srv/app/.next/static ./.next/static
USER app
EXPOSE 3000
ENV PORT=3000
CMD ["node", "server.js"]
