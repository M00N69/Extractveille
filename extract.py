import streamlit as st
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import pandas as pd
import google.generativeai as genai
from datetime import datetime

# Ensure NLTK dependencies are downloaded
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')

def extraire_texte_et_liens(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    table = soup.find('table')
    if table:
        rows = table.find_all('tr')
        data = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 7:
                row_data = [col.text.strip() for col in cols]
                for i, col in enumerate(cols):
                    if col.find('a'):
                        row_data[i] = f"<a href='{col.find('a')['href']}'>{col.text.strip()}</a>"
                data.append(row_data)

        return data
    else:
        return None

# URL du GIF
gif_url = "https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExbTl6aXY3dXp3djdjYzVyNGMyYWpnN3g3bnZ0NXo1emJ4aDdmdmY3YSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/a3IGFA4BKrE40/giphy.gif"

# Définir le CSS pour l'arrière-plan
css_background = f"""
<style>
.stApp {{
    background: url("{gif_url}") no-repeat center center fixed;
    background-size: cover;
}}
</style>
"""

# Injecter le CSS dans l'application Streamlit
st.markdown(css_background, unsafe_allow_html=True)

# Page Streamlit
st.title("VEILLE EN IAA")
st.write("Extraction du tableau et des liens du bulletin de veille")

# Barre latérale gauche pour les filtres
st.sidebar.title("Filtres")

# Introduction with collapse/expand effect
with st.sidebar.expander("Introduction"):
    st.markdown("""
    Utilisez les filtres ci-dessous pour affiner les résultats affichés dans le tableau principal.
    - **Mots-clés**: Entrez des mots-clés séparés par des virgules pour rechercher dans les articles.
    - **Dates**: Sélectionnez une plage de dates pour filtrer les articles publiés entre ces dates.
    - **Rubriques**: Choisissez une ou plusieurs rubriques pour filtrer les articles en fonction de leur catégorie.
    - **Réinitialiser les filtres**: Cliquez pour réinitialiser tous les filtres.
    - **Afficher le tableau principal**: Cochez pour afficher ou masquer le tableau principal.
    - **Afficher les résumés**: Cliquez pour afficher les résumés des articles filtrés.
    """)

# Filtre par mots-clés
mots_cles = st.sidebar.text_input("Entrez vos mots-clés (séparés par des virgules):")

# Filtre par date
date_debut = st.sidebar.date_input("Date de début:", datetime.now())
date_fin = st.sidebar.date_input("Date de fin:", datetime.now())

# Filtre par rubrique
rubriques = st.sidebar.multiselect("Choisissez les rubriques:", ["Alertes alimentaires", "Contaminants", "Signes de qualité", "OGM", "Alimentation animale", "Produits de la pêche", "Produits phytopharmaceutiques", "Biocides", "Fertilisants", "Hygiène", "Vins", "Fruits, légumes et végétaux", "Animaux et viandes", "Substances nutritionnelles", "Nouveaux aliments"])

# Button to clear all filters
if st.sidebar.button("Réinitialiser les filtres"):
    st.experimental_rerun()

# Initialize session state for showing summaries
if 'show_summaries' not in st.session_state:
    st.session_state.show_summaries = False

# Function to toggle the display of summaries
def toggle_summaries():
    st.session_state.show_summaries = not st.session_state.show_summaries

# Button to toggle summaries
st.sidebar.button("Afficher les résumés", on_click=toggle_summaries)

# Fonction pour calculer la pertinence des articles
def calculer_pertinence(texte_article, mots_cles):
    # Prétraitement du texte (suppression des stopwords et lemmatisation)
    stop_words = set(stopwords.words('french'))
    lemmatizer = WordNetLemmatizer()
    tokens_article = nltk.word_tokenize(texte_article)
    tokens_article = [lemmatizer.lemmatize(token.lower()) for token in tokens_article if token.isalpha() and token.lower() not in stop_words]

    tokens_mots_cles = nltk.word_tokenize(mots_cles)
    tokens_mots_cles = [lemmatizer.lemmatize(token.lower()) for token in tokens_mots_cles if token.isalpha() and token.lower() not in stop_words]

    # Convertir les tokens en chaînes de caractères
    texte_article = " ".join(tokens_article) 
    mots_cles = " ".join(tokens_mots_cles)

    # Utiliser un ensemble de mots-clés pour une meilleure correspondance
    mots_cles_set = set(mots_cles.split(",")) 

    # Vérifier la présence de chaque mot-clé dans l'article
    pertinence = 0
    for mot_cle in mots_cles_set:
        if mot_cle in texte_article.lower():
            pertinence += 1

    # Normaliser la pertinence
    pertinence = pertinence / len(mots_cles_set) if mots_cles_set else 0

    return pertinence

# Fonction pour générer des résumés avec Gemini
def generer_resume(texte, lien_resume):
    # Obtenir la clé API Gemini à partir des secrets Streamlit
    gemini_api_key = st.secrets["GEMINI_API_KEY"]

    # Configurer l'API Gemini
    genai.configure(api_key=gemini_api_key)

    # Définir les paramètres de génération
    generation_config = {
        "temperature": 2,
        "top_p": 0.4,
        "top_k": 32,
        "max_output_tokens": 8192,
    }

    # Définir les paramètres de sécurité
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]

    # Définir les instructions du système
    system_instruction = f"""
    Utilisez le texte du lien "Résumé" disponible dans le tableau pour générer un résumé concis et pertinent de l'article.
    Le lien "Résumé" est : {lien_resume} 
    """

    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest",
        generation_config=generation_config,
        system_instruction=system_instruction,
        safety_settings=safety_settings
    )

    # Générer le résumé en utilisant Gemini
    response = model.generate_text(text=texte)
    return response.text

if st.button("Editer"):
    url = "https://www.alexia-iaa.fr/ac/AC000/somAC001.htm"
    data = extraire_texte_et_liens(url)

    if data:
        st.subheader("Tableau extrait:")
        show_main_table = st.sidebar.checkbox("Afficher le tableau principal", value=True)

        if show_main_table:
            # Définir les styles CSS pour le tableau
            st.markdown(
                """
                <style>
                .table-container {
                    display: flex;
                    justify-content: center;
                    width: 100%;
                }
                table {
                    border-collapse: collapse;
                    width: 80%;
                    max-width: 1200px;
                    border: 1px solid #ddd;
                    background-color: #29292F; /* Fond sombre */
                }

                th, td {
                    border: 1px solid #ddd;
                    text-align: left;
                    padding: 8px;
                    color: #fff; /* Texte blanc */
                }

                tr:nth-child(even) {
                    background-color: #333; /* Ligne paire plus foncée */
                }

                th {
                    background-color: #333; /* En-têtes plus foncés */
                    font-weight: bold;
                }

                a {
                    color: #3080F8; /* Bleu clair pour les liens */
                    text-decoration: none; /* Supprimer le soulignement par défaut */
                }

                a:hover {
                    text-decoration: underline; /* Soulignement au survol */
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            # Utiliser la fonction st.markdown() pour afficher le tableau en mode "wide"
            st.markdown(
                f"""
                <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>{'</th><th>'.join(data[0])}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(f'<tr><td>{"</td><td>".join(row)}</td></tr>' for row in data[1:])}
                    </tbody>
                </table>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Filtrer le tableau par mots-clés, date et rubrique
        filtered_data = []
        for row in data[1:]:  # Ignorer l'en-tête
            # Vérifier si les mots-clés sont présents dans l'article
            texte_article = f"{row[4]} {row[5]}"  # Concaténer Titre et Rubrique
            pertinence = calculer_pertinence(texte_article, mots_cles)

            # Vérifier si la date est dans la plage sélectionnée
            try:
                date_publication = datetime.strptime(row[3], "%d/%m/%Y").date()
            except ValueError:
                continue

            if date_debut <= date_publication <= date_fin:
                # Vérifier si la rubrique est sélectionnée
                if not rubriques or any(rubrique in row[5] for rubrique in rubriques):
                    if pertinence > 0.5:  # Seuil de pertinence
                        filtered_data.append(row)

        if filtered_data:
            st.subheader("Résultats filtrés:")

            # Définir les styles CSS pour le tableau
            st.markdown(
                """
                <style>
                .table-container {
                    display: flex;
                    justify-content: center;
                    width: 100%;
                }
                table {
                    border-collapse: collapse;
                    width: 80%;
                    max-width: 1200px;
                    border: 1px solid #ddd;
                    background-color: #29292F; /* Fond sombre */
                }

                th, td {
                    border: 1px solid #ddd;
                    text-align: left;
                    padding: 8px;
                    color: #fff; /* Texte blanc */
                }

                tr:nth-child(even) {
                    background-color: #333; /* Ligne paire plus foncée */
                }

                th {
                    background-color: #333; /* En-têtes plus foncés */
                    font-weight: bold;
                }

                a {
                    color: #3080F8; /* Bleu clair pour les liens */
                    text-decoration: none; /* Supprimer le soulignement par défaut */
                }

                a:hover {
                    text-decoration: underline; /* Soulignement au survol */
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            # Utiliser la fonction st.markdown() pour afficher le tableau en mode "wide"
            st.markdown(
                f"""
                <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>{'</th><th>'.join(data[0])}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(f'<tr><td>{"</td><td>".join(row)}</td></tr>' for row in filtered_data)}
                    </tbody>
                </table>
                </div>
                """,
                unsafe_allow_html=True
            )

        else:
            st.warning("Aucun résultat ne correspond aux filtres.")

        # Générer des résumés avec Gemini
        if st.session_state.show_summaries and filtered_data:
            st.subheader("Résumés des articles:")
            for row in filtered_data:
                lien_resume = row[1].split("href='")[1].split("'")[0]  # Extraire le lien "Résumé"
                resume = generer_resume(f"{row[4]} {row[5]}", lien_resume)  # Passer le lien "Résumé"
                st.markdown(f"**Résumé de {row[4]}:**\n {resume}")
                st.write("---")

        # Extraire les fichiers Excel RASFF
        rasff_articles = [row for row in data if 'Alertes' in row[2]]
        for row in rasff_articles:
            excel_link = row[2].split("href='")[1].split("'")[0]  # Extraire le lien Excel
            try:
                excel_file = requests.get(excel_link)
                excel_file.raise_for_status()

                # Charger les données Excel
                df = pd.read_excel(excel_file.content, engine='openpyxl')

                st.subheader(f"Données RASFF pour {row[3]}")
                st.dataframe(df)

            except requests.exceptions.RequestException as e:
                st.error(f"Erreur lors du téléchargement du fichier Excel: {e}")

    else:
        st.error("Impossible d'extraire le tableau du bulletin.")

