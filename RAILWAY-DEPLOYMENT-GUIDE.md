# 🚂 Railway Deployment Guide - Document Generator

## 🎯 Waarom Railway na Google Cloud Frustratie?

**Na 60+ uur Google Cloud problemen, Railway is de oplossing:**
- ✅ **15 minuten deployment** (vs 60+ uur Google Cloud)
- ✅ **€0-5/maand** (vs €55-125+ Google Cloud)  
- ✅ **Git push = deployment** (geen Terraform/IAM hell)
- ✅ **Automatische database** (geen Cloud SQL gedoe)
- ✅ **Zero configuration** (geen YAML/permissions)

## 📦 Package Inhoud

```
railway-deployment-package/
├── railway.json              # Railway hoofdconfiguratie
├── backend/                  # Backend applicatie
│   ├── Dockerfile           # Railway-geoptimaliseerd
│   ├── requirements.txt     # Python dependencies
│   └── src/
│       ├── main.py         # Flask app met Railway support
│       └── models/         # Database modellen
├── frontend/                # Frontend applicatie  
│   ├── Dockerfile          # Nginx + React
│   ├── nginx.conf          # Railway nginx config
│   └── package.json        # Node.js dependencies
└── docs/                   # Documentatie
    ├── RAILWAY-DEPLOYMENT-GUIDE.md
    └── TROUBLESHOOTING.md
```

## 🚀 Stap-voor-Stap Deployment (15 minuten)

### Stap 1: Repository Voorbereiden (3 min)

```bash
# 1. Ga naar je bestaande repository
cd ~/document-generator-repo

# 2. Kopieer Railway bestanden
cp -r /path/to/railway-deployment-package/* .

# 3. Commit wijzigingen
git add .
git commit -m "🚂 Prepare for Railway deployment"
git push origin main
```

### Stap 2: Railway Account & Backend (5 min)

1. **Account aanmaken:**
   - Ga naar **railway.app**
   - Klik **"Start a New Project"**
   - **"Login with GitHub"**
   - Autoriseer Railway toegang

2. **Backend deployen:**
   - **"Deploy from GitHub repo"**
   - Selecteer je **document-generator** repository
   - Railway detecteert automatisch `railway.json`
   - Klik **"Deploy"**

**Railway doet nu automatisch:**
- ✅ Docker image bouwen
- ✅ Container deployen  
- ✅ HTTPS certificaat
- ✅ Custom domain toewijzen

### Stap 3: Database Toevoegen (2 min)

1. In je Railway project dashboard
2. Klik **"+ New Service"**
3. Selecteer **"PostgreSQL"**

**Railway maakt automatisch:**
- ✅ PostgreSQL database
- ✅ DATABASE_URL environment variable
- ✅ Private networking tussen services

### Stap 4: Environment Variables (3 min)

1. Ga naar je backend service
2. Klik **"Variables"** tab
3. Voeg toe:

```bash
JWT_SECRET_KEY=your-super-secret-jwt-key-here-change-this
FLASK_ENV=production
SECRET_KEY=another-secret-key-for-flask-sessions
```

**DATABASE_URL wordt automatisch ingesteld door Railway!**

### Stap 5: Frontend Deployment (2 min)

**Optie A: Separate Railway Service (Aanbevolen)**
1. In Railway dashboard: **"+ New Service"**
2. **"GitHub Repo"** → Selecteer zelfde repository
3. **"Root Directory"** → `frontend`
4. Railway detecteert automatisch Node.js/React

**Optie B: Vercel (Sneller voor frontend)**
1. Ga naar **vercel.com**
2. **"Import GitHub repository"**
3. **Framework:** React
4. **Root Directory:** `frontend`
5. **Environment Variables:**
```bash
VITE_API_BASE_URL=https://your-railway-backend-url.railway.app/api
```

## 🔧 Configuratie Details

### Railway.json Uitleg
```json
{
  "build": {
    "builder": "DOCKERFILE",           // Gebruik Dockerfile
    "dockerfilePath": "backend/Dockerfile"  // Pad naar Dockerfile
  },
  "deploy": {
    "startCommand": "gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 src.main:app",
    "healthcheckPath": "/health",      // Health check endpoint
    "restartPolicyType": "ON_FAILURE"  // Restart bij crashes
  }
}
```

### Backend Dockerfile Features
- ✅ **Railway PORT support** - Gebruikt $PORT environment variable
- ✅ **Health checks** - `/health` endpoint voor monitoring
- ✅ **Non-root user** - Security best practice
- ✅ **Optimized caching** - Snellere builds
- ✅ **PYTHONPATH fix** - Geen import problemen

### Frontend Nginx Config
- ✅ **SPA routing** - React Router support
- ✅ **Static asset caching** - Performance optimization
- ✅ **Security headers** - XSS/CSRF protection
- ✅ **Gzip compression** - Snellere loading

## 💰 Kosten Breakdown

### Railway Pricing (Perfect voor jou)
```bash
# Hobby Plan - GRATIS
€0/maand    - 500 execution hours
            - 1GB RAM per service
            - 1GB disk storage

# Pro Plan - Als je groeit
€5/maand    - Unlimited execution hours
            - 8GB RAM per service  
            - 100GB disk storage
            - Custom domains

# Jouw Document Generator gebruik:
Backend:     ~100 hours/maand
Frontend:    ~50 hours/maand
Database:    ~30 hours/maand
Total:       ~180 hours = GRATIS TIER!

# Werkelijke kosten: €0/maand
```

## 🎯 Na Deployment

### Je krijgt automatisch:
- ✅ **Backend URL:** `https://your-backend.railway.app`
- ✅ **Frontend URL:** `https://your-frontend.railway.app`
- ✅ **Database:** PostgreSQL automatisch geconfigureerd
- ✅ **HTTPS:** Automatische SSL certificaten
- ✅ **Monitoring:** Real-time logs en metrics
- ✅ **CI/CD:** Git push = automatische deployment

### Custom Domain (Optioneel)
```bash
# 1. Railway dashboard → Settings → Domains
# 2. Add domain: "documentgenerator.jouwdomein.nl"
# 3. Update DNS bij je provider:
CNAME documentgenerator your-app.railway.app

# Railway configureert automatisch SSL!
```

## 🔄 CI/CD Pipeline

**Railway = Automatische CI/CD:**
```bash
# Elke git push naar main branch:
1. Railway detecteert wijzigingen
2. Bouwt nieuwe Docker image  
3. Deployt automatisch
4. Zero-downtime deployment
5. Rollback mogelijk met 1 klik

# Geen GitHub Actions nodig!
# Geen YAML configuratie!
# Gewoon git push = deployment!
```

## 📊 Monitoring & Logs

### Real-time Monitoring
1. Railway dashboard → je service
2. **"Deployments"** tab → Live deployment logs
3. **"Metrics"** tab → CPU/Memory/Requests
4. **"Logs"** tab → Application logs

### Health Checks
- ✅ **Backend:** `https://your-backend.railway.app/health`
- ✅ **Frontend:** `https://your-frontend.railway.app/health`
- ✅ **API Info:** `https://your-backend.railway.app/api`

## 🚨 Troubleshooting

### Build Fails
```bash
# Check Railway logs:
1. Dashboard → Service → Deployments
2. Klik op failed deployment  
3. Bekijk build logs

# Common fixes:
- Dockerfile path correct in railway.json?
- Requirements.txt compleet?
- PYTHONPATH correct ingesteld?
```

### Database Connection Issues
```bash
# Check environment variables:
1. Dashboard → Service → Variables
2. Controleer DATABASE_URL aanwezig
3. Test connection in application logs

# Railway PostgreSQL is automatisch geconfigureerd!
```

### Port Issues
```bash
# Railway gebruikt $PORT environment variable
# Backend: Luistert op 0.0.0.0:$PORT (✅ geconfigureerd)
# Frontend: Nginx luistert op $PORT (✅ geconfigureerd)
```

### Frontend API Connection
```bash
# Update frontend environment:
VITE_API_BASE_URL=https://your-railway-backend-url.railway.app/api
# Of kopieer `frontend/.env.example` naar `frontend/.env` en pas de URL aan

# Of update nginx.conf proxy_pass:
location /api/ {
    proxy_pass https://your-railway-backend-url.railway.app/api/;
}
```

## 🔄 Migratie van Google Cloud

### Als je data hebt in Google Cloud:
```bash
# 1. Export Google Cloud database
gcloud sql export sql your-instance gs://bucket/backup.sql

# 2. Download backup  
gsutil cp gs://bucket/backup.sql ./

# 3. Import in Railway PostgreSQL
# Get connection string from Railway dashboard
psql $DATABASE_URL < backup.sql
```

### Fresh start (Aanbevolen na jouw frustratie):
```bash
# Gewoon deployen op Railway
# Laat Google Cloud links liggen
# Start fresh zonder legacy problemen
# Bespaar jezelf meer frustratie!
```

## 🏆 Waarom Railway Perfect Is Voor Jou

**Na 60+ uur Google Cloud nightmare:**

| Aspect | Google Cloud | Railway |
|--------|-------------|---------|
| **Setup tijd** | 60+ uur | 15 minuten |
| **Maandkosten** | €55-125+ | €0-5 |
| **Configuratie** | 50+ bestanden | 1 bestand |
| **Deployment** | Complex YAML | Git push |
| **Database** | Cloud SQL setup hell | 1 klik PostgreSQL |
| **Monitoring** | Complex setup | Automatisch |
| **Support** | Ticket systeem | Responsive team |
| **Frustratie** | 😡😡😡😡😡 | 😊😊😊😊😊 |

## 🎉 Success Checklist

**Na deployment heb je:**
- ✅ **Werkende app** binnen 15 minuten
- ✅ **Automatische HTTPS** en custom domains
- ✅ **Zero-downtime deployments** bij updates
- ✅ **Real-time monitoring** en logs
- ✅ **Predictable kosten** (€0-5/maand)
- ✅ **No vendor lock-in** - makkelijk te migreren
- ✅ **Developer happiness** - focus op je app!

## 🚀 Volgende Stappen

1. **Deploy nu** - Stop de Google Cloud frustratie
2. **Test thoroughly** - Zorg dat alles werkt
3. **Add custom domain** - Professional appearance
4. **Monitor usage** - Blijf binnen gratis tier
5. **Focus on features** - Niet op infrastructure!

**Railway = Developer happiness na Google Cloud hell! 🚂**

Wil je hulp bij de deployment? Ik kan je stap-voor-stap begeleiden!

