import streamlit as st
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
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

# Function to generate summaries with Gemini
def generer_resume(texte, lien_resume):
    gemini_api_key = st.secrets["GEMINI_API_KEY"]

    # Configure the Gemini API
    genai.configure(api_key=gemini_api_key)

    # Define the generation parameters
    generation_config = {
        "temperature": 2,
        "top_p": 0.4,
        "top_k": 32,
        "max_output_tokens": 8192,
    }

    # Define the safety settings
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]

    # Define the system instructions
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

    # Generate the summary using Gemini
    response = model.generate_text(text=texte)
    return response.text

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

# Function to display the main table with formatting and analyze button
def afficher_tableau(data):
    # Filter the table by keywords, date, and category
    filtered_data = []
    for i, row in enumerate(data[1:]):  # Ignore header
        texte_article = f"{row[4]} {row[5]}"  # Concatenate Title and Category
        pertinence = calculer_pertinence(texte_article, mots_cles)

        try:
            date_publication = datetime.strptime(row[3], "%d/%m/%Y").date()
        except ValueError:
            continue

        if date_debut <= date_publication <= date_fin:
            if not rubriques or any(rubrique in row[5] for rubrique in rubriques):
                if pertinence > 0.5:  # Relevance threshold
                    filtered_data.append((i, row))

    if filtered_data:
        st.subheader("Résultats filtrés:")

        for i, row in filtered_data:
            with st.container():
                cols = st.columns([2, 6, 2, 2, 1])
                cols[0].markdown(f"**{row[0]}**")  # Fiche
                cols[1].markdown(f"**{row[4]}**")  # Titre
                cols[2].markdown(f"**{row[3]}**")  # Date
                cols[3].markdown(f"**{row[5]}**")  # Rubrique et profil
                analyze_button = cols[4].button("Analyser", key=f"analyze_{i}")

                if analyze_button:
                    # Trigger summary generation
                    lien_resume = row[1].split("href='")[1].split("'")[0]  # Extract "Résumé" link
                    summary = generer_resume(f"{row[4]} {row[5]}", lien_resume)
                    st.expander(f"Résumé pour {row[4]}").write(summary)

    else:
        st.warning("Aucun résultat ne correspond aux filtres.")

# Separate page for RASFF data
def rasff_page():
    st.title("Données RASFF")

    # Filter by week using multiselect
    semaines_disponibles = list(range(1, 53))  # Example list of weeks, 1 to 52
    semaines_selectionnees = st.sidebar.multiselect(
        "Sélectionnez les semaines:",
        options=semaines_disponibles,
        default=semaines_disponibles  # Select all weeks by default
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
                    df_filtered = df[df['Semaine'].isin(semaines_selectionnees)]
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

# Sidebar filters and buttons
st.sidebar.title("Filtres")

mots_cles = st.sidebar.text_input("Entrez vos mots-clés (séparés par des virgules):")

# Filter by date with default values
current_year = datetime.now().year
default_start_date = datetime(current_year, 1, 1)
default_end_date = datetime.now()

date_debut = st.sidebar.date_input("Date de début:", default_start_date)
date_fin = st.sidebar.date_input("Date de fin:", default_end_date)

rubriques = st.sidebar.multiselect("Choisissez les rubriques:", [
    "Alertes alimentaires", "Contaminants", "Signes de qualité", "OGM", 
    "Alimentation animale", "Produits de la pêche", "Produits phytopharmaceutiques", 
    "Biocides", "Fertilisants", "Hygiène", "Vins", "Fruits, légumes et végétaux", 
    "Animaux et viandes", "Substances nutritionnelles", "Nouveaux aliments"
])

if st.sidebar.button("Réinitialiser les filtres"):
    st.experimental_rerun()

if st.button("Editer"):
    url = "https://www.alexia-iaa.fr/ac/AC000/somAC001.htm"
    data = extraire_texte_et_liens(url)

    if data:
        afficher_tableau(data)
    else:
        st.error("Impossible d'extraire le tableau du bulletin.")

if st.sidebar.button("Afficher les données RASFF"):
    rasff_page()
