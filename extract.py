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

# URL du GIF pour l'arrière-plan
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

/* Style the analyze buttons */
.analyze-button {{
    padding: 4px 8px;
    color: #fff;
    background-color: #3080F8;
    border: none;
    cursor: pointer;
    text-align: center;
}}

.analyze-button:hover {{
    background-color: #1A5BB1;
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
if 'show_summary' not in st.session_state:
    st.session_state.show_summary = False

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

        # Display the table
        filtered_table_html = '<div class="table-container"><table>'
        filtered_table_html += '<thead><tr><th>' + '</th><th>'.join(data[0]) + '</th><th>Action</th></tr></thead>'
        filtered_table_html += '<tbody>'
        
        for i, row in filtered_data:
            with st.container():
                cols = st.columns(len(row) + 1)  # Create columns
                for j, cell in enumerate(row):
                    cols[j].markdown(cell, unsafe_allow_html=True)
                if cols[-1].button("Analyser", key=f"analyze_button_{i}"):
                    st.session_state.selected_row = i
                    st.session_state.show_summary = True
                    st.experimental_rerun()
        
        st.markdown(filtered_table_html, unsafe_allow_html=True)

        # Generate summaries with Gemini if a row is selected
        if st.session_state.show_summary and st.session_state.selected_row is not None:
            selected_row_data = filtered_data[st.session_state.selected_row][1]
            st.subheader(f"Analyse de l'article sélectionné: {selected_row_data[4]}")
            lien_resume = selected_row_data[1].split("href='")[1].split("'")[0]
            with st.spinner('Analyse en cours...'):
                try:
                    resume = generer_resume(f"{selected_row_data[4]} {selected_row_data[5]}", lien_resume)
                    st.markdown(f"**Résumé de {selected_row_data[4]}:**\n {resume}")
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse : {e}")
            st.write("---")
            if st.button("Fermer l'analyse"):
                st.session_state.show_summary = False
                st.experimental_rerun()

# Separate page for RASFF data
def rasff_page():
    st.title("Données RASFF")

    # Filter by week range
    semaine_debut, semaine_fin = st.sidebar.slider(
        "Sélectionnez une plage de semaines:",
        min_value=1,
        max_value=52,
        value=(1, 52)  # Default values
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

                # Filter data by week
                if 'Semaine' in df.columns:
                    df_filtered = df[(df['Semaine'] >= semaine_debut) & (df['Semaine'] <= semaine_fin)]
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

# Main application flow
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
