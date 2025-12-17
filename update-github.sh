#!/bin/bash
# Script pour remplacer l'ancienne version sur GitHub
# Repository: https://github.com/SonOfOgre666/InternetOfEmotions

set -e  # Arrêter en cas d'erreur

echo "🚀 Mise à jour du repository GitHub avec la nouvelle version..."

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Vérifier qu'on est dans le bon répertoire
if [ ! -f "README.md" ]; then
    echo -e "${RED}❌ Erreur: README.md non trouvé${NC}"
    exit 1
fi

# Vérifier les fichiers sensibles
if [ -f ".env" ]; then
    echo -e "${RED}⚠️  ATTENTION: Fichier .env détecté !${NC}"
    echo -e "${YELLOW}Assurez-vous qu'il est dans .gitignore (déjà configuré)${NC}"
fi

# Initialiser Git
echo "📦 Initialisation Git..."
git init
echo -e "${GREEN}✅ Git initialisé${NC}"

# Ajouter tous les fichiers
echo "📁 Ajout des fichiers..."
git add .
echo -e "${GREEN}✅ Fichiers ajoutés${NC}"

# Créer le commit
echo "💾 Création du commit..."
git commit -m "feat: Major update - Complete refactor with microservices architecture

🎯 New Features:
- 6 microservices architecture (Data Fetcher, Content Extractor, Event Extractor, ML Analyzer, Aggregator, API Gateway)
- Machine Learning with RoBERTa transformer (90% emotion detection accuracy)
- Next.js 15 frontend with TypeScript and Tailwind CSS
- Real-time processing with 30-second pipeline cycles
- Support for 195+ countries
- Automatic translation for any language
- Circuit breaker pattern for resilience
- Complete French presentation materials

🛠️ Technical Stack:
- Backend: Python 3.9+, Flask, SQLite + WAL
- ML: PyTorch, Transformers (RoBERTa), DBSCAN clustering
- Frontend: Next.js 15, TypeScript, Leaflet maps
- DevOps: Sentry monitoring, Shell scripts

📚 Documentation:
- Complete architecture documentation (ARCHITECTURE.md)
- Software engineering presentation (Présentation_d'Ingénierie_Logicielle.md)
- Detailed README with setup instructions
- Test suite with pytest"

echo -e "${GREEN}✅ Commit créé${NC}"

# Renommer la branche en main
git branch -M main
echo -e "${GREEN}✅ Branche configurée: main${NC}"

# Ajouter le remote
echo "🔗 Configuration du remote GitHub..."
git remote add origin https://github.com/SonOfOgre666/InternetOfEmotions.git
echo -e "${GREEN}✅ Remote ajouté: https://github.com/SonOfOgre666/InternetOfEmotions${NC}"

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}⚠️  IMPORTANT: Vous allez remplacer l'ancienne version${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Votre repository GitHub: https://github.com/SonOfOgre666/InternetOfEmotions"
echo ""
echo -e "${RED}⚠️  Cela va ÉCRASER l'ancienne version sur GitHub${NC}"
echo ""
read -p "Êtes-vous sûr de vouloir continuer ? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Opération annulée."
    exit 0
fi

echo ""
echo "🚀 Push vers GitHub (force push pour remplacer l'ancienne version)..."
echo ""

# Force push pour remplacer complètement l'ancienne version
git push -f origin main

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ SUCCÈS ! Votre nouvelle version est sur GitHub${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "🔗 Votre repository: https://github.com/SonOfOgre666/InternetOfEmotions"
echo ""
echo "📋 Prochaines étapes:"
echo "  1. Visitez votre repo sur GitHub"
echo "  2. Vérifiez que README.md s'affiche correctement"
echo "  3. Ajoutez des topics (microservices, machine-learning, emotion-analysis, etc.)"
echo "  4. Créez une LICENSE si nécessaire"
echo ""
echo "🎉 Votre projet est maintenant public et prêt à être partagé !"
