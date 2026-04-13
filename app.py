import csv
import os
from flask import Flask, request, jsonify, render_template

from chatbot import get_response

app = Flask(__name__)

VOTES_FILE = "votes.csv"


def _ensure_votes_file():
    """Crée le fichier votes.csv s'il n'existe pas."""
    if not os.path.exists(VOTES_FILE):
        with open(VOTES_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["hash", "likes", "dislikes"])


def _read_votes():
    """Lit les votes depuis le CSV et retourne un dict {hash: {likes, dislikes}}."""
    _ensure_votes_file()
    votes = {}
    with open(VOTES_FILE, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            h = row.get("hash", "").strip()
            if h:
                votes[h] = {
                    "likes": int(row.get("likes", 0) or 0),
                    "dislikes": int(row.get("dislikes", 0) or 0),
                }
    return votes


def _write_votes(votes: dict):
    """Écrit le dict de votes dans le CSV."""
    with open(VOTES_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["hash", "likes", "dislikes"])
        for h, v in votes.items():
            writer.writerow([h, v["likes"], v["dislikes"]])


# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    response = get_response(user_message)
    return jsonify({"reponse": response})


@app.route("/get_votes", methods=["GET"])
def get_votes():
    """Retourne les compteurs like/dislike pour un hash donné."""
    response_hash = request.args.get("hash", "").strip()
    if not response_hash:
        return jsonify({"likes": 0, "dislikes": 0})

    votes = _read_votes()
    entry = votes.get(response_hash, {"likes": 0, "dislikes": 0})
    return jsonify(entry)


@app.route("/vote", methods=["POST"])
def vote():
    """Enregistre un vote (like ou dislike) pour une réponse."""
    data = request.json or {}
    response_hash = str(data.get("hash", "")).strip()
    vote_type = data.get("type", "")  # "like" ou "dislike"

    if not response_hash or vote_type not in ("like", "dislike"):
        return jsonify({"error": "Paramètres invalides"}), 400

    votes = _read_votes()
    if response_hash not in votes:
        votes[response_hash] = {"likes": 0, "dislikes": 0}

    if vote_type == "like":
        votes[response_hash]["likes"] += 1
    else:
        votes[response_hash]["dislikes"] += 1

    _write_votes(votes)
    return jsonify({"success": True, **votes[response_hash]})


if __name__ == "__main__":
    app.run(debug=True)
