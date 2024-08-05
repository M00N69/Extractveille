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
    for article in soup.find_all('tr'): # Correct: Trouver les lignes du tableau 
        try:
            # Trouver le lien dans le <td> précédent le <td> avec le titre
            lien_td = article.find_previous('td', class_='lien') 
            if lien_td:
                lien = lien_td.find('a')['href']
                titre = lien_td.find('a').text.strip()
            else:
                lien = None
                titre = None
            
            resume = article.find('td', class_='resume').text.strip() # Correct: Sélectionner le résumé
            date_publication = article.find('td', class_='date').text.strip() # Correct: Sélectionner la date
            rubrique = article.find('td', class_='rubrique').text.strip() # Correct: Sélectionner la rubrique
            
            articles.append({
                'titre': titre,
                'resume': resume,
                'date_publication': date_publication,
                'rubrique': rubrique,
                'lien': lien
            })
        except AttributeError:
            pass  # Ignore les lignes qui manquent d'informations
    return articles

# Fonction pour prétraiter le texte
def pre_traiter_texte(texte):
    tokens = nltk.word_tokenize(texte)
    tokens = [token.lower() for token in tokens if token.isalpha()]
    tokens = [nltk.stem.WordNetLemmatizer().lemmatize(token) for token in tokens]
    return ' '.join(tokens)

# Fonction pour calculer la pertinence
def calculer_pertinence(texte_article, texte_entree):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([texte_article, texte_entree])
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
    return similarity[0][0]

# Page Streamlit
st.title("IA-Reader")
st.write("Recherche d'articles pertinents")

mots_cles = st.text_input("Entrez vos mots-clés (séparés par des virgules):")

if st.button("Rechercher"):
    articles = extraire_articles("https://www.alexia-iaa.fr/ac/AC000/somAC001.htm")
    resultats = []
    for article in articles:
        if article['lien']: # Vérifier si le lien est présent
            texte_traite = pre_traiter_texte(article['resume'])
            pertinence = calculer_pertinence(texte_traite, mots_cles.lower())
            resultats.append({
                'titre': article['titre'],
                'resume': article['resume'],
                'date_publication': article['date_publication'],
                'rubrique': article['rubrique'],
                'lien': article['lien'],
                'pertinence': pertinence
            })

    resultats.sort(key=lambda x: x['pertinence'], reverse=True)

    st.subheader("Résultats de la recherche:")
    for resultat in resultats:
        st.write(f"**{resultat['titre']}**")
        st.write(f"**Résumé:** {resultat['resume']}")
        st.write(f"**Date de publication:** {resultat['date_publication']}")
        st.write(f"**Rubrique:** {resultat['rubrique']}")
        st.write(f"[Lire l'article complet]({resultat['lien']})")
