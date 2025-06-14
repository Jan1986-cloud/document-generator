# Document Generator

Een complete standalone webapp voor Google Cloud die gebruikersinput omzet naar PDF documenten met Google Docs sjablonen.

## 🚀 Snelle Start

### Vereisten
- Google Cloud Platform account met billing enabled
- Google Workspace account voor Docs/Drive/Sheets integratie
- Node.js 18+ en Python 3.11+
- Docker en Git

### Installatie

1. **Clone de repository**
   ```bash
   git clone <your-repo-url>
   cd document-generator
   ```

2. **Google Cloud Setup**
   ```bash
   chmod +x scripts/setup-gcp.sh
   ./scripts/setup-gcp.sh
   ```

3. **Lokale Development**
   ```bash
   # Backend
   cd document-generator-backend
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # of: venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   cp .env.example .env
   # Bewerk .env met uw configuratie
   python src/main.py
   
   # Frontend (nieuwe terminal)
   cd document-generator-frontend
   pnpm install
   cp .env.example .env
   # Bewerk .env met uw configuratie
   pnpm run dev
   ```

4. **Productie Deployment**
   ```bash
   chmod +x scripts/deploy-to-gcp.sh
   ./scripts/deploy-to-gcp.sh
   ```

## 📁 Project Structuur

```
document-generator/
├── document-generator-backend/     # Flask API backend
├── document-generator-frontend/    # React frontend
├── .github/workflows/             # CI/CD pipelines
├── docs/                         # Documentatie
├── scripts/                      # Setup en deployment scripts
├── terraform/                    # Infrastructure as Code
├── docker-compose.yml            # Lokale development
└── README.md                     # Dit bestand
```

## 🔧 Functionaliteiten

- **Document Generatie**: Automatische PDF generatie vanuit Google Docs sjablonen
- **Multi-tenant**: Ondersteuning voor meerdere organisaties
- **Gebruikersbeheer**: Role-based access control
- **Klant & Product Management**: Volledige CRUD met Google Sheets sync
- **Dashboard**: Modulair widget systeem
- **Mobile Responsive**: Werkt op alle apparaten

## 📚 Documentatie

- [Implementatie Handleiding](docs/implementatie-handleiding.md) - Complete setup instructies
- [Architectuur Document](docs/architectuur_document.md) - Technische specificaties
- [Project Oplevering](docs/project-oplevering.md) - Overzicht van alle componenten

## 🛠️ Development

### Backend Development
```bash
cd document-generator-backend
source venv/bin/activate
python src/main.py
```

### Frontend Development
```bash
cd document-generator-frontend
pnpm run dev
```

### Database Migraties
```bash
cd document-generator-backend
source venv/bin/activate
python -c "from src.main import app; app.app_context().push(); from src.models.database import db; db.create_all()"
```

## 🚀 Deployment

### Automatisch via GitHub Actions
Push naar `main` branch voor staging deployment
Push naar `production` branch voor productie deployment

### Handmatig
```bash
./scripts/deploy-to-gcp.sh
```

## 🔐 Configuratie

### Environment Variables
Kopieer `.env.example` bestanden en configureer:

**Backend (.env)**
- `DATABASE_URL` - Database connection string
- `GOOGLE_APPLICATION_CREDENTIALS` - Service account path
- `JWT_SECRET_KEY` - JWT signing key

**Frontend (.env)**
- `VITE_API_BASE_URL` - Backend API URL

### Google Cloud Secrets
Secrets worden automatisch aangemaakt via setup script:
- `database-password`
- `jwt-secret-key`
- `google-service-account`

## 📊 Monitoring

- Google Cloud Monitoring dashboards
- Automated alerting
- Audit logging
- Performance metrics

## 🤝 Contributing

1. Fork de repository
2. Maak een feature branch (`git checkout -b feature/nieuwe-functie`)
3. Commit uw wijzigingen (`git commit -am 'Voeg nieuwe functie toe'`)
4. Push naar de branch (`git push origin feature/nieuwe-functie`)
5. Maak een Pull Request

## 📄 Licentie

Dit project is ontwikkeld door Manus AI voor [Uw Organisatie].

## 🆘 Support

Voor vragen en ondersteuning, raadpleeg de documentatie in de `docs/` folder of neem contact op met uw systeembeheerder.

---

**Status: ✅ Productie-klaar**

Ready for deployment
