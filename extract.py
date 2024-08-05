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
            if len(cols) >= 7:
                row_data = [col.text.strip() for col in cols]
                for i, col in enumerate(cols):
                    if col.find('a'):
                        row_data[i] = f"<a href='{col.find('a')['href']}'>{col.text.strip()}</a>"
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

        # Ajouter cette ligne au début de la section st.markdown pour le tableau
        st.markdown("<div style='width: 100%; overflow-x: auto;'>", unsafe_allow_html=True)

        # Créer le tableau HTML avec les données extraites
        st.markdown(
            f"""
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
            """,
            unsafe_allow_html=True
        )

        # Ajouter cette ligne à la fin de la section st.markdown pour le tableau
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.error("Impossible d'extraire le tableau du bulletin.")
