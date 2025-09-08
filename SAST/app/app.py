from flask import Flask, request, render_template_string
from markupsafe import escape

app = Flask(__name__)

# Exemple volontairement vulnérable (XSS)
@app.route('/')
def index():
    name = request.args.get('name', 'visiteur')
    return render_template_string(f"<h1>Bonjour {name}</h1>")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
