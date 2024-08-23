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

# Function to extract text and links from the website
def extraire_texte_et_liens(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    table = soup.find('table')
    if not table:
        return None

    rows = table.find_all('tr')
    data = []

    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 7:  # Ensure that there are at least 7 columns to process
            continue

        fiche = cols[0].text.strip()
        resume_link = cols[1].find('a').get('href') if cols[1].find('a') else ''
        resume = f"<a href='{resume_link}'>Résumé</a>"
        publication = cols[2].text.strip()
        date_publication = cols[3].text.strip()
        titre = cols[4].text.strip()
        rubrique_profil = cols[5].text.strip()

        # Append the extracted data as a list
        row_data = [fiche, resume, publication, date_publication, titre, rubrique_profil]
        data.append(row_data)

    return data

# Inject the CSS into the Streamlit app
st.markdown(css_background, unsafe_allow_html=True)

# Streamlit Page
st.title("VEILLE EN IAA")
st.write("Extraction du tableau et des liens du bulletin de veille")

# Left sidebar for filters
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

# Filter by keywords
mots_cles = st.sidebar.text_input("Entrez vos mots-clés (séparés par des virgules):")

# Filter by date with default values
current_year = datetime.now().year
default_start_date = datetime(current_year, 1, 1)
default_end_date = datetime.now()

date_debut = st.sidebar.date_input("Date de début:", default_start_date)
date_fin = st.sidebar.date_input("Date de fin:", default_end_date)

# Filter by category
rubriques = st.sidebar.multiselect("Choisissez les rubriques:", [
    "Alertes alimentaires", "Contaminants", "Signes de qualité", "OGM", 
    "Alimentation animale", "Produits de la pêche", "Produits phytopharmaceutiques", 
    "Biocides", "Fertilisants", "Hygiène", "Vins", "Fruits, légumes et végétaux", 
    "Animaux et viandes", "Substances nutritionnelles", "Nouveaux aliments"
])

# Button to clear all filters
if st.sidebar.button("Réinitialiser les filtres"):
    st.experimental_rerun()

# Initialize session state for selected row for analysis
if 'selected_row' not in st.session_state:
    st.session_state.selected_row = None

# Function to calculate the relevance of articles
def calculer_pertinence(texte_article, mots_cles):
    stop_words = set(stopwords.words('french'))
    lemmatizer = WordNetLemmatizer()
    tokens_article = nltk.word_tokenize(texte_article)
    tokens_article = [lemmatizer.lemmatize(token.lower()) for token in tokens_article if token.isalpha() and token.lower() not in stop_words]

    tokens_mots_cles = nltk.word_tokenize(mots_cles)
    tokens_mots_cles = [lemmatizer.lemmatize(token.lower()) for token in tokens_mots_cles if token.isalpha() and token.lower() not in stop_words]

    texte_article = " ".join(tokens_article) 
    mots_cles = " ".join(tokens_mots_cles)

    mots_cles_set = set(mots_cles.split(",")) 

    pertinence = 0
    for mot_cle in mots_cles_set:
        if mot_cle in texte_article.lower():
            pertinence += 1

    pertinence = pertinence / len(mots_cles_set) if mots_cles_set else 0

    return pertinence

# Function to display the main table with formatting
def afficher_tableau(data):
    filtered_data = []
    for i, row in enumerate(data):
        texte_article = f"{row[4]} {row[5]}"  # Concaténation du titre et de la rubrique
        pertinence = calculer_pertinence(texte_article, mots_cles)

        try:
            date_publication = datetime.strptime(row[3], "%d/%m/%Y").date()
        except (ValueError, IndexError):
            continue

        if date_debut <= date_publication <= date_fin:
            if not rubriques or any(rubrique in row[5] for rubrique in rubriques):
                if pertinence > 0.5:  # Seuil de pertinence
                    filtered_data.append((i, row))

    if filtered_data:
        st.subheader("Résultats filtrés:")

        for i, (index, row) in enumerate(filtered_data):
            with st.container():
                # Adjust column widths: 1, 2, 1, 1, 4, 4
                cols = st.columns([1, 2, 1, 1, 4, 4])

                # Display the extracted data
                cols[0].markdown(f"**{row[0]}**")  # Fiche
                lien_resume = row[1].split("href='")[1].split("'")[0]
                resume_link = f"[Résumé]({lien_resume})"
                cols[1].markdown(resume_link, unsafe_allow_html=True)
                cols[2].markdown(f"**{row[2]}**")
                cols[3].markdown(f"**{row[3]}**")
                cols[4].markdown(f"**{row[4]}**")
                cols[5].markdown(f"{row[5]}")

    else:
        st.warning("Aucun résultat ne correspond aux filtres.")

# Separate page for RASFF data
def rasff_page():
    st.title("Données RASFF")

    # Filter by specific weeks
    selected_weeks = st.sidebar.multiselect(
        "Sélectionnez les semaines:",
        options=list(range(1, 53)),  # Assuming weeks are from 1 to 52
        default=[1, 52]  # Default to show all weeks
    )

    url = "https://www.alexia-iaa.fr/ac/AC000/somAC001.htm"
    data = extraire_texte_et_liens(url)

    if data:
        # Extract RASFF Excel files
        rasff_articles = [row for row in data if 'Alertes' in row[2]]
        for row in rasff_articles:
            excel_link = row[2].split("href='")[1].split("'")[0]  # Extract Excel link
            try:
                excel_file = requests.get(excel_link)
                excel_file.raise_for_status()

                # Load Excel data
                df = pd.read_excel(excel_file.content, engine='openpyxl')

                # Filter data by selected weeks
                if 'Semaine' in df.columns:
                    df_filtered = df[df['Semaine'].isin(selected_weeks)]
                else:
                    df_filtered = df  # If no week column, display all data

                st.subheader(f"Données RASFF pour {row[3]}")

                # Configure AgGrid
                gb = GridOptionsBuilder.from_dataframe(df_filtered)
                gb.configure_pagination(paginationAutoPageSize=True)
                gb.configure_side_bar()  # Add sidebar with filter options
                gb.configure_default_column(editable=True, groupable=True, sortable=True, filter=True)
                gridOptions = gb.build()

                # Display interactive table
                AgGrid(df_filtered, gridOptions=gridOptions, enable_enterprise_modules=True)

            except requests.exceptions.RequestException as e:
                st.error(f"Erreur lors du téléchargement du fichier Excel: {e}")
    else:
        st.error("Impossible d'extraire le tableau du bulletin.")

# Main page button to display extracted data
if st.button("Editer"):
    url = "https://www.alexia-iaa.fr/ac/AC000/somAC001.htm"
    data = extraire_texte_et_liens(url)

    if data:
        afficher_tableau(data)
    else:
        st.error("Impossible d'extraire le tableau du bulletin.")

# Sidebar button to display RASFF data page
if st.sidebar.button("Afficher les données RASFF"):
    rasff_page()
