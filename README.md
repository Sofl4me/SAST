# 🔐 Démo Flask XSS & Analyse SonarQube

## 📌 Contexte
Ce projet met en place un pipeline qui déploie une **application Flask volontairement vulnérable**, puis l’analyse avec **SonarQube**.  
Objectif : illustrer la détection automatique d’une faille de type **Cross-Site Scripting (XSS)**.

---

## 🚨 Résultat SonarQube

### Ce que Sonar a détecté
- **Règle** : *“Change this code to not construct HTML content directly from user-controlled data”*  
  (`pythonsecurity:S5496`)
- **Gravité** : **Security / Blocker**  
- **Vulnérabilité** : **XSS (Cross-Site Scripting)**
- **Pourquoi** : le code génère du HTML en concaténant une valeur **contrôlée par l’utilisateur** (`name`), et l’envoie directement au navigateur.

---

## 🔎 Traçage source → sink

Sonar montre le flux en 5 étapes :

1. **SOURCE** : l’utilisateur peut injecter du contenu via HTTP (`request.args.get('name', 'visiteur')`).
2. La valeur est stockée dans la variable `name`.
3. La valeur est insérée dans une f-string Python.
4. La f-string devient du HTML grâce à `render_template_string`.
5. **SINK** : le navigateur reçoit du HTML non échappé.  
   → Si `name` contient `<script>...</script>`, le JavaScript est exécuté.

👉 En clair : *Ne construisez pas du HTML avec des données brutes de l’utilisateur !*

---

## ⚠️ Exemple de code vulnérable

```python
name = request.args.get('name', 'visiteur')
return render_template_string(f"<h1>Bonjour {name}</h1>")
name provient directement de la requête (non validé, non échappé).
```

f"...{name}..." injecte la valeur brute dans le HTML.

## ✅ Solutions de correction

1) Utiliser un template Jinja (recommandé)
Jinja2 applique l’auto-escape par défaut.

```python
from flask import Flask, render_template, request

@app.route("/")
def index():
    name = request.args.get("name", "visiteur")
    return render_template("index.html", name=name)
```
templates/index.html

```python
<h1>Bonjour {{ name }}</h1>  <!-- auto-échappé -->
```

2) Avec render_template_string (échappement explicite)
```python
from flask import Flask, request, render_template_string

@app.route("/")
def index():
    name = request.args.get("name", "visiteur")
    return render_template_string("<h1>Bonjour {{ name|e }}</h1>", name=name)
```
3) Échapper côté Python (moins idiomatique Flask)
```python
from markupsafe import escape

@app.route("/")
def index():
    name = escape(request.args.get("name", "visiteur"))
    return f"<h1>Bonjour {name}</h1>"
```

## 💡 Bonnes pratiques
- Ne jamais désactiver l’auto-escape Jinja.
- Toujours valider et normaliser les entrées (longueur, charset, liste blanche).
- Séparer logique et présentation (éviter f-strings HTML avec inputs).
- Intégrer SonarQube dans le pipeline CI/CD pour détecter automatiquement ces vulnérabilités.

# 🔐 Démo Flask & Analyse OWASP ZAP

## 📌 Contexte
Ce projet met en place un pipeline qui déploie une **application Flask volontairement vulnérable**, puis l’analyse automatiquement avec **OWASP ZAP**.  
Objectif : illustrer la détection de failles de configuration et de sécurité HTTP côté **runtime** (application en exécution).

---

## 📊 Résultat ZAP

### Résumé des résultats
- **High (élevé)** : 0  
- **Medium (moyen)** : 2  
- **Low (faible)** : 3  
- **Informational (info)** : 1  
- **False Positive** : 0  

👉 Aucune vulnérabilité critique n’a été détectée, mais plusieurs **faiblesses de configuration HTTP** doivent être corrigées.

---

## 🔎 Détail des vulnérabilités

### 🔶 Vulnérabilités Medium

1. **Content Security Policy (CSP) Header Not Set**  
   - **Description** : l’application ne définit pas de politique CSP. Cela laisse la porte ouverte aux attaques **XSS** et injections de contenu.  
   - **Occurrences** : 4 (`/`, page d’accueil, `robots.txt`, `sitemap.xml`).  
   - **Solution** : ajouter un en-tête HTTP :  
     ```
     Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'
     ```  
   - **Référence** : [MDN - CSP](https://developer.mozilla.org/fr/docs/Web/HTTP/CSP).

2. **Missing Anti-clickjacking Header**  
   - **Description** : absence de `X-Frame-Options` ou `Content-Security-Policy: frame-ancestors`. Cela expose l’app au **clickjacking**.  
   - **Occurrences** : 2 (`/` et page d’accueil).  
   - **Solution** :  
     ```
     X-Frame-Options: DENY
     ```  
     ou bien  
     ```
     Content-Security-Policy: frame-ancestors 'none'
     ```

---

### 🟡 Vulnérabilités Low

1. **Insufficient Site Isolation Against Spectre**  
   - **Description** : absence des en-têtes `Cross-Origin-Resource-Policy`, `Cross-Origin-Embedder-Policy`, `Cross-Origin-Opener-Policy`.  
   - **Impact** : faiblesse face aux attaques **Spectre** (side-channel).  
   - **Occurrences** : 6.  
   - **Solution** :  
     ```
     Cross-Origin-Resource-Policy: same-origin
     Cross-Origin-Opener-Policy: same-origin
     Cross-Origin-Embedder-Policy: require-corp
     ```

2. **Permissions Policy Header Not Set**  
   - **Description** : l’en-tête `Permissions-Policy` est manquant. Cela permet potentiellement à des scripts d’accéder à des API sensibles (micro, caméra, géolocalisation).  
   - **Occurrences** : 4.  
   - **Solution** :  
     ```
     Permissions-Policy: geolocation=(), camera=(), microphone=()
     ```

3. **X-Content-Type-Options Header Missing**  
   - **Description** : absence de `X-Content-Type-Options: nosniff`.  
   - **Impact** : permet à un navigateur d’interpréter un fichier avec le mauvais type MIME.  
   - **Occurrences** : 2.  
   - **Solution** :  
     ```
     X-Content-Type-Options: nosniff
     ```

---

### 🔵 Observation Informational

- **Storable and Cacheable Content**  
  - **Description** : certains contenus statiques (ex. `robots.txt`) sont mis en cache.  
  - **Impact** : faible, mais une politique de cache maîtrisée est recommandée.  
  - **Solution** : ajuster les en-têtes :  
    ```
    Cache-Control: no-store
    Pragma: no-cache
    ```

---

## 📑 Exemple de rapport
Un rapport HTML détaillé est disponible :  
![Analyse ZAP Report](./artifacts/zap_report.html)

---

## 🔎 Détail des alertes

### 🔶 Risque Moyen
1. **Content Security Policy (CSP) Header Not Set**  
   - **Problème** : aucun en-tête CSP n’est défini.  
   - **Impact** : l’application est exposée aux attaques XSS et injections de contenu.  
   - **Correction** :
     ```python
     @app.after_request
     def set_csp(response):
         response.headers["Content-Security-Policy"] = "default-src 'self'"
         return response
     ```

2. **Missing Anti-clickjacking Header**  
   - **Problème** : pas d’en-tête `X-Frame-Options`.  
   - **Impact** : l’application peut être intégrée dans un iframe malveillant (*clickjacking*).  
   - **Correction** :
     ```python
     @app.after_request
     def set_xframe(response):
         response.headers["X-Frame-Options"] = "DENY"
         return response
     ```

---

### 🟡 Risque Faible
1. **Insufficient Site Isolation Against Spectre Vulnerability**  
   - **Problème** : certains en-têtes de protection contre les attaques CPU (Spectre) manquent.  
   - **Correction** :
     ```
     Cross-Origin-Opener-Policy: same-origin
     Cross-Origin-Resource-Policy: same-origin
     ```

2. **Permissions Policy Header Not Set**  
   - **Problème** : pas de politique fine sur les API navigateur (caméra, micro, etc.).  
   - **Correction** :
     ```
     Permissions-Policy: geolocation=(), microphone=()
     ```

3. **X-Content-Type-Options Header Missing**  
   - **Problème** : l’en-tête `X-Content-Type-Options: nosniff` est absent.  
   - **Impact** : certains navigateurs peuvent interpréter des contenus avec le mauvais type MIME.  
   - **Correction** :
     ```python
     response.headers["X-Content-Type-Options"] = "nosniff"
     ```

---

## 💡 Bonnes pratiques

- Toujours configurer des **en-têtes HTTP de sécurité** (CSP, X-Frame-Options, X-Content-Type-Options, etc.).  
- Empêcher le *clickjacking* et limiter les API navigateur accessibles.  
- Définir des politiques claires de cache pour éviter la fuite de données sensibles.  
- Garder **ZAP** dans le pipeline CI/CD : il détecte les failles runtime que SonarQube (analyse statique) ne voit pas.

---

# 🔐 Démo Flask & Analyse pip-audit

## 📌 Contexte
Ce projet met en place un pipeline qui déploie une **application Flask volontairement vulnérable**, puis lance une analyse avec **pip-audit**.  
Objectif : détecter les **vulnérabilités connues (CVE)** dans les dépendances Python.

---

## 🚨 Résultat pip-audit

### Ce que pip-audit a détecté
- Plusieurs vulnérabilités critiques ont été trouvées dans les dépendances utilisées par Flask, en particulier **Flask** et **Werkzeug**.  
- D’autres librairies comme **Click**, **Itsdangerous**, **Jinja2** et **MarkupSafe** ne présentent pas de vulnérabilité connue dans les versions scannées.

---

## 🔎 Détail des vulnérabilités

### 1) Flask 2.3.2
- **CVE** : `PYSEC-2023-62` / `CVE-2023-30861`  
- **Problème** : risque de fuite de cookies/session via certains proxys.  
- **Impact** : exposition de données sensibles entre utilisateurs.  
- **Correction** : mettre à jour vers `2.3.3` ou `2.2.5`.

---

### 2) Werkzeug 2.2.3
- **CVE-2023-46136 / PYSEC-2023-221**  
  - **Problème** : parsing de fichiers malveillants volumineux.  
  - **Impact** : attaque par **Denial of Service (DoS)**.  
  - **Fix** : `2.3.8` ou `3.0.1`.

- **CVE-2024-34069 / GHSA-2g68-c3qc-8985**  
  - **Problème** : le debugger peut être exploité par un attaquant.  
  - **Impact** : risque d’**exécution de code à distance (RCE)**.  
  - **Fix** : `3.0.1`.

- **CVE-2024-49767 / GHSA-f9vj-2wh5-fj8j**  
  - **Problème** : mauvaise gestion de chemins UNC sous Windows + Python 3.11.  
  - **Impact** : accès non intentionné à des fichiers.  
  - **Fix** : `3.0.6`.

- **GHSA-q34m-jh98-gwm2**  
  - **Problème** : parsing `multipart/form-data` peut contourner les limites mémoire (`max_form_memory_size`).  
  - **Impact** : épuisement mémoire (DoS).  
  - **Fix** : `3.0.6`.

---

### 3) Autres dépendances
- **Click 8.2.1** → pas de vulnérabilités.  
- **Itsdangerous 2.2.0** → pas de vulnérabilités.  
- **Jinja2 3.1.6** → pas de vulnérabilités.  
- **MarkupSafe 3.0.2** → pas de vulnérabilités.  

---

## ✅ Comment corriger
Mettre à jour Flask et Werkzeug vers des versions corrigées :
```bash
pip install --upgrade flask werkzeug
```

## ✅ Conclusion
- SonarQube détecte les vulnérabilités dans le code source.
- ZAP détecte les failles au runtime (en-têtes manquants, comportements dangereux).
- pip-audit détecte les vulnérabilités dans les dépendances.

En combinant les trois, on obtient une vision complète de la sécurité de l’application Flask :
Code + Runtime + Supply Chain

