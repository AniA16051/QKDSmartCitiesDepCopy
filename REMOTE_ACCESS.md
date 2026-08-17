# Free remote access from your own computer

This mode runs the full Compose stack on your computer and opens only the
dashboard through a temporary Cloudflare Quick Tunnel. Mosquitto and the
control-center remain private inside the Docker network.

## Start

1. Copy `.env.example` to `.env` and replace both password values with long,
   unique passwords.
2. In PowerShell, from the project directory, run:

   ```powershell
   docker compose --env-file .env -f docker-compose.yml -f docker-compose.tunnel.yml up -d --build
   ```

3. Get the public URL:

   ```powershell
   docker compose -f docker-compose.yml -f docker-compose.tunnel.yml logs cloudflared
   ```

   Copy the `https://...trycloudflare.com` URL from the log and send it to your
   users. They sign in as `admin` or `user` with the passwords from `.env`.

## Stop

```powershell
docker compose -f docker-compose.yml -f docker-compose.tunnel.yml down
```

## Important limits

Quick Tunnels are free and need no domain, but the URL changes whenever the
tunnel restarts and Cloudflare documents them as testing/development only.
Your computer must stay powered on, online, and running Docker. For a stable
URL later, create a free Cloudflare account and configure a named tunnel with a
domain you control.
