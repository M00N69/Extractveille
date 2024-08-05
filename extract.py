import streamlit as st
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords

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

# Filtre par mots-clés
mots_cles = st.sidebar.text_input("Entrez vos mots-clés (séparés par des virgules):")

# Fonction pour calculer la pertinence des articles
def calculer_pertinence(texte_article, mots_cles):
    # Prétraitement du texte (suppression des stopwords et lemmatisation)
    stop_words = set(stopwords.words('french'))
    lemmatizer = nltk.stem.WordNetLemmatizer()
    tokens_article = nltk.word_tokenize(texte_article)
    tokens_article = [lemmatizer.lemmatize(token.lower()) for token in tokens_article if token.isalpha() and token.lower() not in stop_words]

    tokens_mots_cles = nltk.word_tokenize(mots_cles)
    tokens_mots_cles = [lemmatizer.lemmatize(token.lower()) for token in tokens_mots_cles if token.isalpha() and token.lower() not in stop_words]

    # Convertir les tokens en chaînes de caractères
    texte_article = " ".join(tokens_article) 
    mots_cles = " ".join(tokens_mots_cles)

    # Utiliser un ensemble de mots-clés pour une meilleure correspondance
    mots_cles_set = set(mots_cles.split(","))  # Corrigé : Splittez la chaîne de mots-clés

    # Vérifier la présence de chaque mot-clé dans l'article
    pertinence = 0
    for mot_cle in mots_cles_set:
        if mot_cle in texte_article.lower():
            pertinence += 1

    # Normaliser la pertinence
    pertinence = pertinence / len(mots_cles_set)

    return pertinence

if st.button("Editer"):
    url = "https://www.alexia-iaa.fr/ac/AC000/somAC001.htm"
    data = extraire_texte_et_liens(url)

    if data:
        if mots_cles:
            filtered_data = []
            for row in data[1:]:  # Ignorer l'en-tête
                # Vérifier si les mots-clés sont présents dans l'article
                texte_article = f"{row[4]} {row[5]}"  # Concaténer Titre et Rubrique
                pertinence = calculer_pertinence(texte_article, mots_cles)

                if pertinence > 0.5:  # Seuil de pertinence
                    filtered_data.append(row)

            st.subheader("Résultats filtrés:")

            # Définir les styles CSS pour le tableau
            st.markdown(
                """
                <style>
                table {
                    border-collapse: collapse;
                    width: 100%;
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
                <div style="overflow-x: auto;">
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
            st.subheader("Tableau extrait:")

            # Définir les styles CSS pour le tableau
            st.markdown(
                """
                <style>
                table {
                    border-collapse: collapse;
                    width: 100%;
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
                <div style="overflow-x: auto;">
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

    else:
        st.error("Impossible d'extraire le tableau du bulletin.")
