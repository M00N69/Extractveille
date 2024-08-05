import streamlit as st
import requests
from bs4 import BeautifulSoup

def extraire_texte_et_liens(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    texte = ""
    liens = []

    for element in soup.find_all(True):
        if element.name == 'a':
            liens.append((element.text.strip(), element['href']))  # Ajoute le texte et le lien
        else:
            texte += element.text.strip()

    return texte, liens

# Page Streamlit
st.title("IA-Reader")
st.write("Extraction du texte et des liens du bulletin Alexia")

if st.button("Extraire"):
    url = "https://www.alexia-iaa.fr/ac/AC000/somAC001.htm"
    texte, liens = extraire_texte_et_liens(url)

    st.subheader("Texte du bulletin:")
    st.write(texte)

    st.subheader("Liens extraits:")
    for texte_lien, lien in liens:
        st.write(f"[{texte_lien}]({lien})")
