import streamlit as st
import requests
from bs4 import BeautifulSoup

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
            if len(cols) >= 7:  # Vérifier s'il y a au moins 7 colonnes
                row_data = []
                for col in cols:
                    # Extraire le texte et le lien de chaque colonne
                    text = col.text.strip()
                    if col.find('a'):
                        link = col.find('a')['href']
                        text = f"[{text}]({link})"
                    row_data.append(text)

                # Afficher des messages de débogage (à supprimer une fois que le code fonctionne)
                st.write(f"Ligne: {row_data}")
                
                data.append(row_data)

        return data
    else:
        return None

# Page Streamlit
st.title("IA-Reader")
st.write("Extraction du tableau et des liens du bulletin Alexia")

if st.button("Extraire"):
    url = "https://www.alexia-iaa.fr/ac/AC000/somAC001.htm"
    data = extraire_texte_et_liens(url)

    if data:
        st.subheader("Tableau extrait:")
        st.markdown(
            """
            <style>
            table {
                border-collapse: collapse;
                width: 100%;
            }

            th, td {
                border: 1px solid #ddd;
                text-align: left;
                padding: 8px;
            }

            tr:nth-child(even) {
                background-color: #f2f2f2;
            }

            th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        for i, row in enumerate(data):
            if i == 0:
                st.markdown(f"{' | '.join(row)}", unsafe_allow_html=True)  # Affiche l'en-tête
            else:
                st.markdown(f"{' | '.join(row)}", unsafe_allow_html=True)
    else:
        st.error("Impossible d'extraire le tableau du bulletin.")
