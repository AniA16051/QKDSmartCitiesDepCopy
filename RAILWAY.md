# Railway deployment

Railway does **not** run this repository's `docker-compose.yml` as a single
application. It deploys one Railway service per Compose service. The root
`Dockerfile` in this repository is for the public Streamlit dashboard service.

## Create the services

1. Create an empty Railway project.
2. Add a second service from the same GitHub repository, name it
   **mosquitto**, and set `RAILWAY_DOCKERFILE_PATH=docker/Dockerfile.mosquitto`.
   Do not create a public domain for this service. It uses the committed
   Mosquitto configuration and Railway private networking.
3. Add a service from this GitHub repository for the dashboard. Railway will
   automatically use the root `Dockerfile` and bind Streamlit to its assigned
   `PORT`. In **Settings → Deploy**, set the Healthcheck Path to
   `/_stcore/health`.
4. Add another service from the same repository for the control-center worker.
   In its Railway settings set `RAILWAY_DOCKERFILE_PATH=docker/Dockerfile.admin`
   and its start command to `python -m network.control_center`.

## Variables

For both the dashboard and control-center services, configure:

```text
BROKER_HOST=${{mosquitto.RAILWAY_PRIVATE_DOMAIN}}
BROKER_PORT=1883
QKD_ADMIN_PASSWORD=<a long unique password>
QKD_USER_PASSWORD=<a long unique password>
PYTHONUNBUFFERED=1
```

Use the private-network hostname Railway exposes for the Mosquitto service;
do not use `localhost` or expose MQTT ports publicly. The dashboard can start
before the broker: it reconnects automatically.

The dashboard's user file and the shared key store are local container files.
Attach a Railway Volume to the dashboard if users must survive redeployments;
for a multi-service production design, move the shared key store to durable
shared storage instead of relying on a local Docker bind mount.

## Local verification

```powershell
docker compose up --build
```

Then open `http://localhost:8501`. Set `QKD_ADMIN_PASSWORD` and
`QKD_USER_PASSWORD` in a local `.env` file before testing credentials.
