# ⚡ Quick Start - Railway Deployment

## 🎯 15 Minuten van Google Cloud Frustratie naar Werkende App

### Stap 1: Bestanden Kopiëren (2 min)
```bash
# Ga naar je repository
cd ~/document-generator-repo

# Kopieer Railway bestanden (uit deze zip)
cp railway.json .
cp -r backend/ .
cp -r frontend/ .

# Commit
git add .
git commit -m "🚂 Railway deployment ready"
git push origin main
```

### Stap 2: Railway Backend (5 min)
1. Ga naar **railway.app**
2. **"Login with GitHub"**
3. **"Deploy from GitHub repo"** → Selecteer je repo
4. **"+ New Service"** → **"PostgreSQL"**

### Stap 3: Environment Variables (3 min)
In Railway dashboard → Backend service → Variables:
```bash
JWT_SECRET_KEY=your-secret-key-here
FLASK_ENV=production
SECRET_KEY=flask-secret-key
```

### Stap 4: Frontend (5 min)
**Optie A: Railway**
- **"+ New Service"** → **"GitHub Repo"** → Root Directory: `frontend`

**Optie B: Vercel (Sneller)**
- Ga naar **vercel.com** → Import repo → Root: `frontend`
- Environment: `VITE_API_BASE_URL=https://your-railway-backend.railway.app/api`
- Of kopieer `frontend/.env.example` naar `frontend/.env` en pas de URL aan

## ✅ Klaar!

**Je hebt nu:**
- ✅ Backend: `https://your-backend.railway.app`
- ✅ Frontend: `https://your-frontend.railway.app` 
- ✅ Database: PostgreSQL automatisch
- ✅ HTTPS: Automatische SSL
- ✅ CI/CD: Git push = deployment

**Kosten: €0/maand (gratis tier)**

## 🚨 Problemen?

**Build fails?** → Check Railway logs in dashboard
**Database errors?** → DATABASE_URL wordt automatisch ingesteld
**Frontend niet bereikbaar?** → Check nginx.conf en Dockerfile

## 🎉 Success!

Na 60+ uur Google Cloud frustratie → 15 minuten Railway succes!

**Focus nu op je app, niet op infrastructure! 🚂**

