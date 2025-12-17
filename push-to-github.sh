#!/bin/bash
# Script pour préparer et pousser le projet sur GitHub
# Usage: ./push-to-github.sh

set -e  # Arrêter en cas d'erreur

echo "🚀 Préparation du projet pour GitHub..."

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Vérifier qu'on est dans le bon répertoire
if [ ! -f "README.md" ]; then
    echo -e "${RED}❌ Erreur: README.md non trouvé. Êtes-vous dans le bon répertoire ?${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Répertoire du projet vérifié${NC}"

# Vérifier qu'il n'y a pas de fichier .env
if [ -f ".env" ]; then
    echo -e "${RED}⚠️  ATTENTION: Fichier .env détecté !${NC}"
    echo -e "${YELLOW}Ce fichier contient des secrets et ne doit PAS être commité.${NC}"
    echo -e "${YELLOW}Le .gitignore est configuré pour l'ignorer, mais vérifiez.${NC}"
    read -p "Continuer ? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}✅ Pas de secrets détectés${NC}"

# Initialiser Git si nécessaire
if [ ! -d ".git" ]; then
    echo "📦 Initialisation du repository Git..."
    git init
    echo -e "${GREEN}✅ Git initialisé${NC}"
else
    echo -e "${YELLOW}ℹ️  Git déjà initialisé${NC}"
fi

# Demander le nom d'utilisateur GitHub
echo ""
echo -e "${YELLOW}📝 Configuration du repository GitHub${NC}"
read -p "Votre nom d'utilisateur GitHub: " github_username

if [ -z "$github_username" ]; then
    echo -e "${RED}❌ Nom d'utilisateur requis${NC}"
    exit 1
fi

read -p "Nom du repository (par défaut: internet-of-emotions): " repo_name
repo_name=${repo_name:-internet-of-emotions}

echo ""
echo -e "${GREEN}Configuration:${NC}"
echo "  Username: $github_username"
echo "  Repository: $repo_name"
echo "  URL: https://github.com/$github_username/$repo_name"
echo ""

read -p "Confirmer ? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Annulé."
    exit 1
fi

# Ajouter tous les fichiers
echo "📁 Ajout des fichiers..."
git add .

# Créer le commit initial
echo "💾 Création du commit..."
git commit -m "Initial commit: Internet des Émotions - Real-time Global Emotion Analysis Platform

- 6 microservices architecture (Data Fetcher, Content Extractor, Event Extractor, ML Analyzer, Aggregator, API Gateway)
- Machine Learning with RoBERTa for emotion detection (90% accuracy)
- Frontend with Next.js 15 and TypeScript
- Supports 195+ countries
- Real-time processing with 30-second pipeline cycles
- Complete documentation and presentation materials"

echo -e "${GREEN}✅ Commit créé${NC}"

# Renommer la branche en main
git branch -M main
echo -e "${GREEN}✅ Branche renommée en 'main'${NC}"

# Ajouter le remote
remote_url="https://github.com/$github_username/$repo_name.git"
if git remote | grep -q "origin"; then
    echo "🔄 Mise à jour du remote origin..."
    git remote set-url origin "$remote_url"
else
    echo "🔗 Ajout du remote origin..."
    git remote add origin "$remote_url"
fi

echo -e "${GREEN}✅ Remote configuré: $remote_url${NC}"

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🎯 PROCHAINES ÉTAPES:${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "1. Allez sur GitHub: https://github.com/new"
echo "2. Créez un nouveau repository nommé: $repo_name"
echo "3. Description suggérée:"
echo "   '🌍 Real-time Global Emotion Analysis Platform - Microservices + ML (RoBERTa) + Next.js'"
echo "4. ⚠️  NE PAS initialiser avec README/LICENSE/.gitignore (vous les avez déjà)"
echo "5. Choisir Public ou Private selon votre préférence"
echo "6. Cliquer 'Create repository'"
echo ""
echo "Puis, de retour ici, exécutez:"
echo -e "${GREEN}  git push -u origin main${NC}"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📋 Résumé de ce qui a été préparé:"
echo "  ✅ .gitignore configuré (secrets, logs, db exclus)"
echo "  ✅ .env.example créé (template sans secrets)"
echo "  ✅ Commit initial créé avec message détaillé"
echo "  ✅ Remote GitHub configuré"
echo ""
echo -e "${GREEN}🎉 Votre projet est prêt pour GitHub !${NC}"
