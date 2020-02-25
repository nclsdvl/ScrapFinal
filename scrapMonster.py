# -*- coding: utf-8 -*-
"""
Created on Fri Feb 14 06:44:31 2020

@author: MonOrdiPro
"""

import requests
from bs4 import BeautifulSoup

URL = 'https://www.monster.fr/emploi/recherche/?q=data&cy=fr&stpage=1&page=10'
page = requests.get(URL)
#parsage du html
soup = BeautifulSoup(page.content, 'html.parser')
#je recupere l'objet conteneur de tous les resultats
results = soup.find(id="SearchResults")


#tableau des elements contenant chacun un resultat
job_elems = results.find_all('section', class_='card-content')

mes_jobs = []
rejets = []
count_erreur = 0

for job_elem in job_elems :
    #retire les icones type accesibilité de nos resultats
    try:
        job_elem.ul.decompose()
    except:
        print("pas de ul")

    title_elem = job_elem.find('h2', class_='title')
    company_elem = job_elem.find('div', class_='company')
    location_elem = job_elem.find('div', class_='location')

    # si une des trois infos principales manque : on passe
    if None in (title_elem, company_elem, location_elem):
        count_erreur += 1
        rejets.append([title_elem, company_elem, location_elem])
        continue

    print("*********************************************************************")
    print(title_elem.text.strip())
    print(company_elem.text.strip())
    print(location_elem.text.strip())
    
    mes_jobs.append([title_elem.text.strip(), company_elem.text.strip(), location_elem.text.strip()])

    
print("\nnombre de rejets = ", count_erreur)
print("\nnombre d'offre = ", len(mes_jobs))