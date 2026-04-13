"""
Insère des données manuelles complémentaires pour l'EPI dans epi_site_data.csv.
Utile pour ajouter des informations qui ne sont pas extraites automatiquement par le crawler.
"""

import csv
import os

EPI_DATA = [
    ["question", "réponse", "catégorie", "source"],
    [
        "Qu'est-ce que l'EPI ?",
        "L'EPI (École Privée d'Ingénierie et de Technologies) est un établissement "
        "privé d'enseignement supérieur en Tunisie, agréé par le Ministère de "
        "l'Enseignement Supérieur. L'EPI forme des ingénieurs et des techniciens "
        "dans les domaines de l'informatique, du génie civil, du génie électrique "
        "et du génie industriel.",
        "fr",
        "https://episup.com/fr",
    ],
    [
        "Quelles formations propose l'EPI ?",
        "L'EPI propose des formations en cycle ingénieur (5 ans) et en licence "
        "appliquée (3 ans) dans les spécialités suivantes :\n"
        "• Génie Informatique et Systèmes d'Information\n"
        "• Génie Civil et BTP\n"
        "• Génie Électrique et Systèmes Embarqués\n"
        "• Génie Industriel et Management\n"
        "• Technologies de l'Informatique\n"
        "• Réseaux et Télécommunications",
        "fr",
        "https://episup.com/fr",
    ],
    [
        "Comment s'inscrire à l'EPI ?",
        "Pour s'inscrire à l'EPI, il faut :\n"
        "1. Remplir le formulaire de candidature en ligne sur episup.com\n"
        "2. Soumettre les documents requis (bac, relevés, CIN, photos)\n"
        "3. Passer l'entretien de sélection\n"
        "4. Recevoir la lettre d'admission\n"
        "5. Régler les frais d'inscription",
        "fr",
        "https://episup.com/fr",
    ],
    [
        "Quels sont les frais de scolarité à l'EPI ?",
        "Les frais de scolarité varient selon la filière et le cycle choisi. "
        "L'EPI propose des facilités de paiement en plusieurs tranches. "
        "Des bourses d'excellence sont disponibles pour les meilleurs étudiants. "
        "Contactez l'administration pour les tarifs exacts.",
        "fr",
        "https://episup.com/fr",
    ],
    [
        "Quels sont les débouchés après l'EPI ?",
        "Les diplômés de l'EPI exercent comme ingénieurs en informatique, "
        "développeurs logiciels, ingénieurs en génie civil, chefs de projets IT, "
        "ingénieurs en automatisme et énergie renouvelable, consultants en "
        "cybersécurité, data scientists, etc. Le taux d'insertion professionnelle "
        "est très élevé.",
        "fr",
        "https://episup.com/fr",
    ],
    [
        "Comment contacter l'EPI ?",
        "Vous pouvez contacter l'EPI via :\n"
        "• Site web : https://episup.com/fr\n"
        "• Email : contact@episup.com\n"
        "• Téléphone : consultez le site officiel pour les numéros actualisés\n"
        "• Réseaux sociaux : Facebook, Instagram, LinkedIn",
        "fr",
        "https://episup.com/fr",
    ],
    [
        "Y a-t-il des stages à l'EPI ?",
        "Oui, les stages font partie intégrante de la formation à l'EPI :\n"
        "• Stage d'observation en 1ère année\n"
        "• Stage technique en 2ème et 3ème année\n"
        "• Stage de Projet de Fin d'Études (PFE) de 4 à 6 mois\n"
        "L'EPI dispose de partenariats avec de nombreuses entreprises nationales "
        "et internationales.",
        "fr",
        "https://episup.com/fr",
    ],
    [
        "L'EPI est-elle reconnue par l'État ?",
        "Oui, l'EPI est agréée par le Ministère de l'Enseignement Supérieur et "
        "de la Recherche Scientifique tunisien. Les diplômes délivrés sont "
        "officiellement reconnus.",
        "fr",
        "https://episup.com/fr",
    ],
    [
        "Quels sont les clubs étudiants à l'EPI ?",
        "L'EPI dispose de plusieurs clubs étudiants :\n"
        "• Club Informatique et Innovation\n"
        "• Club de Robotique\n"
        "• Club de Génie Civil\n"
        "• Association sportive\n"
        "• Club culturel et artistique\n"
        "• Junior Entreprise",
        "fr",
        "https://episup.com/fr",
    ],
    [
        "Y a-t-il des bourses à l'EPI ?",
        "Oui, l'EPI propose des bourses d'excellence pour les bacheliers mention "
        "Très Bien et pour les meilleurs étudiants en cours de scolarité. "
        "Des facilités de paiement et des prêts étudiants sont également "
        "disponibles via les banques partenaires.",
        "fr",
        "https://episup.com/fr",
    ],
    [
        "Quels sont les laboratoires de l'EPI ?",
        "L'EPI dispose de laboratoires modernes :\n"
        "• Laboratoires informatiques (IA, réseaux, cybersécurité)\n"
        "• Laboratoires d'électronique et systèmes embarqués\n"
        "• Laboratoires de génie civil et matériaux\n"
        "• Salles de TP équipées avec du matériel récent",
        "fr",
        "https://episup.com/fr",
    ],
]

FILENAME = "epi_site_data.csv"


def insert_data():
    mode = "a" if os.path.exists(FILENAME) else "w"
    with open(FILENAME, mode=mode, newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Écrire l'en-tête seulement si le fichier est nouveau
        start = 0 if mode == "a" else 0
        if mode == "w":
            writer.writerows(EPI_DATA)
        else:
            writer.writerows(EPI_DATA[1:])  # Pas de ré-écriture d'en-tête
    print(f"Les données EPI ont été ajoutées dans {FILENAME}")


if __name__ == "__main__":
    insert_data()
