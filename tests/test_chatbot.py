"""
Tests fonctionnels du chatbot EPI.
Lance le serveur Flask avant d'exécuter : python app.py
"""

import requests
import json
from time import sleep

BASE_URL = "http://localhost:5000/chat"

# Questions de test couvrant toutes les thématiques EPI
QUESTIONS = [
    # Salutations
    "bonjour",
    "salut",
    # Présentation EPI
    "c'est quoi l'EPI ?",
    "présente-moi l'EPI",
    # Formations
    "quelles formations propose l'EPI ?",
    "génie informatique",
    "génie civil",
    "génie électrique",
    "réseaux et télécommunications",
    # Admission
    "comment s'inscrire à l'EPI ?",
    "quelles sont les conditions d'admission ?",
    "étapes d'inscription",
    # Frais et bourses
    "quels sont les frais de scolarité ?",
    "y a-t-il des bourses ?",
    # Vie étudiante
    "vie étudiante",
    "quels clubs existent à l'EPI ?",
    "sport à l'EPI",
    # Stages et débouchés
    "stages à l'EPI",
    "quels sont les débouchés après l'EPI ?",
    "projet de fin d'études",
    # Infrastructure
    "laboratoires",
    "bibliothèque",
    "transport pour aller à l'EPI",
    # Contact
    "comment contacter l'EPI ?",
    "adresse de l'EPI",
    # Orientation
    "quelle filière choisir ?",
    "certifications professionnelles",
    # Reconnaissance
    "l'EPI est-elle reconnue par l'État ?",
    "portes ouvertes",
    # Divers
    "merci",
    "au revoir",
    # Question hors sujet (doit renvoyer la réponse par défaut)
    "quelle est la capitale du Japon ?",
]


def test_question(question):
    """Teste une question et affiche le résultat."""
    print(f"\n{'='*60}")
    print(f"  Q : {question}")
    print(f"{'='*60}")
    try:
        response = requests.post(BASE_URL, json={"message": question}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            reponse = data.get("reponse", "Pas de réponse")
            # Tronquer pour l'affichage
            preview = reponse[:200] + "..." if len(reponse) > 200 else reponse
            print(f"  R : {preview}")
            # Vérification basique : la réponse ne doit pas contenir de référence ISET
            if "ISET" in reponse or "isetsf" in reponse:
                print("  ⚠  ATTENTION : Référence ISET détectée dans la réponse !")
                return False
            return True
        else:
            print(f"  ✗ Erreur HTTP : {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("  ✗ Serveur non accessible. Lancez d'abord : python app.py")
        return False
    except Exception as e:
        print(f"  ✗ Erreur : {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("  TESTS DU CHATBOT EPI")
    print("  École Privée d'Ingénierie et de Technologies")
    print("=" * 60)

    total = len(QUESTIONS)
    success = 0

    for question in QUESTIONS:
        if test_question(question):
            success += 1
        sleep(0.5)

    print(f"\n{'='*60}")
    print(f"  RÉSULTAT : {success}/{total} tests réussis")
    if success == total:
        print("  Tous les tests sont passés avec succès !")
    else:
        print(f"  {total - success} test(s) ont échoué.")
    print(f"{'='*60}")
