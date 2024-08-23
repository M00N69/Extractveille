import streamlit as st
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import pandas as pd
from datetime import datetime

# Configure Streamlit to use "wide" mode
st.set_page_config(layout="wide")

# Ensure NLTK dependencies are downloaded
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')

# Fixer les dates par défaut
current_year = datetime.now().year
default_start_date = datetime(current_year, 1, 1)
default_end_date = datetime.now()

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
gif_url = "https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExZzl1djM4anJ3dGQxY3cwYmM2M2VyeDI4cDUyM3ozcmNvNzJjOWg3aiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/26gJzajW8IiyJs3YY/giphy.gif"

# Définir le CSS pour l'arrière-plan et les couleurs
css_background = f"""
<style>
.stApp {{
    background: url("{gif_url}") no-repeat center center fixed;
    background-size: cover;
    color: #F0F0F0;  /* Texte clair */
}}
.stSidebar {{
    background-color: #006d77 !important;  /* Bleu-vert */
    color: #EDF6F9;  /* Texte clair */
}}
.stSidebar .sidebar-content {{
    color: #EDF6F9;  /* Texte clair */
}}
.stSidebar input, .stSidebar selectbox, .stSidebar button {{
    color: #EDF6F9;  /* Texte clair */
    background-color: #83c5be;  /* Boutons et inputs en bleu-vert clair */
}}
button, .stButton > button {{
    color: #fff !important; /* Texte blanc */
    background-color: #3080F8 !important; /* Fond bleu */
}}
button:hover, .stButton > button:hover {{
    background-color: #1A5BB1 !important; /* Fond bleu plus foncé */
}}
.table-container {{
    display: flex;
    justify-content: center;
    width: 100%;
}}
table {{
    border-collapse: collapse;
    width: 100%;  /* S'assurer que le tableau utilise toute la largeur disponible */
    max-width: 100%;
    border: 1px solid #ddd;
    background-color: #29292F; /* Fond sombre */
}}

th, td {{
    border: 1px solid #ddd;
    text-align: left;
    padding: 8px;
    color: #F0F0F0;  /* Texte clair */
    word-wrap: break-word;  /* Permettre les retours à la ligne dans les cellules */
    white-space: normal;  /* Permettre les retours à la ligne */
}}

tr:nth-child(even) {{
    background-color: #333; /* Ligne paire plus foncée */
}}

th {{
    background-color: #333; /* En-têtes plus foncés */
    font-weight: bold;
}}

a {{
    color: #00d9d9; /* Bleu clair pour les liens */
    text-decoration: none; /* Supprimer le soulignement par défaut */
}}

a:hover {{
    text-decoration: underline; /* Soulignement au survol */
}}

.analyze-button {{
    padding: 4px 8px;
    color: #fff;
    background-color: #3080F8;
    border: none;
    cursor: pointer;
}}

.analyze-button:hover {{
    background-color: #1A5BB1;
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
with st.sidebar.expander("INTRODUCTION"):
    st.markdown("""
    Utilisez les filtres ci-dessous pour affiner les résultats affichés dans le tableau principal.
    - **Mots-clés**: Entrez des mots-clés séparés par des virgules pour rechercher dans les articles.
    - **Dates**: Sélectionnez une plage de dates pour filtrer les articles publiés entre ces dates.
    - **Rubriques**: Choisissez une ou plusieurs rubriques pour filtrer les articles en fonction de leur catégorie.
    - **Réinitialiser les filtres**: Cliquez pour réinitialiser tous les filtres.
    """)

# Filtre par mots-clés
mots_cles = st.sidebar.text_input("Entrez vos mots-clés (séparés par des virgules):")

# Filtre par date avec valeurs par défaut
date_debut = st.sidebar.date_input("Date de début:", default_start_date)
date_fin = st.sidebar.date_input("Date de fin:", default_end_date)

# Filtre par rubrique
rubriques = st.sidebar.multiselect("Choisissez les rubriques:", ["Alertes alimentaires", "Contaminants", "Signes de qualité", "OGM", "Alimentation animale", "Produits de la pêche", "Produits phytopharmaceutiques", "Biocides", "Fertilisants", "Hygiène", "Vins", "Fruits, légumes et végétaux", "Animaux et viandes", "Substances nutritionnelles", "Nouveaux aliments"])

# Button to clear all filters
if st.sidebar.button("Réinitialiser les filtres"):
    st.experimental_rerun()

# Initialize session state for selected row for analysis
if 'selected_row' not in st.session_state:
    st.session_state.selected_row = None

# Function to set selected row for analysis
def select_row_for_analysis(index):
    st.session_state.selected_row = index

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

# Filtrer et afficher les données
def afficher_tableau(data):
    # Filtrer le tableau par mots-clés, date et rubrique
    filtered_data = []
    for i, row in enumerate(data[1:]):  # Ignorer l'en-tête
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
                    filtered_data.append((i, row))

    if filtered_data:
        st.subheader("Résultats filtrés:")

        # Utiliser la fonction st.markdown() pour afficher le tableau en mode "wide"
        filtered_table_html = '<div class="table-container"><table>'
        filtered_table_html += '<thead><tr><th>' + '</th><th>'.join(data[0]) + '</th><th>Action</th></tr></thead>'
        filtered_table_html += '<tbody>'
        
        for i, row in filtered_data:
            filtered_table_html += '<tr><td>' + '</td><td>'.join(row) + f'</td><td><button class="analyze-button" onclick="select_row_for_analysis({i})">Analyser</button></td></tr>'
        
        filtered_table_html += '</tbody></table></div>'
        st.markdown(filtered_table_html, unsafe_allow_html=True)

    else:
        st.warning("Aucun résultat ne correspond aux filtres.")
    
    # Générer des résumés avec Gemini
    if st.session_state.selected_row is not None:
        row_index, row = filtered_data[st.session_state.selected_row]
        st.subheader("Analyse de l'article sélectionné:")
        lien_resume = row[1].split("href='")[1].split("'")[0]  # Extraire le lien "Résumé"
        with st.spinner('Analyse en cours...'):
            try:
                resume = generer_resume(f"{row[4]} {row[5]}", lien_resume)  # Passer le lien "Résumé"
                st.markdown(f"**Résumé de {row[4]}:**\n {resume}")
            except Exception as e:
                st.error(f"Erreur lors de l'analyse : {e}")
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
            st.dataframe(df, use_container_width=True)

        except requests.exceptions.RequestException as e:
            st.error(f"Erreur lors du téléchargement du fichier Excel: {e}")

if st.button("Editer"):
    url = "https://www.alexia-iaa.fr/ac/AC000/somAC001.htm"
    data = extraire_texte_et_liens(url)

    if data:
        afficher_tableau(data)
    else:
        st.error("Impossible d'extraire le tableau du bulletin.")

# Page séparée pour les données RASFF
def rasff_page():
    st.title("Données RASFF")

    # Filtre par semaine
    semaine_min = st.sidebar.slider("Semaine de début:", 1, 52, 1)
    semaine_max = st.sidebar.slider("Semaine de fin:", 1, 52, 52)

    url = "https://www.alexia-iaa.fr/ac/AC000/somAC001.htm"
    data = extraire_texte_et_liens(url)

    if data:
        # Extraire les fichiers Excel RASFF
        rasff_articles = [row for row in data if 'Alertes' in row[2]]
        for row in rasff_articles:
            excel_link = row[2].split("href='")[1].split("'")[0]  # Extraire le lien Excel
            try:
                excel_file = requests.get(excel_link)
                excel_file.raise_for_status()

                # Charger les données Excel
                df = pd.read_excel(excel_file.content, engine='openpyxl')

                # Filtrer les données par semaine
                if 'Semaine' in df.columns:
                    df_filtered = df[(df['Semaine'] >= semaine_min) & (df['Semaine'] <= semaine_max)]
                else:
                    df_filtered = df  # Si pas de colonne semaine, afficher tout

                st.subheader(f"Données RASFF pour {row[3]}")
                st.dataframe(df_filtered, use_container_width=True)

            except requests.exceptions.RequestException as e:
                st.error(f"Erreur lors du téléchargement du fichier Excel: {e}")
    else:
        st.error("Impossible d'extraire le tableau du bulletin.")

if st.sidebar.button("Afficher les données RASFF"):
    rasff_page()
