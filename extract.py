import streamlit as st
from bs4 import BeautifulSoup
import requests
import nltk
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Fonction pour extraire le HTML complet
def extraire_html_complet(url):
    options = Options()
    options.add_argument('--headless=new')  # Exécuter en mode headless
    driver = webdriver.Chrome(ChromeDriverManager(options=options).install()) 
    driver.get(url)

    # Attendre que le contenu soit chargé 
    driver.implicitly_wait(10) 

    html_complet = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html_complet, 'html.parser')
    return soup

# Fonction pour extraire les articles du site web
def extraire_articles(html_complet):
    soup = BeautifulSoup(html_complet, 'html.parser')
    articles = []
    for article in soup.find_all('tr'):
        try:
            fiche_td = article.find('td', class_='fiche')
            if fiche_td:
                lien_td = fiche_td.find('td', class_='lien')
                if lien_td:
                    lien = lien_td.find('a')['href']
                    titre = lien_td.find('a').text.strip()
                else:
                    lien = None
                    titre = None

                resume = fiche_td.find('td', class_='resume').text.strip()
                date_publication = fiche_td.find('td', class_='date').text.strip()
                rubrique = fiche_td.find('td', class_='rubrique').text.strip()

                # Extraire la publication par position
                publication_tds = fiche_td.find_all('td')
                publication = publication_tds[2].text.strip() if len(publication_tds) > 2 else None
                
                # Afficher des messages de débogage (à supprimer une fois que le code fonctionne)
                st.write(f"Lien: {lien}")
                st.write(f"Titre: {titre}")
                st.write(f"Résumé: {resume}")
                st.write(f"Date de publication: {date_publication}")
                st.write(f"Rubrique: {rubrique}")
                st.write(f"Publication: {publication}")
                st.write("---")

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
    # Obtenir le code HTML complet (utilisez Selenium ou un autre outil)
    html_complet = extraire_html_complet("https://www.alexia-iaa.fr/ac/AC000/somAC001.htm")

    # Extraire les articles en utilisant le HTML complet
    articles = extraire_articles(html_complet)

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
