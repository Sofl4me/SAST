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

Avec render_template_string (échappement explicite)

from flask import Flask, request, render_template_string
```python
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

## 🚨 Résultat ZAP

### Ce que ZAP a détecté
- **High (Critique)** : 0  
- **Medium (Moyen)** : 2  
- **Low (Faible)** : 3  
- **Informational (Infos)** : 1  

👉 Bonne nouvelle : pas de vulnérabilité critique.  
Cependant, plusieurs points de configuration de sécurité manquent, ce qui expose l’application à certains risques.

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

### 🔵 Informationnel
- **Storable and Cacheable Content**  
  - **Problème** : certains contenus peuvent être stockés ou mis en cache.  
  - **Impact** : pas critique, mais peut poser problème si des données sensibles sont concernées.  
  - **Correction** : définir des en-têtes HTTP adaptés, par exemple :  
    ```
    Cache-Control: no-store
    Pragma: no-cache
    ```

---

## 💡 Bonnes pratiques

- Toujours configurer des **en-têtes HTTP de sécurité** (CSP, X-Frame-Options, X-Content-Type-Options, etc.).  
- Empêcher le *clickjacking* et limiter les API navigateur accessibles.  
- Définir des politiques claires de cache pour éviter la fuite de données sensibles.  
- Garder **ZAP** dans le pipeline CI/CD : il détecte les failles runtime que SonarQube (analyse statique) ne voit pas.

---

## ✅ Conclusion
- **SonarQube** → détecte les failles **dans le code source** (ex. XSS).  
- **ZAP** → détecte les failles **au runtime** (mauvaises configurations HTTP, en-têtes manquants, comportements risqués).  

En combinant les deux outils dans ton pipeline CI/CD, tu obtiens une **analyse de sécurité complète** :  
- Vérification **statique** (code).  
- Vérification **dynamique** (application en exécution).  

