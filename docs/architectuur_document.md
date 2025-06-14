# Document Generatie App - Architectuur & Implementatie Plan

## Systeemoverzicht

De Document Generatie App is een moderne, schaalbare webapplicatie gebouwd op Google Cloud Platform met GitHub als centrale code repository. Het systeem automatiseert het proces van documentgeneratie (offertes, facturen, werkbonnen) door gebruikersinput om te zetten naar professionele PDF documenten via Google Docs sjablonen.

### Kerncomponenten

Het systeem bestaat uit vijf hoofdcomponenten die samen een complete documentgeneratie workflow vormen. De frontend is een React-gebaseerde single-page application die een intuïtieve gebruikersinterface biedt met een modulair dashboard systeem. Gebruikers kunnen via deze interface klantgegevens invoeren, producten selecteren, en documenten genereren. Het dashboard is volledig configureerbaar met widgets die aangepast kunnen worden per gebruikersrol.

De backend is een Flask-gebaseerde REST API die draait op Google Cloud Run. Deze service behandelt alle business logica, authenticatie, autorisatie, en communicatie met externe services. De API is ontworpen volgens RESTful principes en biedt endpoints voor klantbeheer, productbeheer, documentgeneratie, en gebruikersbeheer. De service is stateless en horizontaal schaalbaar.

Voor gegevensopslag wordt een hybride aanpak gebruikt met Google Cloud SQL als primaire database en Google Sheets als gebruiksvriendelijke interface voor databeheer. Cloud SQL biedt de betrouwbaarheid en prestaties die nodig zijn voor een productieomgeving, terwijl Google Sheets gebruikers in staat stelt om eenvoudig bulk-updates uit te voeren en data te beheren zonder technische kennis.

De documentgeneratie service integreert met Google Docs API om sjablonen te verwerken en PDF's te genereren. Deze service kan placeholders vervangen, loops verwerken voor dynamische content, en de resulterende documenten opslaan in Google Drive. De architectuur is voorbereid op toekomstige migratie naar HTML-naar-PDF generatie.

Het authenticatie- en autorisatiesysteem ondersteunt zowel Google-gebruikers als externe gebruikers via email-verificatie. Het systeem implementeert role-based access control (RBAC) met verschillende gebruikersrollen zoals monteur, verkoper, administrateur, en directeur. Elke rol heeft specifieke rechten en ziet aangepaste dashboard-widgets.

### Technologie Stack

De frontend wordt gebouwd met React 18, TypeScript, en Material-UI voor een moderne en responsive gebruikersinterface. State management gebeurt via Redux Toolkit, en API communicatie via Axios. De applicatie wordt gebouwd als een Progressive Web App (PWA) voor optimale gebruikerservaring op alle apparaten.

De backend gebruikt Flask 2.3 met SQLAlchemy ORM voor database interacties, Flask-JWT-Extended voor authenticatie, en Flask-CORS voor cross-origin requests. De applicatie wordt gecontaineriseerd met Docker en gedeployed op Google Cloud Run voor automatische schaling en hoge beschikbaarheid.

Voor de database wordt Google Cloud SQL met PostgreSQL gebruikt vanwege de robuustheid en SQL-compliance. Redis wordt ingezet voor caching en sessie-opslag. Google Cloud Storage wordt gebruikt voor bestandsopslag van gegenereerde documenten en uploads.

De integraties omvatten Google Workspace APIs (Docs, Sheets, Drive), Google Cloud APIs (SQL, Storage, IAM), en GitHub API voor repository management. Monitoring gebeurt via Google Cloud Monitoring en Logging.

### Deployment en CI/CD

Het project gebruikt GitHub als centrale code repository met een gestructureerde branching strategie. De main branch bevat productie-klare code, develop branch wordt gebruikt voor integratie, en feature branches voor nieuwe functionaliteit. Pull requests zijn verplicht voor alle wijzigingen naar main en develop branches.

GitHub Actions wordt gebruikt voor Continuous Integration en Continuous Deployment. Bij elke push naar develop wordt automatisch een test-suite uitgevoerd, en bij merge naar main wordt automatisch gedeployed naar productie. De CI/CD pipeline omvat code quality checks, security scanning, automated testing, en deployment naar Google Cloud Run.

Infrastructure as Code wordt geïmplementeerd via Terraform scripts die alle Google Cloud resources definiëren. Dit zorgt voor reproduceerbare deployments en eenvoudig beheer van verschillende omgevingen (development, staging, production).

### Beveiliging en Compliance

Het systeem implementeert security best practices op alle niveaus. API endpoints zijn beveiligd met JWT tokens, input validatie voorkomt injection attacks, en HTTPS wordt afgedwongen voor alle communicatie. Gebruikersdata wordt encrypted at rest en in transit.

Role-based access control zorgt ervoor dat gebruikers alleen toegang hebben tot data en functionaliteit die relevant is voor hun rol. Audit logging houdt bij wie wanneer welke acties heeft uitgevoerd. Regular security updates worden automatisch toegepast via de CI/CD pipeline.

GDPR compliance wordt gewaarborgd door data minimization, right to be forgotten implementatie, en expliciete consent management. Gebruikers hebben volledige controle over hun persoonlijke gegevens.

### Schaalbaarheid en Performance

De architectuur is ontworpen voor horizontale schaling. Google Cloud Run schaalt automatisch op basis van verkeer, en de database kan worden geschaald via read replicas en connection pooling. Redis caching vermindert database load en verbetert response times.

De frontend gebruikt code splitting en lazy loading voor optimale laadtijden. Service workers cachen statische assets en API responses voor offline functionaliteit. Progressive Web App features zorgen voor een native app-achtige ervaring.

Database queries zijn geoptimaliseerd met indexen en query analysis. Background jobs voor zware taken zoals PDF generatie worden uitgevoerd via Cloud Tasks om de gebruikersinterface responsief te houden.

## Database Schema Ontwerp

Het database schema is ontworpen om alle aspecten van het documentgeneratie proces te ondersteunen, van klantbeheer tot productcatalogus en documenthistorie. Het schema volgt normalisatie principes om data integriteit te waarborgen en redundantie te minimaliseren.

### Gebruikers en Organisaties

De users tabel bevat alle gebruikersgegevens inclusief authenticatie informatie, persoonlijke gegevens, en rol-informatie. Elke gebruiker behoort tot een organisatie, wat multi-tenancy mogelijk maakt. De organizations tabel bevat bedrijfsgegevens die gebruikt worden in documenten zoals logo, adresgegevens, en BTW-nummer.

User roles worden gedefinieerd in de user_roles tabel met granulaire permissions. Dit maakt het mogelijk om flexibel verschillende toegangsniveaus te definiëren zonder hardcoded rollen. De user_sessions tabel houdt actieve sessies bij voor beveiligingsdoeleinden.

### Klanten en Contacten

De customers tabel bevat alle klantgegevens inclusief factuur- en leveradressen. Klanten kunnen meerdere contactpersonen hebben die worden opgeslagen in de customer_contacts tabel. Dit maakt het mogelijk om verschillende contactpersonen te hebben voor verschillende doeleinden (inkoop, techniek, administratie).

Customer addresses worden apart opgeslagen om historische adressen te bewaren en meerdere adressen per klant mogelijk te maken. De customer_notes tabel bevat vrije tekst notities over klanten voor toekomstige referentie.

### Producten en Prijzen

De products tabel bevat de complete productcatalogus met omschrijvingen, eenheden, en metadata. Prijzen worden apart opgeslagen in de product_prices tabel om prijshistorie bij te houden en verschillende prijzen voor verschillende klantgroepen mogelijk te maken.

Product categories maken het mogelijk om producten te groeperen voor eenvoudiger beheer en rapportage. De product_attachments tabel slaat links op naar datasheets, foto's, en andere productgerelateerde documenten.

### Opdrachten en Documenten

De orders tabel bevat hoofdgegevens van opdrachten inclusief klant, status, en totaalbedragen. Order items worden opgeslagen in de order_items tabel met specifieke product informatie, aantallen, en prijzen op het moment van bestelling.

Generated documents worden geregistreerd in de documents tabel met links naar de gegenereerde PDF bestanden in Google Drive. Document templates definiëren de beschikbare sjablonen en hun configuratie.

### Configuratie en Instellingen

De system_settings tabel bevat globale systeeminstellingen zoals BTW-percentages, standaard betalingstermijnen, en API configuratie. User preferences slaat gebruikersspecifieke instellingen op zoals dashboard configuratie en notificatie voorkeuren.

Widget configurations definiëren de beschikbare dashboard widgets en hun standaard configuraties per gebruikersrol. Dit maakt het dashboard systeem volledig configureerbaar zonder code wijzigingen.

## Google Cloud Setup Scripts

Voor een geautomatiseerde en reproduceerbare setup van de Google Cloud omgeving worden verschillende scripts ontwikkeld die alle benodigde resources configureren. Deze scripts gebruiken de Google Cloud CLI en Terraform voor infrastructure as code.

### Project Initialisatie Script

Het project initialisatie script configureert een nieuw Google Cloud project met alle benodigde APIs, service accounts, en basis configuratie. Het script controleert eerst of de gebruiker is ingelogd en het juiste project heeft geselecteerd, en activeert vervolgens alle benodigde APIs zoals Cloud Run, Cloud SQL, Cloud Storage, en Google Workspace APIs.

Service accounts worden aangemaakt met minimale rechten volgens het principle of least privilege. Een deployment service account krijgt rechten voor Cloud Run deployment, een application service account voor runtime operaties, en een backup service account voor database backups.

IAM rollen worden geconfigureerd om secure toegang te waarborgen. Custom rollen worden gedefinieerd voor specifieke applicatie behoeften, en binding gebeurt op resource niveau om blast radius te minimaliseren.

### Database Setup Script

Het database setup script configureert Google Cloud SQL met PostgreSQL, inclusief high availability configuratie, automated backups, en security instellingen. Het script maakt een private IP configuratie aan voor secure communicatie tussen services.

Database gebruikers worden aangemaakt met specifieke rechten voor verschillende componenten. Een application user krijgt read/write rechten op applicatie tabellen, een readonly user voor rapportage, en een migration user voor schema wijzigingen.

Connection pooling wordt geconfigureerd via Cloud SQL Proxy om database connecties efficiënt te beheren. SSL certificaten worden gegenereerd voor encrypted connections.

### Storage en Networking Setup

Google Cloud Storage buckets worden geconfigureerd voor verschillende doeleinden: document storage voor gegenereerde PDF's, template storage voor Google Docs sjablonen, en backup storage voor database backups. Lifecycle policies worden ingesteld om kosten te optimaliseren.

VPC networking wordt geconfigureerd met private subnets voor database toegang en public subnets voor load balancers. Firewall rules worden ingesteld om alleen noodzakelijk verkeer toe te staan.

Cloud NAT wordt geconfigureerd voor uitgaande internet toegang vanuit private subnets, en Cloud Load Balancing voor high availability en SSL termination.

### Monitoring en Alerting Setup

Google Cloud Monitoring wordt geconfigureerd met custom dashboards voor applicatie metrics, database performance, en business metrics. Alerting policies worden ingesteld voor kritieke metrics zoals error rates, response times, en resource utilization.

Cloud Logging wordt geconfigureerd met log sinks voor long-term storage en analysis. Structured logging wordt ingesteld om eenvoudig zoeken en filteren mogelijk te maken.

Uptime checks monitoren de applicatie beschikbaarheid en sturen alerts bij downtime. SLA monitoring houdt bij of service level objectives worden gehaald.

## GitHub Repository Structuur

De GitHub repository wordt gestructureerd volgens moderne software development best practices met duidelijke scheiding tussen frontend, backend, infrastructure, en documentatie. Deze structuur maakt het eenvoudig voor ontwikkelaars om de codebase te begrijpen en bij te dragen.

### Repository Layout

De root directory bevat configuratiebestanden voor het gehele project zoals Docker Compose voor lokale ontwikkeling, GitHub Actions workflows, en project documentatie. Een README.md bestand geeft een overzicht van het project en setup instructies.

De backend directory bevat alle Flask applicatie code georganiseerd in modules voor verschillende functionaliteiten. Models, views, services, en utilities zijn duidelijk gescheiden. Database migraties worden beheerd via Alembic en opgeslagen in een migrations directory.

De frontend directory bevat de React applicatie met een moderne folder structuur. Components zijn georganiseerd per functionaliteit, en shared components worden hergebruikt. Styling gebeurt via CSS modules of styled-components voor component-scoped styling.

Infrastructure code wordt opgeslagen in een terraform directory met modules voor verschillende Google Cloud resources. Environment-specifieke configuraties worden gescheiden om verschillende deployment omgevingen te ondersteunen.

### Branching Strategie

Het project gebruikt GitFlow als branching strategie met enkele aanpassingen voor moderne CI/CD. De main branch bevat altijd productie-klare code en wordt beschermd met branch protection rules. Directe pushes zijn niet toegestaan, en alle wijzigingen moeten via pull requests.

De develop branch wordt gebruikt voor integratie van nieuwe features. Feature branches worden aangemaakt vanaf develop en gemerged terug via pull requests na code review. Hotfix branches kunnen direct vanaf main worden aangemaakt voor kritieke bugfixes.

Release branches worden gebruikt voor release voorbereiding en kunnen worden gebruikt voor release-specifieke bugfixes. Na release worden deze branches gemerged naar zowel main als develop.

### Code Quality en Standards

Pre-commit hooks worden geconfigureerd om code quality te waarborgen voordat code wordt gecommit. Deze hooks voeren linting, formatting, en basic tests uit. ESLint en Prettier worden gebruikt voor JavaScript/TypeScript code, en Black en Flake8 voor Python code.

Pull request templates zorgen voor consistente code reviews met checklists voor functionaliteit, tests, documentatie, en security. Code coverage requirements worden afgedwongen om test kwaliteit te waarborgen.

Conventional commits worden gebruikt voor consistente commit messages die automatische changelog generatie mogelijk maken. Semantic versioning wordt gebruikt voor releases.

### CI/CD Pipeline

GitHub Actions workflows automatiseren testing, building, en deployment. De CI pipeline wordt getriggerd bij elke push en pull request en voert unit tests, integration tests, linting, en security scans uit.

De CD pipeline wordt getriggerd bij merge naar main en deploy automatisch naar productie na succesvolle tests. Deployment naar staging gebeurt automatisch bij merge naar develop.

Secrets management gebeurt via GitHub Secrets voor gevoelige informatie zoals API keys en database credentials. Environment-specifieke secrets worden gescheiden om security te waarborgen.

## Authenticatie en Autorisatie Strategie

Het authenticatie en autorisatie systeem is ontworpen om zowel Google Workspace gebruikers als externe gebruikers te ondersteunen met een naadloze gebruikerservaring. Het systeem implementeert moderne security best practices en ondersteunt verschillende authenticatie methoden.

### Multi-Provider Authenticatie

Google OAuth 2.0 wordt gebruikt als primaire authenticatie methode voor gebruikers met Google accounts. Dit biedt een naadloze ervaring voor organisaties die al Google Workspace gebruiken. De OAuth flow wordt geïmplementeerd met PKCE voor enhanced security.

Voor externe gebruikers wordt email-gebaseerde authenticatie geïmplementeerd met magic links of verification codes. Gebruikers kunnen een account aanmaken met alleen een email adres en krijgen een verificatie link toegestuurd. Na verificatie kunnen zij een wachtwoord instellen voor toekomstige logins.

Multi-factor authenticatie wordt ondersteund via TOTP (Time-based One-Time Passwords) en kan worden verplicht gesteld per organisatie of gebruikersrol. SMS-gebaseerde 2FA wordt ook ondersteund als fallback optie.

### Role-Based Access Control

Het RBAC systeem definieert granulaire permissions die kunnen worden gecombineerd in rollen. Basis permissions omvatten read, write, delete, en admin rechten op verschillende resources zoals klanten, producten, documenten, en gebruikers.

Standaard rollen worden gedefinieerd voor verschillende gebruikerstypes. Een monteur rol heeft toegang tot werkbonnen en klantgegevens maar niet tot financiële informatie. Een verkoper kan offertes maken en klanten beheren. Een administrateur heeft toegang tot alle documenten en kan gebruikers beheren. Een directeur heeft volledige toegang inclusief rapportages en systeem configuratie.

Custom rollen kunnen worden aangemaakt door organisatie administrators om specifieke behoeften te ondersteunen. Rollen kunnen worden geërfd en gecombineerd om complexe autorisatie scenario's te ondersteunen.

### Session Management

JWT tokens worden gebruikt voor stateless authenticatie met korte expiry times voor security. Refresh tokens met langere expiry times worden gebruikt om nieuwe access tokens te verkrijgen zonder herhaalde login.

Session invalidation wordt ondersteund om gebruikers uit te loggen op alle apparaten. Dit is belangrijk voor security bij verlies of diefstal van apparaten. Concurrent session limits kunnen worden ingesteld om misbruik te voorkomen.

Device tracking houdt bij vanaf welke apparaten gebruikers inloggen en kan verdachte activiteit detecteren. Gebruikers krijgen notificaties bij login vanaf nieuwe apparaten.

### Security Features

Rate limiting voorkomt brute force attacks op login endpoints. Progressive delays worden geïmplementeerd bij herhaalde mislukte login pogingen. Account lockout wordt geactiveerd na een configureerbaar aantal mislukte pogingen.

Password policies worden afgedwongen voor gebruikers die wachtwoord authenticatie gebruiken. Minimale lengte, complexiteit, en password history worden gecontroleerd. Compromised password detection waarschuwt gebruikers bij gebruik van bekende gelekte wachtwoorden.

Audit logging houdt alle authenticatie events bij inclusief succesvolle en mislukte logins, password changes, en permission wijzigingen. Deze logs worden gebruikt voor security monitoring en compliance rapportage.

## API Endpoints Specificatie

De REST API is ontworpen volgens OpenAPI 3.0 specificaties en biedt een complete interface voor alle applicatie functionaliteiten. Alle endpoints volgen RESTful principes en gebruiken standaard HTTP status codes en methods.

### Authenticatie Endpoints

POST /api/auth/login accepteert email en password en retourneert JWT tokens bij succesvolle authenticatie. GET /api/auth/google/login initieert Google OAuth flow en redirect naar Google voor authenticatie. POST /api/auth/refresh accepteert een refresh token en retourneert nieuwe access en refresh tokens.

POST /api/auth/register maakt een nieuw gebruikersaccount aan met email verificatie. POST /api/auth/verify-email verifieert email adressen via verification tokens. POST /api/auth/forgot-password initieert password reset flow.

POST /api/auth/logout invalidateert de huidige sessie en refresh token. POST /api/auth/logout-all invalidateert alle sessies voor de gebruiker.

### Gebruikersbeheer Endpoints

GET /api/users retourneert een lijst van gebruikers met filtering en paginering. POST /api/users maakt een nieuwe gebruiker aan (admin only). GET /api/users/{id} retourneert specifieke gebruikersgegevens. PUT /api/users/{id} werkt gebruikersgegevens bij. DELETE /api/users/{id} verwijdert een gebruiker.

GET /api/users/me retourneert gegevens van de huidige gebruiker. PUT /api/users/me werkt gegevens van de huidige gebruiker bij. POST /api/users/me/change-password wijzigt het wachtwoord van de huidige gebruiker.

GET /api/roles retourneert beschikbare rollen. POST /api/roles maakt een nieuwe rol aan. PUT /api/users/{id}/roles wijzigt rollen van een gebruiker.

### Klantenbeheer Endpoints

GET /api/customers retourneert klanten lijst met zoek en filter opties. POST /api/customers maakt een nieuwe klant aan. GET /api/customers/{id} retourneert specifieke klantgegevens inclusief contacten en adressen. PUT /api/customers/{id} werkt klantgegevens bij. DELETE /api/customers/{id} verwijdert een klant.

POST /api/customers/{id}/contacts voegt een contact toe aan een klant. PUT /api/customers/{id}/contacts/{contact_id} werkt contactgegevens bij. DELETE /api/customers/{id}/contacts/{contact_id} verwijdert een contact.

POST /api/customers/{id}/addresses voegt een adres toe aan een klant. PUT /api/customers/{id}/addresses/{address_id} werkt adresgegevens bij. DELETE /api/customers/{id}/addresses/{address_id} verwijdert een adres.

### Productbeheer Endpoints

GET /api/products retourneert producten lijst met categorieën en prijzen. POST /api/products maakt een nieuw product aan. GET /api/products/{id} retourneert specifieke productgegevens. PUT /api/products/{id} werkt productgegevens bij. DELETE /api/products/{id} verwijdert een product.

GET /api/products/categories retourneert product categorieën. POST /api/products/categories maakt een nieuwe categorie aan. PUT /api/products/{id}/prices werkt productprijzen bij.

POST /api/products/{id}/attachments voegt bijlagen toe aan een product. DELETE /api/products/{id}/attachments/{attachment_id} verwijdert een bijlage.

### Documentgeneratie Endpoints

POST /api/documents/generate genereert een document op basis van sjabloon en data. GET /api/documents retourneert lijst van gegenereerde documenten. GET /api/documents/{id} retourneert specifiek document. DELETE /api/documents/{id} verwijdert een document.

GET /api/templates retourneert beschikbare document sjablonen. POST /api/templates uploadt een nieuw sjabloon. PUT /api/templates/{id} werkt sjabloon configuratie bij.

POST /api/documents/{id}/email verstuurt een document via email. GET /api/documents/{id}/download download een document als PDF.

Deze API specificatie vormt de basis voor zowel frontend ontwikkeling als externe integraties. Alle endpoints zijn gedocumenteerd met request/response schemas en error handling.

