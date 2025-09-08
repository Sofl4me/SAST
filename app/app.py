from flask import Flask, request, jsonify
from markupsafe import Markup
from .db import get_db

app = Flask(__name__)

def init_db():
    db = get_db()
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
    db.execute("DELETE FROM users")
    db.executemany("INSERT INTO users(name) VALUES(?)", [("Alice",), ("Bob",)])
    db.commit()

@app.before_first_request
def _init():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/hello")
def hello():
    name = request.args.get("name", "world")
    return f"<h1>Hello {name}</h1>"

@app.get("/user")
def user():
    uid = request.args.get("id", "1")
    db = get_db()
    try:
            rows = db.execute(f"SELECT * FROM users WHERE id = {uid}").fetchall()
            return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)