import streamlit as st
from bs4 import BeautifulSoup
import requests
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Fonction pour extraire les articles du site web
def extraire_articles(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    articles = []
    for article in soup.find_all('tr'):
        try:
            # Trouver le lien dans le <td> précédent le <td> avec le titre
            lien_td = article.find('td', class_='lien')
            if lien_td:
                lien = lien_td.find('a')['href']
                titre = lien_td.find('a').text.strip()
            else:
                lien = None
                titre = None

            resume = article.find('td', class_='resume').text.strip()
            date_publication = article.find('td', class_='date').text.strip()
            rubrique = article.find('td', class_='rubrique').text.strip()

            # Ajouter des informations supplémentaires si disponibles
            publication_td = article.find('td', class_='publication')
            publication = publication_td.text.strip() if publication_td else None
            
            articles.append({
                'titre': titre,
                'resume': resume,
                'date_publication': date_publication,
                'rubrique': rubrique,
                'lien': lien,
                'publication': publication
            })
        except AttributeError:
            pass  # Ignore les lignes qui manquent d'informations
    return articles

# Fonction pour prétraiter le texte (non utilisée pour le moment)
# def pre_traiter_texte(texte):
#     tokens = nltk.word_tokenize(texte)
#     tokens = [token.lower() for token in tokens if token.isalpha()]
#     tokens = [nltk.stem.WordNetLemmatizer().lemmatize(token) for token in tokens]
#     return ' '.join(tokens)

# Fonction pour calculer la pertinence (non utilisée pour le moment)
# def calculer_pertinence(texte_article, texte_entree):
#     vectorizer = TfidfVectorizer()
#     tfidf_matrix = vectorizer.fit_transform([texte_article, texte_entree])
#     similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
#     return similarity[0][0]

# Page Streamlit
st.title("IA-Reader")
st.write("Recherche d'articles pertinents")

# mots_cles = st.text_input("Entrez vos mots-clés (séparés par des virgules):")

if st.button("Extraire les articles"):
    articles = extraire_articles("https://www.alexia-iaa.fr/ac/AC000/somAC001.htm")

    st.subheader("Articles extraits:")
    for article in articles:
        if article['lien']:
            st.write(f"**Titre:** {article['titre']}")
            st.write(f"**Résumé:** {article['resume']}")
            st.write(f"**Date de publication:** {article['date_publication']}")
            st.write(f"**Rubrique:** {article['rubrique']}")
            st.write(f"**Publication:** {article['publication']}")
            st.write(f"[Lire l'article complet]({article['lien']})")
            st.write("---")  # Séparateur entre les articles
