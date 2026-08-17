# Ubuntu VPS Deployment Guide for QKD Dashboard

This guide walks you through setting up a live, shared QKD dashboard on an Ubuntu VPS that both you and your friend can access remotely.

---

## Phase 1: Choose & Create Your VPS

### Recommended providers (cheapest first):
- **Hetzner** (~€3/month) - reliable, no credit card required for many locations
- **DigitalOcean** (~$5/month) - very beginner-friendly, great docs
- **Linode** (~$5/month) - stable, good uptime
- **AWS/Azure** - overkill for this, but works
- **Your home PC** - if you can port-forward and keep it always on

### What to select when creating:
- **OS:** Ubuntu 22.04 LTS or Ubuntu 24.04 LTS
- **CPU:** 1 vCPU is enough
- **RAM:** 2GB minimum (4GB better)
- **Storage:** 20GB is fine
- **Region:** Pick one closest to you

### After creation:
- You'll get a **root password** or **SSH key**
- Note down the **public IP address** (looks like `203.0.113.42`)
- This is your `<server-ip>`

---

## Phase 2: Initial Server Access & Setup

### Step 1: Connect via SSH

From your Windows PowerShell or terminal:

```powershell
ssh root@<server-ip>
```

If using an SSH key instead of password:

```powershell
ssh -i "C:\path\to\key.pem" root@<server-ip>
```

When prompted, type "yes" to accept the server's fingerprint.

### Step 2: Update the system

Once logged in:

```bash
apt update && apt upgrade -y
```

This takes 2-5 minutes. Wait for it to finish.

### Step 3: Create a non-root user (optional but recommended)

```bash
adduser appuser
```

Follow the prompts (you can skip most, just set a password).

Then give them sudo access:

```bash
usermod -aG sudo appuser
```

From now on, you can log in as:

```bash
ssh appuser@<server-ip>
```

---

## Phase 3: Install Docker

Run this entire block on the server:

```bash
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=\"$(dpkg --print-architecture)\" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### Verify Docker installed:

```bash
docker --version
docker compose version
```

Both should show version numbers.

### Allow your user to run Docker (optional):

If you created a non-root user:

```bash
sudo usermod -aG docker appuser
```

Then log out and back in for this to take effect.

---

## Phase 4: Clone Your Project

### Option A: If you have it on GitHub

```bash
cd /opt
sudo git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo-name>
```

### Option B: If you only have it locally

On your Windows machine:

```powershell
cd D:\AniA\QKDNEW
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/<your-username>/<new-repo-name>.git
git push -u origin main
```

Then on the server:

```bash
cd /opt
git clone https://github.com/<your-username>/<new-repo-name>.git
cd <new-repo-name>
```

### Option C: Direct copy via SCP

If you don't want to use GitHub, copy the folder directly:

```powershell
scp -r D:\AniA\QKDNEW appuser@<server-ip>:/opt/qkd-dashboard
```

Then on the server:

```bash
cd /opt/qkd-dashboard
```

---

## Phase 5: Start the Docker Stack

From the project root directory on the server:

```bash
sudo docker compose up -d --build
```

This will:
- Build the images (takes 2-5 minutes)
- Start the Mosquitto broker
- Start the admin control node
- Start the Streamlit dashboard

### Check if everything started:

```bash
sudo docker compose ps
```

You should see 3 containers running:
- `qkd_mosquitto`
- `qkd_admin_node`
- `qkd_dashboard`

### View logs:

If something fails:

```bash
sudo docker compose logs -f
```

Press `Ctrl+C` to exit logs.

---

## Phase 6: Access the Dashboard

### From your browser:

Open:

```
http://<server-ip>:8501
```

Replace `<server-ip>` with the actual IP (e.g., `http://203.0.113.42:8501`)

### You should see:
- Login page
- Default credentials shown at the bottom

### Log in as admin:

- **Username:** admin
- **Password:** admin@qkd2026

If the page loads, you're live! 🎉

---

## Phase 7: Create a User for Your Friend

### In the dashboard:

1. Click **Settings** tab (bottom left)
2. Under **Admin Controls**, find **"Create New User"**
3. Enter:
   - Username: (pick any, e.g., `friend`)
   - Password: (pick any, e.g., `MyPassword123`)
   - Role: `user`
4. Click **Create User**

### Give your friend the link:

```
http://<server-ip>:8501
```

And the credentials:

```
Username: friend
Password: MyPassword123
```

---

## Phase 8: Test Both Users See the Same Dashboard

1. You log in as `admin` in one browser
2. Your friend opens the same link and logs in as `friend` in another browser
3. Both should see:
   - The same node status
   - The same live metrics
   - The same real-time updates

If they are in sync, you have succeeded. Both screens should update together because they're connected to the same MQTT broker.

---

## Phase 9: Keep the App Running Permanently

The `docker compose up -d` command starts the containers in detached mode, which means they'll keep running even if you disconnect.

### To ensure restart after server reboot:

In your `docker-compose.yml`, verify each service has:

```yaml
restart: unless-stopped
```

This is already in your project, so you're good.

### If you need to stop/restart:

```bash
cd /opt/qkd-dashboard
sudo docker compose stop          # Stop all containers
sudo docker compose start         # Start them again
sudo docker compose restart       # Restart them
sudo docker compose down          # Remove containers (data persists)
```

---

## Phase 10: Add HTTPS (Optional but Recommended)

For a production setup, add a domain and SSL certificate.

### Get a domain:
- Buy from Namecheap, GoDaddy, or Route53
- Point it to your server's IP

### Install Nginx and Certbot:

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

### Create Nginx config:

```bash
sudo nano /etc/nginx/sites-available/qkd-dashboard
```

Paste this (replace `qkd.example.com` with your domain):

```nginx
server {
    listen 80;
    server_name qkd.example.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Save with `Ctrl+O`, `Enter`, `Ctrl+X`.

### Enable the config:

```bash
sudo ln -s /etc/nginx/sites-available/qkd-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Get SSL certificate:

```bash
sudo certbot --nginx -d qkd.example.com
```

Now access via:

```
https://qkd.example.com
```

---

## Phase 11: Troubleshooting

### Dashboard won't load

Check if the container is running:

```bash
sudo docker compose ps
```

If `qkd_dashboard` is not running:

```bash
sudo docker compose logs qkd_dashboard
```

Look for error messages. Common issues:
- Port 8501 already in use
- Out of memory
- Missing dependencies

Restart:

```bash
sudo docker compose down
sudo docker compose up -d --build
```

### Broker connection fails

Check the broker logs:

```bash
sudo docker compose logs qkd_mosquitto
```

### Friend can't connect

- Confirm the server IP is correct
- Check firewall allows port 8501
- Try `telnet <server-ip> 8501` from your friend's computer

On most VPS providers, ports are open by default. If not:

```bash
sudo ufw allow 8501
sudo ufw allow 1883
```

---

## Phase 12: Make It Even Better (Optional)

### Automatic backups
Store your keystore data:

```bash
tar -czf qkd-backup-$(date +%Y%m%d).tar.gz /opt/qkd-dashboard/docker/shared_keystore
```

### Monitor uptime
Add monitoring via Uptime Robot (free tier) to alert you if the server goes down.

### Logs rotation
By default, Docker logs can get large. Set log limits in `docker-compose.yml`:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## Phase 13: Your Live Deployment Checklist

Before you call your friend:

- [ ] VPS created and you can SSH in
- [ ] Docker installed and working
- [ ] Project cloned to `/opt/`
- [ ] `docker compose up -d --build` completed
- [ ] Dashboard loads at `http://<server-ip>:8501`
- [ ] You can log in as admin
- [ ] Friend user created with credentials
- [ ] Both users can see the same dashboard
- [ ] Metrics update in real-time for both
- [ ] MQTT broker is reachable

---

## Phase 14: Share the Live Link

Once everything works:

**Tell your friend:**

> Open this link in your browser:
> 
> `http://<server-ip>:8501`
> 
> Log in with:
> - Username: `friend`
> - Password: `MyPassword123`
>
> You should see the same dashboard I see. If you refresh, you'll see live updates.

---

## Quick Command Reference

```bash
# SSH into server
ssh appuser@<server-ip>

# Navigate to project
cd /opt/qkd-dashboard

# Start everything
sudo docker compose up -d --build

# Check status
sudo docker compose ps

# View logs
sudo docker compose logs -f

# Stop everything
sudo docker compose down

# Restart a specific container
sudo docker compose restart qkd_dashboard
```

---

## Need Help?

Common questions:

**Q: How much does this cost?**
A: $5-10/month for a basic VPS. The app uses minimal CPU/RAM.

**Q: What if I want to stop paying and remove the VPS?**
A: Delete the VPS from your provider's dashboard. All data is lost unless you backed it up.

**Q: Can I run this on my home PC instead?**
A: Yes, but you'd need to port-forward 8501 and 1883 on your router, and your PC must stay on 24/7.

**Q: What if the server crashes?**
A: The containers have `restart: unless-stopped`, so they'll auto-restart. If the whole server crashes, you need to SSH back in and restart Docker, but the data persists.

**Q: Can my friend create a new user too?**
A: Only the admin can create users. Your friend (logged in as user) cannot create new accounts.

**Q: How do I change the default admin password?**
A: Delete the `.users.json` file in the dashboard folder, or edit it directly. The app will regenerate it from the code defaults on restart.

---

## Next Steps

1. Pick a VPS provider
2. Create a server
3. Follow Phase 2 through Phase 8
4. Test with your friend
5. If it works, you're done — it's live!
