import streamlit as st
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import pandas as pd
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder  # Ensure this import is correct

# Ensure NLTK dependencies are downloaded
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')

# Configure Streamlit to use "wide" mode
st.set_page_config(layout="wide")


# URL of the GIF for the background
gif_url = "https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExZzl1djM4anJ3dGQxY3cwYmM2M2VyeDI4cDUyM3ozcmNvNzJjOWg3aiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/26gJzajW8IiyJs3YY/giphy.gif"

# Define the CSS for background and colors
css_background = f"""
<style>
.stApp {{
    background: url("{gif_url}") no-repeat center center fixed;
    background-size: cover;
    color: #F0F0F0;  /* Light text */
}}

/* Apply background color to the entire sidebar */
[data-testid="stSidebar"] > div:first-child {{
    background-color: #037283 !important;  /* Blue-green */
    color: #EDF6F9 !important;  /* Light text */
}}

/* Style the inputs, selections, and buttons in the sidebar */
.stSidebar input, .stSidebar selectbox, .stSidebar button {{
    color: #EDF6F9 !important;  /* Light text */
    background-color: #83c5be !important;  /* Light blue-green for buttons and inputs */
}}

/* Style the global buttons */
button, .stButton > button {{
    color: #fff !important; /* White text */
    background-color: #3080F8 !important; /* Blue background */
}}

button:hover, .stButton > button:hover {{
    background-color: #1A5BB1 !important; /* Darker blue background */
}}

/* Container for the table */
.table-container {{
    display: flex;
    justify-content: center;
    width: 100%;
}}

/* Styles for the table */
table {{
    border-collapse: collapse;
    width: 100%;  /* Ensure the table takes up the full width */
    max-width: 100%;
    border: 1px solid #ddd;
    background-color: #29292F; /* Dark background */
}}

th, td {{
    border: 1px solid #ddd;
    text-align: left;
    padding: 8px;
    color: #F0F0F0;  /* Light text */
    word-wrap: break-word;  /* Allow line breaks within cells */
    white-space: normal;  /* Allow line breaks */
}}

tr:nth-child(even) {{
    background-color: #333; /* Darker background for even rows */
}}

th {{
    background-color: #333; /* Darker background for headers */
    font-weight: bold;
}}

a {{
    color: #00d9d9; /* Light blue for links */
    text-decoration: none; /* Remove default underline */
}}

a:hover {{
    text-decoration: underline; /* Underline on hover */
}}
</style>
"""

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
def extraire_texte_et_liens(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all rows in the table
    rows = soup.find_all('tr')
    
    data = []
    for row in rows:
        columns = row.find_all('td')
        if len(columns) > 0:
            fiche = columns[0].text.strip()
            publication = columns[1].text.strip()
            link_element = row.find('a', href=True)
            if link_element and 'Alertes' in link_element.text:
                excel_link = link_element['href']
                data.append((fiche, publication, excel_link))
    
    return data

def rasff_page():
    st.title("Données RASFF")

    url = "https://www.alexia-iaa.fr/ac/AC000/somAC001.htm"
    data = extraire_texte_et_liens(url)

    if data:
        for row in data:
            excel_link = row[2]
            try:
                excel_file = requests.get(excel_link)
                excel_file.raise_for_status()

                # Load Excel data
                df = pd.read_excel(excel_file.content, engine='openpyxl')

                st.subheader(f"Données RASFF pour {row[1]}")

                # Configure AgGrid
                gb = GridOptionsBuilder.from_dataframe(df)
                gb.configure_pagination(paginationAutoPageSize=True)
                gb.configure_side_bar()  # Add sidebar with filter options
                gb.configure_default_column(editable=True, groupable=True, sortable=True, filter=True)
                gridOptions = gb.build()

                # Display interactive table using AgGrid
                AgGrid(df, gridOptions=gridOptions, enable_enterprise_modules=True)

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
