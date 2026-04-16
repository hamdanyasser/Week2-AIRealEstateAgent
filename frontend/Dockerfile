# ---------- Frontend ----------
# The React app is pre-built on the host (npm run build).
# This image only copies the static dist/ and a zero-dep Node
# server script — no npm install, no network needed.

FROM node:20-alpine

WORKDIR /app

COPY dist/ dist/
COPY serve.cjs .

EXPOSE 80

CMD ["node", "serve.cjs"]
