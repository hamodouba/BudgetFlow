"""
BudgetFlow - Système de Gestion de Budget avec Règle des 3 Comptes
Backend Flask + JSON Database
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from datetime import datetime, timedelta
import json
import os
import uuid
import secrets
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.jinja_env.globals.update(max=max, min=min)

# ==================== CONFIGURATION ====================
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# Règle des 3 comptes
DEFAULT_RULES = {
    "besoins": 50,
    "envies": 30,
    "epargne": 20
}

# ==================== BASE DE DONNÉES JSON ====================
def load_json(filename):
    """Charge un JSON de manière sécurisée (tolère fichiers vides/corrompus)"""
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return []  # Fichier vide → retourne liste vide
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return []  # JSON invalide → retourne liste vide
    return []

def save_json(filename, data):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

def load_config():
    filepath = os.path.join(DATA_DIR, 'config.json')
    default_config = {
        "rules": {"besoins": 50, "envies": 30, "epargne": 20},
        "devise": "€",
        "nom_utilisateur": "Utilisateur"
    }
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    pass
    save_json('config.json', default_config)
    return default_config

def save_config(config):
    save_json('config.json', config)

# ==================== AUTHENTIFICATION ====================
def load_users():
    filepath = os.path.join(DATA_DIR, 'users.json')
    default_users = [{"username": "admin", "password": "admin123", "role": "admin"}]
    
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                try:
                    users = json.loads(content)
                    if isinstance(users, list) and len(users) > 0:
                        return users
                except json.JSONDecodeError:
                    pass  # Corrompu → on recrée
    save_json('users.json', default_users)
    return default_users

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ==================== CALCULS FINANCIERS ====================
def calculer_revenus_mensuels():
    """Calcule le total des revenus mensuels récurrents"""
    sources = load_json('revenus_sources.json')
    total = 0
    now = datetime.now()
    for source in sources:
        if source.get('actif', True):
            periode = source.get('periode', 'mensuel')
            montant = float(source.get('montant', 0))
            if periode == 'mensuel':
                total += montant
            elif periode == 'hebdomadaire':
                total += montant * 4.33
            elif periode == 'bimensuel':
                total += montant * 2
            elif periode == 'trimestriel':
                total += montant / 3
            elif periode == 'annuel':
                total += montant / 12
    return round(total, 2)

def calculer_revenus_occasionnels(mois=None, annee=None):
    """Calcule les revenus occasionnels du mois"""
    if mois is None:
        mois = datetime.now().month
    if annee is None:
        annee = datetime.now().year
    revenus = load_json('revenus_occasionnels.json')
    total = 0
    for r in revenus:
        d = datetime.fromisoformat(r['date'])
        if d.month == mois and d.year == annee:
            total += float(r.get('montant', 0))
    return round(total, 2)

def calculer_total_revenus(mois=None, annee=None):
    return round(calculer_revenus_mensuels() + calculer_revenus_occasionnels(mois, annee), 2)

def calculer_depenses_mensuelles(mois=None, annee=None):
    """Calcule les dépenses du mois"""
    if mois is None:
        mois = datetime.now().month
    if annee is None:
        annee = datetime.now().year
    depenses = load_json('depenses.json')
    total = 0
    for d in depenses:
        date_dep = datetime.fromisoformat(d['date'])
        if date_dep.month == mois and date_dep.year == annee:
            total += float(d.get('montant', 0))
    return round(total, 2)

def calculer_repartition_budget():
    """Répartition selon la règle des 3 comptes"""
    config = load_config()
    rules = config.get('rules', DEFAULT_RULES)
    total_revenus = calculer_revenus_mensuels()
    return {
        "besoins": round(total_revenus * rules['besoins'] / 100, 2),
        "envies": round(total_revenus * rules['envies'] / 100, 2),
        "epargne": round(total_revenus * rules['epargne'] / 100, 2),
        "regles": rules,
        "total": total_revenus
    }

def calculer_depenses_par_compte(mois=None, annee=None):
    """Dépenses réparties par compte"""
    if mois is None:
        mois = datetime.now().month
    if annee is None:
        annee = datetime.now().year
    depenses = load_json('depenses.json')
    repartition = {"besoins": 0, "envies": 0, "epargne": 0}
    for d in depenses:
        date_dep = datetime.fromisoformat(d['date'])
        if date_dep.month == mois and date_dep.year == annee:
            compte = d.get('compte', 'besoins')
            repartition[compte] = repartition.get(compte, 0) + float(d.get('montant', 0))
    return {k: round(v, 2) for k, v in repartition.items()}

def generer_conseils():
    """Génère des conseils personnalisés"""
    config = load_config()
    rules = config.get('rules', DEFAULT_RULES)
    repartition = calculer_repartition_budget()
    depenses_compte = calculer_depenses_par_compte()
    total_dep = calculer_depenses_mensuelles()
    total_rev = calculer_total_revenus()
    conseils = []

    # Analyse épargne
    taux_epargne = ((repartition['epargne'] - depenses_compte.get('epargne', 0)) / max(repartition['epargne'], 1)) * 100
    if taux_epargne < 50:
        conseils.append({
            "type": "warning",
            "icone": "⚠️",
            "titre": "Épargne insuffisante",
            "message": f"Votre épargne est utilisée à {100-taux_epargne:.0f}%. Essayez de réduire vos dépenses non essentielles pour atteindre votre objectif d'épargne."
        })
    else:
        conseils.append({
            "type": "success",
            "icone": "✅",
            "titre": "Bonne gestion d'épargne",
            "message": f"Vous avez économisé {taux_epargne:.0f}% de votre budget épargne ce mois-ci. Continuez ainsi !"
        })

    # Analyse besoins
    budget_besoins = repartition['besoins']
    dep_besoins = depenses_compte.get('besoins', 0)
    if dep_besoins > budget_besoins:
        conseils.append({
            "type": "danger",
            "icone": "🚨",
            "titre": "Dépassement budget besoins",
            "message": f"Vous avez dépassé votre budget besoins de {dep_besoins - budget_besoins:.2f}{config['devise']}. Vérifiez vos dépenses essentielles."
        })

    # Analyse envies
    budget_envies = repartition['envies']
    dep_envies = depenses_compte.get('envies', 0)
    if dep_envies > budget_envies * 0.8:
        conseils.append({
            "type": "info",
            "icone": "💡",
            "titre": "Budget envies presque atteint",
            "message": f"Vous avez utilisé {dep_envies/budget_envies*100:.0f}% de votre budget envies. Pensez à modérer vos dépenses plaisir."
        })

    # Conseil général
    reste = total_rev - total_dep
    if reste < 0:
        conseils.append({
            "type": "danger",
            "icone": "📉",
            "titre": "Budget déficitaire",
            "message": f"Votre solde est négatif de {abs(reste):.2f}{config['devise']}. Réduisez immédiatement vos dépenses."
        })
    elif reste < total_rev * 0.1:
        conseils.append({
            "type": "warning",
            "icone": "⚡",
            "titre": "Marge faible",
            "message": f"Il ne vous reste que {reste:.2f}{config['devise']}. Soyez prudent pour le reste du mois."
        })

    if not conseils:
        conseils.append({
            "type": "success",
            "icone": "🌟",
            "titre": "Excellent !",
            "message": "Votre budget est bien géré. Continuez à suivre vos dépenses régulièrement."
        })

    return conseils

def get_plus_grosse_depense(mois=None, annee=None):
    if mois is None:
        mois = datetime.now().month
    if annee is None:
        annee = datetime.now().year
    depenses = load_json('depenses.json')
    max_dep = {"montant": 0, "description": "Aucune", "categorie": "-", "date": "-"}
    for d in depenses:
        date_dep = datetime.fromisoformat(d['date'])
        if date_dep.month == mois and date_dep.year == annee:
            if float(d['montant']) > float(max_dep['montant']):
                max_dep = d
    return max_dep

def calculer_etat_budget():
    total_rev = calculer_total_revenus()
    total_dep = calculer_depenses_mensuelles()
    if total_rev == 0:
        return {"etat": "Inconnu", "icone": "❓", "couleur": "#6b7280", "message": "Aucun revenu déclaré"}
    ratio = (total_rev - total_dep) / total_rev
    if ratio >= 0.15:
        return {"etat": "Excellent", "icone": "🌟", "couleur": "#10b981", "message": f"+{ratio*100:.1f}% de marge. Budget très sain."}
    elif ratio >= 0.05:
        return {"etat": "Stable", "icone": "⚖️", "couleur": "#3b82f6", "message": f"+{ratio*100:.1f}% de marge. Budget équilibré."}
    elif ratio >= 0:
        return {"etat": "Attention", "icone": "⚠️", "couleur": "#f59e0b", "message": f"+{ratio*100:.1f}% de marge. Réduisez les dépenses superflues."}
    else:
        return {"etat": "Critique", "icone": "🚨", "couleur": "#ef4444", "message": f"{ratio*100:.1f}% de déficit. Action immédiate requise !"}

def get_depenses_par_jour(mois=None, annee=None):
    if mois is None:
        mois = datetime.now().month
    if annee is None:
        annee = datetime.now().year
    depenses = load_json('depenses.json')
    jours = {}
    for d in depenses:
        date_dep = datetime.fromisoformat(d['date'])
        if date_dep.month == mois and date_dep.year == annee:
            jour = date_dep.day
            jours[jour] = jours.get(jour, 0) + float(d['montant'])
    return jours

def get_depenses_par_categorie(mois=None, annee=None):
    if mois is None:
        mois = datetime.now().month
    if annee is None:
        annee = datetime.now().year
    depenses = load_json('depenses.json')
    categories = {}
    for d in depenses:
        date_dep = datetime.fromisoformat(d['date'])
        if date_dep.month == mois and date_dep.year == annee:
            cat = d.get('categorie', 'Autre')
            categories[cat] = categories.get(cat, 0) + float(d['montant'])
    return {k: round(v, 2) for k, v in sorted(categories.items(), key=lambda x: x[1], reverse=True)}

def get_historique_mensuel(nb_mois=6):
    """Historique des revenus et dépenses sur N mois"""
    now = datetime.now()
    historique = []
    for i in range(nb_mois - 1, -1, -1):
        date_ref = now.replace(day=1) - timedelta(days=i * 30)
        mois = date_ref.month
        annee = date_ref.year
        mois_nom = date_ref.strftime('%B %Y')
        revenus = calculer_total_revenus(mois, annee)
        depenses = calculer_depenses_mensuelles(mois, annee)
        historique.append({
            "mois": mois_nom,
            "revenus": revenus,
            "depenses": depenses,
            "solde": round(revenus - depenses, 2)
        })
    return historique

def calculer_solde_comptes_cumulatif():
    sources = load_json('revenus_sources.json')
    validations = load_json('validations_revenus.json')
    depenses = load_json('depenses.json')
    config = load_config()
    r = config.get('rules', DEFAULT_RULES)
    
    comptes = {k: {"recu":0, "depense":0, "solde":0, "pct":v} for k,v in r.items()}
    
    for v in validations:
        src = next((s for s in sources if s['id'] == v['source_id']), None)
        if src:
            m = v.get('montant_valide', float(src['montant']))
            for c in comptes: comptes[c]['recu'] += m * (r[c]/100)
            
    for d in depenses:
        c = d.get('compte', 'besoins')
        if c in comptes: comptes[c]['depense'] += float(d['montant'])
        
    for c in comptes: comptes[c]['solde'] = round(comptes[c]['recu'] - comptes[c]['depense'], 2)
    return comptes

# ==================== ROUTES AUTH ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = load_users()
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        user = next((u for u in users if u['username'] == username and u['password'] == password), None)
        if user:
            session['user'] = username
            session['role'] = user.get('role', 'user')
            return redirect(url_for('dashboard'))
        flash('Identifiants incorrects', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# ==================== ROUTES PRINCIPALES ====================
@app.route('/dashboard')
@login_required
def dashboard():
    config = load_config()
    repartition = calculer_repartition_budget()
    depenses_compte = calculer_depenses_par_compte()
    total_dep = calculer_depenses_mensuelles()
    total_rev = calculer_total_revenus()
    reste = round(total_rev - total_dep, 2)
    taux_epargne = round((repartition['epargne'] / max(total_rev, 1)) * 100, 1) if total_rev > 0 else 0
    plus_grosse = get_plus_grosse_depense()
    depenses_jour = get_depenses_par_jour()
    depenses_cat = get_depenses_par_categorie()
    historique = get_historique_mensuel()
    conseils = generer_conseils()

    return render_template('dashboard.html',
        config=config,
        repartition=repartition,
        depenses_compte=depenses_compte,
        total_dep=total_dep,
        total_rev=total_rev,
        reste=reste,
        taux_epargne=taux_epargne,
        plus_grosse=plus_grosse,
        depenses_jour=depenses_jour,
        depenses_cat=depenses_cat,
        historique=historique,
        conseils=conseils,
        etat_budget=calculer_etat_budget(),
        user=session.get('user')
    )

# ==================== CRUD REVENUS SOURCES ====================
@app.route('/revenus')
@login_required
def revenus():
    sources = load_json('revenus_sources.json')
    occasionnels = load_json('revenus_occasionnels.json')
    config = load_config()
    return render_template('revenus.html',
        sources=sources,
        occasionnels=occasionnels,
        total_mensuel=calculer_revenus_mensuels(),
        config=config,
        user=session.get('user')
    )

@app.route('/api/revenus_sources', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_revenus_sources():
    sources = load_json('revenus_sources.json')

    if request.method == 'GET':
        return jsonify(sources)

    if request.method == 'POST':
        data = request.json
        source = {
            "id": str(uuid.uuid4()),
            "nom": data.get('nom', ''),
            "montant": float(data.get('montant', 0)),
            "periode": data.get('periode', 'mensuel'),
            "type": data.get('type', 'recurrent'),
            "categorie": data.get('categorie', 'salaire'),
            "date_debut": data.get('date_debut', datetime.now().isoformat()),
            "date_creation": datetime.now().isoformat(),
            "actif": data.get('actif', True),
            "description": data.get('description', '')
        }
        sources.append(source)
        save_json('revenus_sources.json', sources)
        return jsonify({"success": True, "source": source})

    if request.method == 'PUT':
        data = request.json
        source_id = data.get('id')
        for i, s in enumerate(sources):
            if s['id'] == source_id:
                sources[i].update({
                    "nom": data.get('nom', s['nom']),
                    "montant": float(data.get('montant', s['montant'])),
                    "periode": data.get('periode', s['periode']),
                    "type": data.get('type', s['type']),
                    "categorie": data.get('categorie', s['categorie']),
                    "actif": data.get('actif', s['actif']),
                    "date_debut": data.get('date_debut', s.get('date_debut', datetime.now().isoformat())),
                    "description": data.get('description', s.get('description', ''))
                })
                save_json('revenus_sources.json', sources)
                return jsonify({"success": True})
        return jsonify({"success": False, "error": "Source non trouvée"}), 404

    if request.method == 'DELETE':
        data = request.json
        source_id = data.get('id')
        sources = [s for s in sources if s['id'] != source_id]
        save_json('revenus_sources.json', sources)
        return jsonify({"success": True})

# ==================== CRUD REVENUS OCCASIONNELS ====================
@app.route('/api/revenus_occasionnels', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_revenus_occasionnels():
    revenus = load_json('revenus_occasionnels.json')

    if request.method == 'GET':
        return jsonify(revenus)

    if request.method == 'POST':
        data = request.json
        revenu = {
            "id": str(uuid.uuid4()),
            "description": data.get('description', ''),
            "montant": float(data.get('montant', 0)),
            "date": data.get('date', datetime.now().isoformat()),
            "type": data.get('type', 'vente'),
            "categorie": data.get('categorie', 'autre')
        }
        revenus.append(revenu)
        save_json('revenus_occasionnels.json', revenus)
        return jsonify({"success": True, "revenu": revenu})

    if request.method == 'DELETE':
        data = request.json
        revenu_id = data.get('id')
        revenus = [r for r in revenus if r['id'] != revenu_id]
        save_json('revenus_occasionnels.json', revenus)
        return jsonify({"success": True})

# ==================== CRUD DÉPENSES ====================
@app.route('/depenses')
@login_required
def depenses():
    depenses_list = load_json('depenses.json')
    config = load_config()
    return render_template('depenses.html',
        depenses=sorted(depenses_list, key=lambda x: x['date'], reverse=True),
        config=config,
        user=session.get('user')
    )

@app.route('/api/depenses', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_depenses():
    depenses_list = load_json('depenses.json')

    if request.method == 'GET':
        return jsonify(depenses_list)

    if request.method == 'POST':
        data = request.json
        depense = {
            "id": str(uuid.uuid4()),
            "description": data.get('description', ''),
            "montant": float(data.get('montant', 0)),
            "categorie": data.get('categorie', 'autre'),
            "compte": data.get('compte', 'besoins'),
            "date": data.get('date', datetime.now().isoformat()),
            "recurrent": data.get('recurrent', False),
            "periode": data.get('periode', 'mensuel') if data.get('recurrent') else None,
            "note": data.get('note', '')
        }
        depenses_list.append(depense)
        save_json('depenses.json', depenses_list)
        return jsonify({"success": True, "depense": depense})

    if request.method == 'PUT':
        data = request.json
        depense_id = data.get('id')
        for i, d in enumerate(depenses_list):
            if d['id'] == depense_id:
                depenses_list[i].update({
                    "description": data.get('description', d['description']),
                    "montant": float(data.get('montant', d['montant'])),
                    "categorie": data.get('categorie', d['categorie']),
                    "compte": data.get('compte', d['compte']),
                    "date": data.get('date', d['date']),
                    "recurrent": data.get('recurrent', d['recurrent']),
                    "note": data.get('note', d.get('note', ''))
                })
                save_json('depenses.json', depenses_list)
                return jsonify({"success": True})
        return jsonify({"success": False, "error": "Dépense non trouvée"}), 404

    if request.method == 'DELETE':
        data = request.json
        depense_id = data.get('id')
        depenses_list = [d for d in depenses_list if d['id'] != depense_id]
        save_json('depenses.json', depenses_list)
        return jsonify({"success": True})

# ==================== COMPTES ====================
@app.route('/comptes')
@login_required
def comptes():
    repartition = calculer_repartition_budget()
    depenses_compte = calculer_depenses_par_compte()
    config = load_config()
    return render_template('comptes.html',
        soldes_cumul=calculer_solde_comptes_cumulatif(),
        config=config,
        user=session.get('user')
    )

# ==================== RAPPORTS ====================
@app.route('/rapports')
@login_required
def rapports():
    historique = get_historique_mensuel(12)
    depenses_cat = get_depenses_par_categorie()
    config = load_config()
    return render_template('rapports.html',
        historique=historique,
        depenses_cat=depenses_cat,
        config=config,
        user=session.get('user')
    )

# ==================== PARAMÈTRES ====================
@app.route('/parametres', methods=['GET', 'POST'])
@login_required
def parametres():
    config = load_config()
    if request.method == 'POST':
        config['rules'] = {
            "besoins": int(request.form.get('besoins', 50)),
            "envies": int(request.form.get('envies', 30)),
            "epargne": int(request.form.get('epargne', 20))
        }
        config['devise'] = request.form.get('devise', '€')
        config['nom_utilisateur'] = request.form.get('nom_utilisateur', 'Utilisateur')
        save_config(config)
        flash('Paramètres sauvegardés !', 'success')
    return render_template('parametres.html', config=config, user=session.get('user'))

# ==================== API DASHBOARD ====================
@app.route('/api/dashboard')
@login_required
def api_dashboard():
    return jsonify({
        "total_revenus": calculer_total_revenus(),
        "total_depenses": calculer_depenses_mensuelles(),
        "repartition": calculer_repartition_budget(),
        "depenses_par_compte": calculer_depenses_par_compte(),
        "depenses_par_categorie": get_depenses_par_categorie(),
        "depenses_par_jour": get_depenses_par_jour(),
        "historique": get_historique_mensuel(),
        "conseils": generer_conseils(),
        "plus_grosse_depense": get_plus_grosse_depense()
    })

# ==================== API EXPORT ====================
@app.route('/api/export')
@login_required
def api_export():
    """Export complet des données"""
    data = {
        "revenus_sources": load_json('revenus_sources.json'),
        "revenus_occasionnels": load_json('revenus_occasionnels.json'),
        "depenses": load_json('depenses.json'),
        "config": load_config(),
        "date_export": datetime.now().isoformat()
    }
    return jsonify(data)

# ==================== VALIDATION REVENUS PÉRIODIQUES ====================
@app.route('/api/validations_revenus', methods=['GET', 'POST'])
@login_required
def api_validations_revenus():
    validations = load_json('validations_revenus.json')
    sources = load_json('revenus_sources.json')
    
    if request.method == 'GET':
        return jsonify(validations)
        
    if request.method == 'POST':
        data = request.json
        sid = data['source_id']
        mois = int(data['mois'])
        annee = int(data['annee'])
        
        # 🔒 Vérification temporelle stricte
        now = datetime.now()
        target_first = datetime(annee, mois, 1)
        current_first = datetime(now.year, now.month, 1)
        
        # 1. Interdire les mois futurs
        if target_first > current_first:
            return jsonify({"success": False, "error": "⛔ Impossible de confirmer un revenu pour un mois futur."}), 400
            
        # 2. Mois courant : uniquement à partir du 25
        if target_first == current_first and now.day < 25:
            return jsonify({"success": False, "error": "⛔ Confirmation possible uniquement à partir du 25 du mois courant."}), 400
            
        # 3. Éviter les doublons
        existe = any(v['source_id'] == sid and v['mois'] == mois and v['annee'] == annee for v in validations)
        if not existe:
            montant = next((float(s['montant']) for s in sources if s['id'] == sid), 0)
            validations.append({
                "id": str(uuid.uuid4()), "source_id": sid, "mois": mois, "annee": annee,
                "montant_valide": montant, "statut": "recu", "date_validation": datetime.now().isoformat()
            })
            save_json('validations_revenus.json', validations)
        return jsonify({"success": True})

# ==================== GESTION DES DETTES ====================
@app.route('/api/dettes', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_dettes():
    dettes = load_json('dettes.json')
    if request.method == 'GET':
        return jsonify(dettes)
    if request.method == 'POST':
        data = request.json
        dette = {
            "id": str(uuid.uuid4()), "nom": data['nom'],
            "montant_initial": float(data['montant_initial']),
            "montant_restant": float(data['montant_initial']),
            "mensualite": float(data.get('mensualite', 0)),
            "prochaine_echeance": data.get('prochaine_echeance', datetime.now().isoformat()),
            "actif": True, "date_creation": datetime.now().isoformat()
        }
        dettes.append(dette)
        save_json('dettes.json', dettes)
        return jsonify({"success": True, "dette": dette})
    if request.method == 'PUT':
        data = request.json
        for i, d in enumerate(dettes):
            if d['id'] == data['id']:
                if data.get('action') == 'paiement':
                    montant = float(data.get('montant', d['mensualite']))
                    dettes[i]['montant_restant'] = max(0, d['montant_restant'] - montant)
                    # Auto-ajout aux dépenses
                    depenses = load_json('depenses.json')
                    depenses.append({
                        "id": str(uuid.uuid4()), "description": f"Échéance: {d['nom']}",
                        "montant": montant, "categorie": "dettes", "compte": "besoins",
                        "date": datetime.now().isoformat(), "recurrent": False, "note": f"Paiement dette"
                    })
                    save_json('depenses.json', depenses)
                    dettes[i]['prochaine_echeance'] = (datetime.fromisoformat(d['prochaine_echeance']) + timedelta(days=30)).isoformat()
                else:
                    dettes[i].update(data)
                save_json('dettes.json', dettes)
                return jsonify({"success": True})
    if request.method == 'DELETE':
        data = request.json
        dettes = [d for d in dettes if d['id'] != data['id']]
        save_json('dettes.json', dettes)
        return jsonify({"success": True})

@app.route('/api/creances_dettes', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_creances_dettes():
    items = load_json('creances_dettes.json')
    if request.method == 'GET':
        return jsonify(items)
    if request.method == 'POST':
        d = request.json
        montant = float(d.get('montant', 0))
        interet = float(d.get('interet', 0))
        items.append({
            "id": str(uuid.uuid4()), "type": d.get('type', 'dette'),
            "partenaire": d.get('partenaire', ''), "montant_initial": montant,
            "interet": interet, "montant_total": montant + interet,
            "montant_restant": montant + interet, "statut": "en_cours",
            "date_creation": datetime.now().isoformat()
        })
        save_json('creances_dettes.json', items)
        return jsonify({"success": True})
    if request.method == 'PUT':
        d = request.json
        idx = next((i for i, x in enumerate(items) if x['id'] == d['id']), None)
        if idx is not None:
            if d.get('action') == 'paiement':
                montant = float(d.get('montant', items[idx]['montant_restant']))
                items[idx]['montant_restant'] = max(0, items[idx]['montant_restant'] - montant)
                if items[idx]['montant_restant'] <= 0:
                    items[idx]['statut'] = 'paye'
                    # Auto-compta
                    if items[idx]['type'] == 'dette':
                        dep = load_json('depenses.json')
                        dep.append({"id": str(uuid.uuid4()), "description": f"Remboursement: {items[idx]['partenaire']}", "montant": items[idx]['montant_initial'], "categorie": "dettes", "compte": "besoins", "date": datetime.now().isoformat()})
                        save_json('depenses.json', dep)
                    else:
                        rev = load_json('revenus_occasionnels.json')
                        rev.append({"id": str(uuid.uuid4()), "description": f"Reçu de: {items[idx]['partenaire']}", "montant": items[idx]['montant_initial'], "date": datetime.now().isoformat(), "type": "remboursement"})
                        save_json('revenus_occasionnels.json', rev)
            save_json('creances_dettes.json', items)
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Non trouvé"}), 404
    if request.method == 'DELETE':
        items = [x for x in items if x['id'] != request.json.get('id')]
        save_json('creances_dettes.json', items)
        return jsonify({"success": True})

if __name__ == '__main__':
    # Initialisation des fichiers JSON (SAUF users.json)
    for f in ['revenus_sources.json', 'revenus_occasionnels.json', 'depenses.json']:
        if not os.path.exists(os.path.join(DATA_DIR, f)):
            save_json(f, [])

    # S'assurer que users.json contient l'admin par défaut
    load_users()  # Force la création si nécessaire

    print("=" * 60)
    print("💰 BudgetFlow - Système de Gestion de Budget")
    print("=" * 60)
    print("🌐 URL: http://127.0.0.1:5000")
    print("👤 Login: admin / admin123")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)