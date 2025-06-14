#!/bin/bash

# Document Generator - GitHub Setup Script
# Dit script initialiseert een Git repository en pusht alles naar GitHub

set -e

echo "🚀 Document Generator - GitHub Setup"
echo "===================================="

# Controleer of we in de juiste directory zijn
if [ ! -f "README.md" ] || [ ! -d "document-generator-backend" ]; then
    echo "❌ Fout: Voer dit script uit vanuit de document-generator-repo directory"
    exit 1
fi

# Vraag gebruiker om GitHub repository URL
echo ""
echo "📝 GitHub Repository Setup"
echo ""
read -p "Voer uw GitHub repository URL in (bijv. https://github.com/username/document-generator.git): " REPO_URL

if [ -z "$REPO_URL" ]; then
    echo "❌ Fout: Repository URL is vereist"
    exit 1
fi

# Vraag om commit message
echo ""
read -p "Voer een commit message in (of druk Enter voor default): " COMMIT_MSG

if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="Initial commit: Complete Document Generator application"
fi

echo ""
echo "🔧 Git Repository Initialisatie..."

# Initialiseer Git repository
if [ ! -d ".git" ]; then
    git init
    echo "✅ Git repository geïnitialiseerd"
else
    echo "ℹ️  Git repository bestaat al"
fi

# Configureer Git (optioneel)
echo ""
read -p "Voer uw Git gebruikersnaam in (of druk Enter om over te slaan): " GIT_USERNAME
if [ ! -z "$GIT_USERNAME" ]; then
    git config user.name "$GIT_USERNAME"
    echo "✅ Git gebruikersnaam ingesteld: $GIT_USERNAME"
fi

read -p "Voer uw Git email in (of druk Enter om over te slaan): " GIT_EMAIL
if [ ! -z "$GIT_EMAIL" ]; then
    git config user.email "$GIT_EMAIL"
    echo "✅ Git email ingesteld: $GIT_EMAIL"
fi

# Voeg remote origin toe
echo ""
echo "🔗 Remote repository configuratie..."
if git remote get-url origin >/dev/null 2>&1; then
    echo "ℹ️  Remote origin bestaat al, wordt bijgewerkt..."
    git remote set-url origin "$REPO_URL"
else
    git remote add origin "$REPO_URL"
fi
echo "✅ Remote origin ingesteld: $REPO_URL"

# Voeg alle bestanden toe
echo ""
echo "📁 Bestanden toevoegen aan Git..."
git add .
echo "✅ Alle bestanden toegevoegd"

# Maak initial commit
echo ""
echo "💾 Initial commit maken..."
git commit -m "$COMMIT_MSG"
echo "✅ Commit gemaakt: $COMMIT_MSG"

# Push naar GitHub
echo ""
echo "🚀 Pushen naar GitHub..."
echo "ℹ️  Als dit de eerste keer is, moet u mogelijk uw GitHub credentials invoeren"

# Probeer te pushen naar main branch
if git push -u origin main; then
    echo "✅ Succesvol gepusht naar main branch"
elif git push -u origin master; then
    echo "✅ Succesvol gepusht naar master branch"
else
    echo "❌ Fout bij pushen. Controleer uw GitHub credentials en repository URL"
    echo "💡 Tip: Zorg ervoor dat de repository bestaat op GitHub en u toegang heeft"
    exit 1
fi

echo ""
echo "🎉 SUCCESS! Repository is succesvol naar GitHub gepusht!"
echo ""
echo "📋 Volgende stappen:"
echo "1. Ga naar uw GitHub repository: $REPO_URL"
echo "2. Configureer GitHub Secrets voor CI/CD (zie docs/implementatie-handleiding.md)"
echo "3. Voer Google Cloud setup uit: ./scripts/setup-gcp.sh"
echo "4. Deploy naar productie: ./scripts/deploy-to-gcp.sh"
echo ""
echo "📚 Documentatie:"
echo "- README.md - Snelle start gids"
echo "- docs/implementatie-handleiding.md - Complete implementatie instructies"
echo "- docs/project-oplevering.md - Project overzicht"
echo ""
echo "✅ GitHub setup voltooid!"

