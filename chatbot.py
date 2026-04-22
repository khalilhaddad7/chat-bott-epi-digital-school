"""
Moteur NLP du chatbot EPI.

Combine plusieurs techniques pour comprendre les requêtes variées :
  1. Correspondance exacte / partielle (priorité haute)
  2. TF-IDF vectorisation + similarité cosinus
  3. Expansion par synonymes
  4. Matching flou (Levenshtein) pour tolérance aux fautes
  5. Recherche dans la base CSV complémentaire
  6. Suivi de contexte conversationnel
  7. Suggestions intelligentes
  8. Réponse par défaut avec suggestions
"""

import csv
import json
import math
import os
import random
import re
import unicodedata
from collections import Counter

# ── Chargement des données ────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

with open(os.path.join(DATA_DIR, "data.json"), encoding="utf-8") as f:
    data = json.load(f)

CSV_FILE = os.path.join(DATA_DIR, "epi_site_data.csv")
csv_knowledge = []
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames and "Question" in reader.fieldnames:
            for row in reader:
                q = (row.get("Question") or "").strip()
                r = (row.get("Réponse") or row.get("Reponse") or "").strip()
                if q and r and len(r) > 20:
                    csv_knowledge.append({"question": q, "response": r})

# ── Synonymes métier (expansion de requêtes) ──────────────────────────────────

SYNONYMS = {
    "inscription": ["inscrire", "candidature", "postuler", "admission", "intégrer", "rejoindre"],
    "formation": ["filière", "filiere", "spécialité", "specialite", "cursus", "programme", "études", "etudes", "diplôme", "diplome"],
    "frais": ["coût", "cout", "prix", "tarif", "paiement", "scolarité", "scolarite", "budget", "argent"],
    "stage": ["pfe", "projet fin", "entreprise", "professionnel", "insertion"],
    "contact": ["téléphone", "telephone", "adresse", "email", "mail", "localisation", "coordonnées", "coordonnees", "joindre"],
    "bourse": ["aide financière", "aide financiere", "financement", "réduction", "reduction", "scholarship", "mérite", "merite"],
    "informatique": ["info", "développement", "developpement", "programmation", "code", "logiciel", "software", "ia", "intelligence artificielle", "cybersécurité", "cybersecurite", "data"],
    "civil": ["btp", "bâtiment", "batiment", "construction", "structure", "béton", "beton", "chantier"],
    "électrique": ["electrique", "électronique", "electronique", "embarqué", "embarque", "automatisme", "robotique", "énergie", "energie"],
    "industriel": ["production", "qualité", "qualite", "logistique", "supply chain", "lean", "usine", "maintenance"],
    "emploi": ["travail", "métier", "metier", "carrière", "carriere", "débouchés", "debouches", "recrutement", "salaire"],
    "réseau": ["reseau", "réseaux", "reseaux", "télécom", "telecom", "cisco", "wifi", "internet"],
    "club": ["association", "activité", "activite", "loisir", "sport", "événement", "evenement"],
    "professeur": ["enseignant", "prof", "formateur", "encadrant", "pédagogique", "pedagogique"],
    "laboratoire": ["labo", "tp", "travaux pratiques", "équipement", "equipement", "matériel", "materiel"],
    "logement": ["hébergement", "hebergement", "résidence", "residence", "foyer", "chambre", "habitation", "colocation"],
    "étranger": ["etranger", "international", "visa", "mobilité", "mobilite", "erasmus", "échange", "echange"],
    "diplôme": ["diplome", "reconnaissance", "accréditation", "accreditation", "agréé", "agree", "ministère", "ministere", "équivalence", "equivalence"],
    "master": ["mastère", "mastere", "doctorat", "phd", "thèse", "these", "recherche", "post-licence", "bac+5"],
    "epi": ["école privée", "ecole privee", "episup", "école d'ingénieurs", "ecole d'ingenieurs"],
}

# ── Mots-clés de suivi conversationnel ────────────────────────────────────────

FOLLOW_UP_PATTERNS = [
    "et", "aussi", "encore", "autre", "plus d'infos", "plus de détails",
    "détails", "details", "expliquer", "préciser", "elaborer",
    "c'est-à-dire", "c'est quoi", "comment", "pourquoi",
    "en savoir plus", "dis m'en plus", "dis-moi plus",
    "tu peux expliquer", "peux-tu", "pouvez-vous",
    "quoi d'autre", "autre chose", "et quoi", "quoi encore",
]

# ── Tags vers suggestions associées ──────────────────────────────────────────

TAG_SUGGESTIONS = {
    "salutation": ["Quelles formations propose l'EPI ?", "Comment s'inscrire ?", "Présente-moi l'EPI"],
    "presentation_epi": ["Quelles formations ?", "Comment s'inscrire ?", "Pourquoi choisir l'EPI ?"],
    "formations": ["Génie Informatique", "Génie Civil", "Génie Électrique", "Génie Industriel"],
    "genie_informatique": ["Débouchés informatique ?", "Langages enseignés ?", "Certifications ?"],
    "genie_civil": ["Débouchés génie civil ?", "Logiciels utilisés ?", "Durée de la formation ?"],
    "genie_electrique": ["Débouchés électrique ?", "Laboratoires ?", "Certifications ?"],
    "genie_industriel": ["Débouchés industriel ?", "Supply Chain ?", "Durée de la formation ?"],
    "admission": ["Quel bac faut-il ?", "Frais de scolarité ?", "Bourses disponibles ?"],
    "frais_scolarite": ["Bourses disponibles ?", "Paiement en plusieurs fois ?", "Comment s'inscrire ?"],
    "contact": ["Horaires d'ouverture ?", "Portes ouvertes ?", "Comment s'inscrire ?"],
    "stages": ["Comment se passe le PFE ?", "Stage à l'étranger ?", "Débouchés ?"],
    "pfe": ["Durée du PFE ?", "Aide pour trouver un stage ?", "Débouchés ?"],
    "vie_etudiante": ["Clubs disponibles ?", "Sports ?", "Restauration ?"],
    "bourses": ["Frais de scolarité ?", "Comment s'inscrire ?", "Paiement en tranches ?"],
    "debouches": ["Formations ?", "Stages ?", "Partenariats ?"],
    "aide": ["Formations ?", "Admission ?", "Contact ?"],
    "merci": ["Autre question ?", "Formations ?", "Contact EPI ?"],
    "au_revoir": [],
    "etat": ["Comment puis-je vous aider ?", "Formations ?", "Admission ?"],
    "identite_bot": ["Formations ?", "Admission ?", "Contact ?"],
    "bac_requis": ["Comment s'inscrire ?", "Frais ?", "Bourses ?"],
    "laboratoires": ["Formations ?", "Vie étudiante ?", "Équipements ?"],
    "logement": ["Transport ?", "Restauration ?", "Contact ?"],
    "partenariats": ["Mobilité internationale ?", "Double diplôme ?", "Stages ?"],
    "masters": ["Partenariats ?", "Débouchés ?", "Reconnaissance du diplôme ?"],
    "certifications": ["Formations ?", "Débouchés ?", "Partenariats ?"],
    "reconnaissance": ["Formations ?", "Débouchés ?", "Étudiants internationaux ?"],
    "orientation": ["Génie Informatique ?", "Génie Civil ?", "Génie Électrique ?"],
    "directeur": ["Présentation EPI ?", "Contact ?", "Historique de l'EPI ?"],
    "nombre_professeurs": ["Formations ?", "Laboratoires ?", "Vie étudiante ?"],
    "nombre_etudiants": ["Formations ?", "Clubs étudiants ?", "Capacité d'accueil ?"],
    "adresse_exacte": ["Transport ?", "Contact ?", "Portes ouvertes ?"],
    "date_creation": ["Présentation EPI ?", "Directeur ?", "Reconnaissance ?"],
    "taux_reussite": ["Formations ?", "Débouchés ?", "Vie étudiante ?"],
    "cout_exact": ["Bourses ?", "Paiement en tranches ?", "Comment s'inscrire ?"],
    "inscription_en_ligne": ["Documents requis ?", "Frais ?", "Contact ?"],
    "emploi_du_temps": ["Résultats ?", "Règlement ?", "Contact ?"],
    "alternance": ["Stages ?", "Débouchés ?", "Formations ?"],
    "concours": ["Vie étudiante ?", "Clubs ?", "Formations ?"],
    "sante": ["Vie étudiante ?", "Contact ?", "Sports ?"],
    "projets_etudiants": ["Formations ?", "Stages ?", "PFE ?"],
    "reseau_alumni": ["Débouchés ?", "Partenariats ?", "Stages ?"],
    "horaires_administration": ["Contact ?", "Adresse ?", "Inscription ?"],
    "difference_licence_ingenieur": ["Formations ?", "Durée des études ?", "Frais ?"],
}

DEFAULT_SUGGESTIONS = ["Formations EPI", "Comment s'inscrire ?", "Frais de scolarité ?"]

# ── Normalisation & tokenisation ──────────────────────────────────────────────

STOP_WORDS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "et", "en",
    "est", "je", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles",
    "me", "te", "se", "ce", "ci", "ca", "cet", "cette", "ces",
    "que", "qui", "quoi", "ou", "mais", "donc", "car", "ni", "y",
    "mon", "ton", "son", "ma", "ta", "sa", "mes", "tes", "ses",
    "pour", "par", "sur", "sous", "avec", "sans", "dans", "vers",
    "plus", "moins", "tres", "bien", "tout", "tous", "toutes",
    "avoir", "etre", "a", "au", "aux", "ne", "pas", "si", "comme",
    "vouloir", "pouvoir", "faire", "dire", "aller", "voir", "savoir",
    "comment", "quand", "pourquoi", "combien", "quelles", "quelle",
    "quels", "quel", "d", "l", "s", "n", "c", "j", "qu",
    "moi", "toi", "soi", "leur", "leurs", "notre", "votre", "nos", "vos",
    "aussi", "deja", "encore", "jamais", "rien", "peu", "beaucoup",
    "oui", "non", "ok", "alors", "bon", "ah", "oh", "eh",
    "suis", "es", "sommes", "etes", "sont", "ai", "as", "avons", "avez", "ont",
    "etait", "sera", "serait", "peut", "veut", "faut", "doit",
}


def normalize(text):
    """Normalise : minuscules, suppression accents et ponctuation."""
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text):
    """Retourne la liste de tokens normalisés."""
    return normalize(text).split()


def meaningful_tokens(text):
    """Tokens significatifs (sans stop words)."""
    return [t for t in tokenize(text) if t not in STOP_WORDS and len(t) > 1]


def expand_with_synonyms(tokens):
    """Étend une liste de tokens avec les synonymes connus."""
    expanded = set(tokens)
    for token in tokens:
        for key, syns in SYNONYMS.items():
            key_norm = normalize(key)
            if token == key_norm:
                for s in syns:
                    expanded.update(normalize(s).split())
            else:
                for s in syns:
                    if token in normalize(s).split():
                        expanded.add(key_norm)
                        break
    return expanded


# ── Distance de Levenshtein (matching flou) ──────────────────────────────────

def levenshtein_distance(s1, s2):
    """Calcule la distance de Levenshtein entre deux chaînes."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]


def fuzzy_match_score(token, target):
    """Score de correspondance floue (0–1). 1 = parfait."""
    if token == target:
        return 1.0
    max_len = max(len(token), len(target))
    if max_len == 0:
        return 0.0
    dist = levenshtein_distance(token, target)
    # Tolérance : 1 erreur pour les mots de 4+ lettres, 2 pour 7+
    max_errors = 1 if max_len >= 4 else 0
    if max_len >= 7:
        max_errors = 2
    if dist <= max_errors:
        return 1.0 - (dist / max_len)
    return 0.0


def score_fuzzy_match(msg_tokens, pattern):
    """Score par matching flou des tokens."""
    pattern_tokens = meaningful_tokens(pattern)
    if not pattern_tokens or not msg_tokens:
        return 0

    total_score = 0
    matched = 0
    for pt in pattern_tokens:
        best = 0
        for mt in msg_tokens:
            s = fuzzy_match_score(mt, pt)
            if s > best:
                best = s
        if best > 0.6:
            total_score += best
            matched += 1

    if matched == 0:
        return 0

    coverage = matched / len(pattern_tokens)
    return coverage * total_score * 3


# ── TF-IDF ────────────────────────────────────────────────────────────────────

class TfIdfMatcher:
    """Moteur TF-IDF léger pour les intents."""

    def __init__(self, intents):
        self.intents = intents
        self.documents = []   # liste de (intent_idx, token_list)
        self.idf = {}
        self._build_index()

    def _build_index(self):
        all_docs = []
        for idx, intent in enumerate(self.intents):
            for pattern in intent["patterns"]:
                tokens = meaningful_tokens(pattern)
                if tokens:
                    self.documents.append((idx, tokens))
                    all_docs.append(set(tokens))

        # IDF
        n = len(all_docs) + 1
        all_tokens = set()
        for doc in all_docs:
            all_tokens.update(doc)
        for token in all_tokens:
            df = sum(1 for doc in all_docs if token in doc)
            self.idf[token] = math.log(n / (df + 1)) + 1

    def _tfidf_vector(self, tokens):
        """Construit un vecteur TF-IDF."""
        tf = Counter(tokens)
        total = len(tokens) or 1
        vec = {}
        for t, count in tf.items():
            vec[t] = (count / total) * self.idf.get(t, 1.0)
        return vec

    def _cosine_similarity(self, vec_a, vec_b):
        """Similarité cosinus entre deux vecteurs."""
        common = set(vec_a) & set(vec_b)
        if not common:
            return 0.0
        dot = sum(vec_a[t] * vec_b[t] for t in common)
        norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
        norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def find_best(self, query_tokens, top_n=3):
        """Trouve les meilleurs intents pour les tokens donnés."""
        query_vec = self._tfidf_vector(query_tokens)
        if not query_vec:
            return []

        scores = {}
        for idx, doc_tokens in self.documents:
            doc_vec = self._tfidf_vector(doc_tokens)
            sim = self._cosine_similarity(query_vec, doc_vec)
            if idx not in scores or sim > scores[idx]:
                scores[idx] = sim

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [(idx, score) for idx, score in ranked[:top_n] if score > 0]


# Construction de l'index TF-IDF
tfidf_matcher = TfIdfMatcher(data["intents"])


# ── Scoring combiné ──────────────────────────────────────────────────────────

def score_exact_match(message_norm, pattern):
    """Score pour la correspondance exacte/partielle."""
    pattern_norm = normalize(pattern)
    if not pattern_norm:
        return 0

    # Correspondance exacte complète
    if pattern_norm == message_norm:
        return 20

    # Pattern contenu dans le message (exiger un mot entier pour les patterns courts)
    if pattern_norm in message_norm:
        if len(pattern_norm) <= 3:
            if re.search(r"\b" + re.escape(pattern_norm) + r"\b", message_norm):
                return 12
        else:
            return 12 + min(len(pattern_norm) / 10, 3)

    # Message contenu dans le pattern (question courte)
    if len(message_norm) > 3 and message_norm in pattern_norm:
        return 8

    return 0


def score_token_overlap(msg_tokens_set, pattern):
    """Score par chevauchement de tokens."""
    pattern_tokens = set(meaningful_tokens(pattern))
    if not pattern_tokens or not msg_tokens_set:
        return 0

    intersection = msg_tokens_set & pattern_tokens
    if not intersection:
        return 0

    # Jaccard pondéré
    union = msg_tokens_set | pattern_tokens
    jaccard = len(intersection) / len(union)

    # Couverture du pattern
    coverage = len(intersection) / len(pattern_tokens)

    score = jaccard * 5 + coverage * 5

    # Bonus si tous les tokens du pattern sont dans le message
    if pattern_tokens.issubset(msg_tokens_set):
        score += 4

    return score


def score_synonym_match(msg_expanded, pattern):
    """Score avec expansion par synonymes."""
    pattern_tokens = set(meaningful_tokens(pattern))
    if not pattern_tokens or not msg_expanded:
        return 0

    intersection = msg_expanded & pattern_tokens
    if not intersection:
        return 0

    coverage = len(intersection) / len(pattern_tokens)
    return coverage * 4


def bigrams(tokens):
    """Génère les bigrammes d'une liste de tokens."""
    return set(zip(tokens, tokens[1:])) if len(tokens) >= 2 else set()


def score_bigram_match(msg_tokens_list, pattern):
    """Score par bigrammes communs."""
    pattern_tokens = meaningful_tokens(pattern)
    msg_bigrams = bigrams(msg_tokens_list)
    pat_bigrams = bigrams(pattern_tokens)
    if not msg_bigrams or not pat_bigrams:
        return 0
    common = msg_bigrams & pat_bigrams
    return (len(common) / max(len(pat_bigrams), 1)) * 4


# ── Recherche CSV ─────────────────────────────────────────────────────────────

def search_csv(msg_tokens_set, msg_expanded, message_norm):
    """Cherche dans la base CSV une réponse pertinente."""
    if not csv_knowledge:
        return None

    best_score = 0
    best_entry = None

    for entry in csv_knowledge:
        q_norm = normalize(entry["question"])
        q_tokens = set(meaningful_tokens(entry["question"]))

        score = 0

        if q_norm in message_norm or message_norm in q_norm:
            score += 8

        if q_tokens and msg_tokens_set:
            common = msg_tokens_set & q_tokens
            if common:
                score += (len(common) / len(q_tokens)) * 5

        if q_tokens and msg_expanded:
            common_syn = msg_expanded & q_tokens
            if common_syn:
                score += (len(common_syn) / len(q_tokens)) * 3

        if score > best_score:
            best_score = score
            best_entry = entry

    if best_score >= 4 and best_entry:
        return best_entry["response"]
    return None


# ── Détection de suivi conversationnel ────────────────────────────────────────

def is_follow_up(message):
    """Détecte si le message est un suivi de conversation."""
    message_norm = normalize(message)
    msg_tokens = tokenize(message)

    # Message très court (1-3 mots) = probable suivi
    if len(msg_tokens) <= 3:
        for pattern in FOLLOW_UP_PATTERNS:
            if normalize(pattern) in message_norm:
                return True

    # Commence par "et", "aussi", "encore"
    if msg_tokens and msg_tokens[0] in ("et", "aussi", "encore", "autre", "plus"):
        return True

    return False


def merge_context_tokens(message, context_messages):
    """Fusionne les tokens du message avec le contexte récent."""
    all_tokens = meaningful_tokens(message)

    # Ajouter les tokens des 2 derniers messages utilisateur du contexte
    for ctx_msg in context_messages[-2:]:
        ctx_tokens = meaningful_tokens(ctx_msg)
        for t in ctx_tokens:
            if t not in all_tokens:
                all_tokens.append(t)

    return all_tokens


# ── Fonction principale ───────────────────────────────────────────────────────

def get_response(message, context=None):
    """
    Retourne la meilleure réponse pour un message donné.

    Args:
        message: Le message de l'utilisateur
        context: Liste optionnelle des messages précédents de l'utilisateur
                 pour le suivi conversationnel

    Returns:
        dict avec 'response', 'tag', 'confidence', 'suggestions'
    """
    if not message or not message.strip():
        return {
            "response": "Veuillez entrer votre question. Je suis là pour vous aider !",
            "tag": None,
            "confidence": 0,
            "suggestions": DEFAULT_SUGGESTIONS,
        }

    message_norm = normalize(message)
    msg_tokens_list = meaningful_tokens(message)
    msg_tokens_set = set(msg_tokens_list)
    msg_expanded = expand_with_synonyms(msg_tokens_list)

    # Gestion du suivi conversationnel
    use_context = False
    if context and is_follow_up(message):
        use_context = True
        merged_tokens = merge_context_tokens(message, context)
        msg_tokens_list_ctx = merged_tokens
        msg_tokens_set_ctx = set(merged_tokens)
        msg_expanded_ctx = expand_with_synonyms(merged_tokens)
    else:
        msg_tokens_list_ctx = msg_tokens_list
        msg_tokens_set_ctx = msg_tokens_set
        msg_expanded_ctx = msg_expanded

    # ── Étape 1 : scoring combiné (exact + tokens + synonymes + bigrammes + flou) ──
    best_score = 0
    best_intent = None

    for intent in data["intents"]:
        intent_score = 0
        for pattern in intent["patterns"]:
            s = 0
            s += score_exact_match(message_norm, pattern)
            s += score_token_overlap(msg_tokens_set, pattern)
            s += score_synonym_match(msg_expanded, pattern)
            s += score_bigram_match(msg_tokens_list, pattern)
            s += score_fuzzy_match(msg_tokens_list, pattern)
            if s > intent_score:
                intent_score = s

        if intent_score > best_score:
            best_score = intent_score
            best_intent = intent

    # Si score élevé → réponse directe
    if best_score >= 6 and best_intent:
        tag = best_intent["tag"]
        return {
            "response": random.choice(best_intent["responses"]),
            "tag": tag,
            "confidence": min(best_score / 20, 1.0),
            "suggestions": TAG_SUGGESTIONS.get(tag, DEFAULT_SUGGESTIONS),
        }

    # ── Étape 1b : si suivi, réessayer avec contexte fusionné ──
    if use_context:
        ctx_best_score = 0
        ctx_best_intent = None
        for intent in data["intents"]:
            intent_score = 0
            for pattern in intent["patterns"]:
                s = 0
                s += score_token_overlap(msg_tokens_set_ctx, pattern)
                s += score_synonym_match(msg_expanded_ctx, pattern)
                s += score_fuzzy_match(msg_tokens_list_ctx, pattern)
                if s > intent_score:
                    intent_score = s
            if intent_score > ctx_best_score:
                ctx_best_score = intent_score
                ctx_best_intent = intent

        if ctx_best_score >= 5 and ctx_best_intent:
            tag = ctx_best_intent["tag"]
            return {
                "response": random.choice(ctx_best_intent["responses"]),
                "tag": tag,
                "confidence": min(ctx_best_score / 20, 1.0),
                "suggestions": TAG_SUGGESTIONS.get(tag, DEFAULT_SUGGESTIONS),
            }

    # ── Étape 2 : TF-IDF ──
    tfidf_tokens = list(msg_expanded_ctx) if msg_expanded_ctx else msg_tokens_list_ctx
    tfidf_results = tfidf_matcher.find_best(tfidf_tokens, top_n=3)

    if tfidf_results:
        top_idx, top_score = tfidf_results[0]
        if top_score >= 0.25:
            intent = data["intents"][top_idx]
            tag = intent["tag"]
            return {
                "response": random.choice(intent["responses"]),
                "tag": tag,
                "confidence": min(top_score, 1.0),
                "suggestions": TAG_SUGGESTIONS.get(tag, DEFAULT_SUGGESTIONS),
            }

    # ── Étape 3 : combiner score faible + TF-IDF ──
    if best_score >= 3 and best_intent:
        tag = best_intent["tag"]
        return {
            "response": random.choice(best_intent["responses"]),
            "tag": tag,
            "confidence": min(best_score / 20, 1.0),
            "suggestions": TAG_SUGGESTIONS.get(tag, DEFAULT_SUGGESTIONS),
        }

    if tfidf_results:
        top_idx, top_score = tfidf_results[0]
        if top_score >= 0.15:
            intent = data["intents"][top_idx]
            tag = intent["tag"]
            return {
                "response": random.choice(intent["responses"]),
                "tag": tag,
                "confidence": min(top_score, 1.0),
                "suggestions": TAG_SUGGESTIONS.get(tag, DEFAULT_SUGGESTIONS),
            }

    # ── Étape 4 : recherche dans le CSV ──
    csv_result = search_csv(msg_tokens_set_ctx, msg_expanded_ctx, message_norm)
    if csv_result:
        return {
            "response": csv_result,
            "tag": "csv_match",
            "confidence": 0.5,
            "suggestions": DEFAULT_SUGGESTIONS,
        }

    # ── Étape 5 : suggestions intelligentes basées sur les mots-clés ──
    # Trouver les tags les plus proches pour proposer des suggestions pertinentes
    partial_suggestions = []
    if tfidf_results:
        for idx, score in tfidf_results[:3]:
            intent = data["intents"][idx]
            tag = intent["tag"]
            sug = TAG_SUGGESTIONS.get(tag, [])
            for s in sug:
                if s not in partial_suggestions:
                    partial_suggestions.append(s)
                if len(partial_suggestions) >= 3:
                    break
            if len(partial_suggestions) >= 3:
                break

    if not partial_suggestions:
        partial_suggestions = DEFAULT_SUGGESTIONS

    # ── Étape 6 : réponse par défaut ──
    return {
        "response": (
            "Désolé, je n'ai pas bien compris votre question.\n\n"
            "Je peux vous renseigner sur :\n"
            "• Les **formations et filières** de l'EPI\n"
            "• Les modalités d'**admission et inscription**\n"
            "• Les **frais de scolarité** et bourses\n"
            "• La **vie étudiante** et les clubs\n"
            "• Les **stages** et débouchés professionnels\n"
            "• Les **contacts** et localisation de l'EPI\n\n"
            "Vous pouvez aussi consulter notre site : https://episup.com/fr"
        ),
        "tag": None,
        "confidence": 0,
        "suggestions": partial_suggestions[:3],
    }
