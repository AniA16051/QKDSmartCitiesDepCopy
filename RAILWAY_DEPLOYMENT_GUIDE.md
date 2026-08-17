# Railway.app Deployment Guide for QKD Dashboard

Deploy your entire QKD dashboard to Railway.app for **FREE** (with limits). Both you and your friend can access the same live dashboard with no VPS costs.

---

## What is Railway?

Railway is a modern hosting platform that:
- Runs Docker containers for free
- Free tier: 500 hours/month (plenty for this)
- Auto-deploys from GitHub
- No credit card required initially
- Easy to set up

**Cost:** FREE (with free tier limits)

---

## Phase 1: Prerequisites

### 1. Create a GitHub Account (if you don't have one)

Go to [github.com](https://github.com) and sign up.

### 2. Push Your Project to GitHub

On your Windows machine, in PowerShell:

```powershell
cd D:\AniA\QKDNEW
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```

Replace `<your-username>` and `<your-repo-name>` with your actual GitHub values.

If Git isn't installed, download it from [git-scm.com](https://git-scm.com).

### 3. Create Railway Account

Go to [railway.app](https://railway.app) and click **"Start for Free"**

Sign in with GitHub (easiest option).

---

## Phase 2: Prepare Your Project for Railway

Railway reads your `docker-compose.yml` and deploys everything automatically.

Your current `docker-compose.yml` is already compatible! ✅

However, we need to make one small adjustment for Railway's environment.

### Edit docker-compose.yml

Open `docker-compose.yml` and find the mosquitto service:

**BEFORE:**
```yaml
mosquitto:
  image: eclipse-mosquitto:latest
  container_name: qkd_mosquitto
  ports:
    - "0.0.0.0:1883:1883"  # Listen on all interfaces
```

**AFTER:**
```yaml
mosquitto:
  image: eclipse-mosquitto:latest
  # Don't set container_name on Railway
  ports:
    - "1883:1883"  # Railway handles networking automatically
```

Same for the dashboard service — remove `container_name` and simplify ports:

**BEFORE:**
```yaml
dashboard:
  build:
    context: .
    dockerfile: docker/Dockerfile.dashboard
  container_name: qkd_dashboard
  ports:
    - "0.0.0.0:8501:8501"
```

**AFTER:**
```yaml
dashboard:
  build:
    context: .
    dockerfile: docker/Dockerfile.dashboard
  ports:
    - "8501:8501"
```

Do the same for `admin-node` (remove `container_name`).

---

## Phase 3: Deploy to Railway

### Step 1: Create a Railway Project

1. Go to [railway.app/dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access GitHub
5. Select your repo (`QKDNEW` or whatever you named it)
6. Select the `main` branch

### Step 2: Railway Auto-Detects docker-compose.yml

Railway will see your `docker-compose.yml` and automatically:
- Build all containers
- Start all services
- Expose ports

This takes 2-5 minutes. You can watch the build log in real-time.

### Step 3: Get Your Railway URL

Once deployed, Railway auto-assigns a domain like:

```
https://qkd-dashboard-production.up.railway.app
```

This is your live URL. Both users access this same URL.

---

## Phase 4: Access the Dashboard

### Open in Browser

```
https://qkd-dashboard-production.up.railway.app
```

You should see the login page.

### Log in as Admin

- **Username:** admin
- **Password:** admin@qkd2026

If it loads, you're live! 🎉

---

## Phase 5: Create a User for Your Friend

### In the Dashboard:

1. Log in as admin
2. Click the **Settings** tab (bottom)
3. Find **"Create New User"**
4. Enter:
   - Username: `friend` (or any name)
   - Password: (pick any secure password)
   - Role: `user`
5. Click **Create User**

### Give Your Friend the Link

Tell your friend:

```
https://qkd-dashboard-production.up.railway.app
```

And credentials:
```
Username: friend
Password: <whatever-you-set>
```

---

## Phase 6: Test Synchronization

1. You log in as `admin` in one browser
2. Your friend opens the same link and logs in as `friend` in another browser
3. Both should see:
   - The same node status
   - The same live metrics
   - Real-time updates sync between both

If metrics update together, it's working! ✅

---

## Phase 7: Custom Domain (Optional)

By default, you get `qkd-dashboard-production.up.railway.app`.

To use a custom domain like `qkd.example.com`:

### 1. Buy a domain

From Namecheap, GoDaddy, or Freenom (free .xyz/.ml/.tk)

### 2. In Railway:

- Go to your project
- Click **Settings**
- Find **Domains**
- Add your custom domain
- Follow Railway's instructions to update DNS

Then both users access:

```
https://qkd.example.com
```

---

## Phase 8: What if Something Goes Wrong?

### Dashboard won't load

Check the logs in Railway:

1. Go to your Railway project dashboard
2. Click on the `dashboard` service
3. Click **Logs** tab
4. Look for error messages

Common issues:
- Missing dependencies (check `requirements.txt`)
- Port conflict (Railway handles this automatically)
- Out of memory (free tier is limited)

### Rebuild the app

Push a new commit to GitHub and Railway auto-deploys:

```powershell
cd D:\AniA\QKDNEW
git add .
git commit -m "Fix: update config"
git push origin main
```

Railway detects the push and redeploys automatically (~3 minutes).

### Check service status

In Railway dashboard:
- Green = running
- Yellow = building
- Red = failed

Click each service to see detailed logs.

---

## Phase 9: Understand Railway's Free Tier

### Limits:

- **500 hours/month** per project (that's ~21 days of continuous runtime)
- **2 projects** at a time
- **4 GB RAM** total per project
- **100 GB/month** bandwidth

### For this project:

- Dashboard runs 24/7 = ~730 hours/month
- **You'll exceed the free limit if it runs constantly for a month**

### Solutions:

**Option A: Keep it within free tier**
- Turn it off when not in use
- Use it for demos only
- Stop the project when not testing

**Option B: Upgrade to paid plan**
- $5-10/month for unlimited hours
- Automatic scaling
- Professional support

**Option C: Use Railway's "sleep on inactivity"**
- Railway auto-stops services after ~30 min inactivity
- Wakes up when accessed
- Good for demos

---

## Phase 10: How to Manage Your Railway Project

### Stop a service:

1. Click the service name
2. Click **Settings**
3. Click **Remove Service**

### Restart everything:

1. Click **Settings** (top right)
2. Click **Restart**

### View real-time logs:

Each service has a **Logs** tab showing live output.

### Delete the project:

1. Go to project **Settings**
2. Scroll to **Danger Zone**
3. Click **Delete Project**

---

## Phase 11: Update Code After Deployment

If you change code locally and want to update the live app:

### Step 1: Commit and push to GitHub

```powershell
cd D:\AniA\QKDNEW
git add .
git commit -m "Feature: update dashboard"
git push origin main
```

### Step 2: Railway auto-deploys

Railway watches your GitHub repo. Any push to `main` automatically:
- Rebuilds Docker images
- Restarts services
- Goes live

You don't need to do anything else. Just wait 2-5 minutes for rebuild.

---

## Phase 12: Troubleshooting Guide

### Issue: Dashboard takes a long time to load

**Cause:** First load builds the Streamlit cache. Subsequent loads are fast.

**Fix:** Wait 30 seconds on first load. Be patient.

### Issue: "Connection refused" error

**Cause:** Broker is reachable but services aren't communicating.

**Fix:** 
1. Check Railway logs for each service
2. Verify `BROKER_HOST` env variable is set correctly (should be `mosquitto` for internal communication)
3. Restart the project

### Issue: Friend can't access the URL

**Cause:** 
- URL is wrong
- Railway service is down
- Browser cache issue

**Fix:**
1. Double-check the Railway URL
2. Open in incognito/private browser
3. Check Railway dashboard for red status
4. If red, wait for auto-recovery or restart

### Issue: "Out of memory" error

**Cause:** Free tier has 4GB total. Multiple browser sessions can use it up.

**Fix:**
1. Reduce the number of browser sessions
2. Refresh the page to clear browser memory
3. If consistent, upgrade to paid plan

### Issue: Metrics not updating

**Cause:** MQTT broker connection lost or nodes not sending data.

**Fix:**
1. Check broker logs in Railway
2. Verify network connectivity
3. Restart all services from Railway dashboard

---

## Phase 13: Production Checklist

Before you tell your friend the link works:

- [ ] Railway project created and deployed
- [ ] Dashboard URL loads in browser
- [ ] Can log in as admin
- [ ] Friend user created with credentials
- [ ] Friend can access the same URL
- [ ] Both users see synchronized data
- [ ] Real-time updates working
- [ ] Logs show no errors

---

## Phase 14: Quick Command Reference

### Local development (before deploying):

```powershell
# Initialize Git
git init
git add .
git commit -m "Initial"
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main

# Push updates after changes
git add .
git commit -m "Update description"
git push origin main
```

### Railway commands (via web dashboard):

- **View logs:** Project → Service → Logs
- **Check status:** Project → Services (green = running)
- **Restart:** Project → Settings → Restart
- **Delete:** Project → Settings → Delete Project

---

## Phase 15: Cost Analysis

| Service | Free Tier | Cost | Notes |
|---------|-----------|------|-------|
| Railway hosting | 500 hrs/mo | $0 | Works if used intermittently |
| Custom domain | — | $1-10/yr | Optional, free .xyz available |
| **Total** | — | **$0-1/yr** | Cheapest option |

If you need 24/7 uptime beyond 500 hours/month:
- Upgrade to paid: $5-10/month
- Or use a cheap VPS ($5/month) instead

---

## Phase 16: Comparison: Railway vs VPS

| Feature | Railway | VPS |
|---------|---------|-----|
| Setup time | 10 minutes | 30 minutes |
| Cost (free tier) | $0/mo | N/A |
| Cost (paid) | $5-10/mo | $5-10/mo |
| 24/7 reliability | No (free tier limits) | Yes |
| Scaling | Automatic | Manual |
| Custom domain | Yes | Yes |
| Uptime | 99% | ~99.9% |

**Best for demos/testing:** Railway

**Best for production/24/7:** VPS

---

## Phase 17: Live Deployment Steps (TL;DR)

1. **Push to GitHub:**
   ```powershell
   git init && git add . && git commit -m "Initial" && git push origin main
   ```

2. **Create Railway project:**
   - Go to railway.app
   - Click "New Project"
   - Connect GitHub repo

3. **Wait for deployment** (2-5 minutes)

4. **Access dashboard:**
   ```
   https://qkd-dashboard-production.up.railway.app
   ```

5. **Log in:** admin / admin@qkd2026

6. **Create friend user** in Settings

7. **Share URL** with friend

8. **Both log in** and verify sync

**Total time to live:** ~15 minutes

---

## Next Steps

1. Make sure `docker-compose.yml` is updated (remove `container_name`, simplify ports)
2. Push to GitHub
3. Create Railway account
4. Connect your GitHub repo to Railway
5. Wait for deployment
6. Share the live URL with your friend

Ready to deploy?
