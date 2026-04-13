# Chatbot EPI – École Privée d'Ingénierie et de Technologies

Assistant virtuel intelligent pour l'EPI, capable de répondre en français aux questions des utilisateurs sur les formations, l'admission, la vie étudiante, les stages et toutes les informations relatives à l'école.

## Fonctionnalités

- Réponses précises en français sur toutes les thématiques EPI
- Moteur de correspondance intelligent (normalisation, tokenisation, score Jaccard)
- Interface web moderne avec design aux couleurs de l'EPI
- Reconnaissance vocale (Web Speech API)
- Historique des conversations (localStorage)
- Système de votes (like / dislike) sur les réponses
- Suggestions rapides pour guider l'utilisateur
- Crawler intégré pour collecter les données depuis episup.com

## Structure du projet

```
Chatbot_Python/
├── app.py                  # Serveur Flask (routes /chat, /vote, /get_votes)
├── chatbot.py              # Moteur de correspondance intelligent
├── data.json               # Base de connaissances EPI (intents)
├── google_search.py        # Intégration recherche Google
├── collect_epi_data.py     # Crawler du site episup.com
├── insert_epi_data.py      # Insertion manuelle de données EPI
├── create_vote_file.py     # Initialisation du fichier de votes
├── test_chatbot.py         # Tests fonctionnels
├── epi_site_data.csv       # Données extraites du site EPI
├── votes.csv               # Votes des utilisateurs
├── requirements.txt        # Dépendances Python
└── templates/
    └── index.html          # Interface web du chatbot
```

## Installation

```bash
pip install -r requirements.txt
```

## Lancement

```bash
python app.py
```

Ouvrir dans le navigateur : [http://localhost:5000](http://localhost:5000)

## Collecte de données

Pour mettre à jour les données depuis le site EPI :

```bash
python collect_epi_data.py
```

## Tests

Lancer le serveur puis exécuter les tests :

```bash
python app.py &
python test_chatbot.py
```

## Technologies

- **Backend** : Python, Flask
- **Frontend** : HTML5, CSS3, JavaScript
- **NLP** : Tokenisation, normalisation, score Jaccard
- **Données** : JSON, CSV

## Site officiel

[https://episup.com/fr](https://episup.com/fr)
