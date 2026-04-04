# 💰 BudgetFlow

**Système intelligent de gestion de budget personnel basé sur la règle des 3 comptes (50/30/20)**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Aperçu](#-aperçu)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [Structure du projet](#-structure-du-projet)
- [Règle des 3 comptes](#-règle-des-3-comptes)
- [Sécurité](#-sécurité)
- [Technologies](#-technologies)
- [Contribuer](#-contribuer)
- [License](#-license)

---

## ✨ Fonctionnalités

### 📊 Tableau de bord financier
- **KPI en temps réel** : Revenus, dépenses, solde, taux d'épargne
- **État du budget** : Analyse automatique (Excellent/Stable/Attention/Critique)
- **Graphiques interactifs** : Distribution du budget, dépenses par jour/catégorie, historique
- **Conseils personnalisés** : Analyse intelligente de vos habitudes de dépenses

### 💵 Gestion des revenus
- **Sources récurrentes** : Salaire, freelance, location, pensions (périodicité configurable)
- **Revenus occasionnels** : Ventes, primes, cadeaux
- **Calendrier annuel** : Validation des revenus (débloqué à partir du 25 du mois)
- **Historique complet** : Suivi des validations de 2025 à 2030

### 💳 Gestion des dépenses
- **Catégorisation automatique** : Alimentation, logement, transport, santé, loisirs...
- **Dépenses récurrentes** : Abonnements, factures fixes
- **Recherche et filtrage** : Par date, catégorie, montant

### 🏦 Règle des 3 comptes
- **Besoins (50%)** : Dépenses essentielles (loyer, nourriture, factures)
- **Envies (30%)** : Plaisirs et loisirs (sorties, shopping, voyages)
- **Épargne (20%)** : Épargne de précaution, investissements, projets
- **Suivi cumulatif** : Solde réel par compte sur toute la durée

### 💸 Dettes & Créances
- **Gestion bidirectionnelle** : Dettes (je dois) et créances (on me doit)
- **Calcul des intérêts** : Support des prêts avec intérêts
- **Paiements partiels** : Suivi du restant dû
- **Statut automatique** : Marqué comme "Payé" une fois soldé

### 🔒 Sécurité & Authentification
- **Login sécurisé** : Session Flask avec secret key
- **Protection des routes** : Toutes les pages protégées
- **Validation serveur** : Double vérification (client + serveur) pour les validations de revenus

### 📱 Responsive Design
- **Interface moderne** : Dark theme avec Chart.js
- **100% responsive** : Mobile, tablette, desktop
- **Animations fluides** : Transitions et micro-interactions

---

## 📸 Aperçu

> *Ajoute des captures d'écran ici :*
> - `screenshots/dashboard.png` - Tableau de bord
> - `screenshots/calendrier.png` - Calendrier des revenus
> - `screenshots/comptes.png` - Vue des 3 comptes
> - `screenshots/dettes.png` - Gestion des dettes

---

## 🚀 Installation

### Prérequis
- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### Étapes d'installation

1. **Cloner le dépôt**
```bash
git clone https://github.com/votre-utilisateur/BudgetFlow.git
cd BudgetFlow
