# -*- coding: utf-8 -*-
"""
Created on Sat Feb 15 06:36:49 2020

@author: MonOrdiPro
"""

import requests
from bs4 import BeautifulSoup
from firebase import firebase
import time
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
firebase = firebase.FirebaseApplication("https://salaire-data.firebaseio.com/", None)



"""
------------------------------------------------------------------------------------------------------------------------------
---------------------------------------------SCRAPPING SECTION----------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------------
"""



def scrap_indeed():
    rejets = []
    mes_offres=[]
    deja_dans_la_liste=[]
    #il faut faire varier le parametre de la requete pour recuperer toutes les pages
    for elt in range (0, 20):
        #delai d'attente min entre deux requetes (certains sites n'apprecie pas d'etre scrapé)
        time.sleep(1)
        URL = 'https://www.indeed.fr/emplois?q=data+analyst&l=&radius=1&limit=50&start={}'.format(elt*50)
        page = requests.get(URL)
        
        #parsage du html
        soup = BeautifulSoup(page.content, 'html.parser')
        
        #je recupere l'objet conteneur de tous les resultats
        results = soup.find(id="resultsCol")
        
        #tableau des elements contenant chacun un resultat
        job_elems = results.find_all('div', class_="jobsearch-SerpJobCard")
        
    
        
        for job_elem in job_elems :
            #recuperation (poste, entreprise, ville)
            title_elem = job_elem.find('a', class_='jobtitle turnstileLink')
            company_elem = job_elem.find('span', class_='company')
            location_elem = job_elem.find('span', class_='location accessible-contrast-color-location')
            
            #le site à l'air mal codé: parfois la ville est dans un span parfois dans une div...
            if location_elem == None :
                location_elem = job_elem.find('div', class_='location accessible-contrast-color-location')
            # si une des trois infos principales manque : on passe
            if None in (title_elem, company_elem, location_elem):
                rejets.append([title_elem, company_elem, location_elem])
                continue
            #le salaire est rarement present et mal formaté...
            salary_elem = job_elem.find('span', class_='salaryText')
            if salary_elem != None:
                mon_element = [title_elem.text.strip(), company_elem.text.strip(), location_elem.text.strip(), salary_elem.text.strip()]
            else:
                mon_element = [title_elem.text.strip(), company_elem.text.strip(), location_elem.text.strip(), ""]
    
    
            if mon_element not in mes_offres:
                mes_offres.append(mon_element)
            else:
               deja_dans_la_liste.append(mon_element)
            
            
    print(len(mes_offres))
    return [mes_offres, deja_dans_la_liste, rejets]

"""
------------------------------------------------------------------------------------------------------------------------------
---------------------------------------------DATABASE SECTION-----------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------------
"""


# enregistrement en bdd :


def save_bdd(liste_offre_sans_doublon):
    for job in liste_offre_sans_doublon:
        data = {
                'Poste' : job[0],
                'Entreprise' : job[1],
                'Ville' : job[2],
                'Salaire' : job[3]
                }
        firebase.post('/salaire-data/job', data)



#recuperation des données depuis la bdd



def recup_bdd():   
    print('in')
    results = firebase.get("/salaire-data/job", '')
    print('results retrieve')
    jobs_in_bdd = []
    tab_id = []
    for key in results :
        temp_tab = []
        
        tab_id.append(key)
        temp_tab.append(results[key]['Poste'])
        temp_tab.append(results[key]['Entreprise'])
        temp_tab.append(results[key]['Ville'])
        temp_tab.append(results[key]['Salaire'])
        
        jobs_in_bdd.append(temp_tab)
        
    return(jobs_in_bdd, tab_id)

 


"""
------------------------------------------------------------------------------------------------------------------------------
---------------------------------------------PREPARATION DES DONNEES----------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------------
"""

def clean_doublon_scrapVSbdd(liste_offre_scrappe, liste_offre_bdd) :       
    count = 0
    liste_offre_sans_doublon = []
    for elem in liste_offre_scrappe: 
        if elem not in liste_offre_bdd:
            liste_offre_sans_doublon.append(elem)
            count +=1
    print("nbr offre à ajouter : " + str(count))
    return liste_offre_sans_doublon

def recuperation_job_avec_salaire (liste_job_bdd) :
    jobs_avec_salaire = []
    for job in liste_job_bdd :
        if job[3] != "" :
            jobs_avec_salaire.append(job)
    return jobs_avec_salaire  


def nettoyage_bdd (mes_job_bdd, tab_id):
    count = 0
    
    for i in range (len(mes_job_bdd)-1) :
        if mes_job_bdd[i] in mes_job_bdd[i+1 : len(mes_job_bdd)-1] :
            print(str(count))
            count += 1
            firebase.delete('/salaire-data/job', tab_id[i])
    print('nbr doublon = '+str(count))
            
            
            
         
        
"""


"""

def calculJobSalaire(jobs_avec_salaire) :
    
    nbr_salaire_par_an = 0
    nbr_salaire_par_mois = 0
    resultats_finaux = []
    resultat_parisien = 0
    ma_liste_paris = ["92", "75", "77", "78", "91", "93", "94", "95", "paris"]
    salaire_parisien = 0
    
    for job in jobs_avec_salaire :
        

    
        if 'an' in job[3] :
            offre_en_nbr = [int(s) for s in job[3].split() if s.isdigit()]
            for dept in ma_liste_paris :
                if dept in job[2].lower() :
                    resultat_parisien += 1
                    break
            
            # cas ou ce n'est pas unhe fourchette
            if len(offre_en_nbr) == 2 :
                #print (offre_en_nbr[0]*1000)
                salaire_annuel = offre_en_nbr[0]*1000
                resultats_finaux.append([job[0] , salaire_annuel])
                nbr_salaire_par_an += 1
            # calcul du centre de classe
            elif len(offre_en_nbr) == 4 :
                #print ( int((offre_en_nbr[0] + offre_en_nbr[2]) / 2)*1000)
                salaire_annuel = int((offre_en_nbr[0] + offre_en_nbr[2]) / 2)*1000
                resultats_finaux.append([job[0], salaire_annuel])
                nbr_salaire_par_an += 1
                
        
        # si le salaire est : par mois       
        elif 'mois' in job[3]:
            #print (job["Salaire"])
            offre_en_nbr = [int(s) for s in job[3].split() if s.isdigit()]
            for dept in ma_liste_paris :
                if dept in job[2].lower() :
                    resultat_parisien += 1
                    break
            
            if len(offre_en_nbr) == 1:
                #print(offre_en_nbr[0]*12)
                salaire_annuel = offre_en_nbr[0]*12
                resultats_finaux.append([job[0] , salaire_annuel])
                nbr_salaire_par_mois += 1
                #print('enregistré!')
    
            elif len(offre_en_nbr) == 4 :
                premiere_fourchette = offre_en_nbr[0] * 1000 + offre_en_nbr[1]
                seconde_fourchette = offre_en_nbr[2] * 1000 + offre_en_nbr[3]
                salaire_annuel = int((premiere_fourchette + seconde_fourchette)/2)*12
                
                #print(salaire_annuel)
                resultats_finaux.append([job[0] , salaire_annuel])
                nbr_salaire_par_mois += 1
                #print('enregistré!')
                
            elif len(offre_en_nbr) == 2 and offre_en_nbr[0] < 10:
                #print(offre_en_nbr)
                salaire_annuel = (offre_en_nbr[0] * 1000 + offre_en_nbr[1])*12
                #print(salaire_annuel)
                resultats_finaux.append([job[0] , salaire_annuel])
                nbr_salaire_par_mois += 1
                #print('enregistré!')
                
            elif len(offre_en_nbr) == 2 and offre_en_nbr[0] >10:   
                salaire_annuel = int(((offre_en_nbr[0] + offre_en_nbr[1])/2)*12)
                #print(salaire_annuel)
                resultats_finaux.append([job[0] , salaire_annuel])
                nbr_salaire_par_mois += 1

    return (resultats_finaux, nbr_salaire_par_an, nbr_salaire_par_mois, resultat_parisien)


"""----------------------SCRAP------------------------------"""
"""
#scrap de Indeed
resultats_scrap = scrap_indeed()
mes_job_scrape = resultats_scrap[0]
doublon_scrappe = resultats_scrap[1]
rejets_scrape = resultats_scrap[2]
"""
"""----------------------BDD---------------------------------------------------"""

#cherche resultat en BDD
mes_job_bdd = recup_bdd()[0]
"""
#Compare les offre scrapper aux offres en bdd
mes_jobs_scrape_sans_doublon_en_bdd = clean_doublon_scrapVSbdd(mes_job_scrape, mes_job_bdd)

#Sauvegarde   
save_bdd(mes_jobs_scrape_sans_doublon_en_bdd)

"""
#tableau des id en vue de nettoyage
#tab_id = recup_bdd()[1]

jobs_avec_salaire = recuperation_job_avec_salaire(mes_job_bdd)

#nettoyage_bdd(mes_job_bdd, tab_id)





results_stat = calculJobSalaire(jobs_avec_salaire)
resultats_finaux = results_stat[0]

nbr_salaire_par_an = results_stat[1]
nbr_salaire_par_mois = results_stat[2]
nbr_offre_parisienne = results_stat[3]

print("offre parisienne = "+str(nbr_offre_parisienne))
"""
------------------------------------------------------------------------------------------------------------------------------
---------------------------------------------ANALYSE DES DONNEES--------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------------
"""



nbr_offre = len(mes_job_bdd)        
nbr_offre_avec_salaire = len(jobs_avec_salaire)
nbr_salaire_par_jour = (nbr_offre_avec_salaire - nbr_salaire_par_an - nbr_salaire_par_mois)
pourcentage_offre_salaire = round(nbr_offre_avec_salaire * 100 / nbr_offre ,2)

print("----------------------------------------------------------------------")
print("nombre d'offre : "+ str(nbr_offre))
print("nombre d'offre avac salaire : " + str(nbr_offre_avec_salaire))
print("les offres avec salaire representent : " +str(pourcentage_offre_salaire)+" %")

print("----------------------------------------------------------------------")

pourcentage_salaire_an = round(nbr_salaire_par_an * 100 / nbr_offre_avec_salaire,2)
pourcentage_salaire_mois = round(nbr_salaire_par_mois * 100 / nbr_offre_avec_salaire,2)
pourcentage_salaire_jour = round(100 - (pourcentage_salaire_an + pourcentage_salaire_mois),2)

print("pourcentage des offres avec salaire donné par mois : " + str(int(pourcentage_salaire_mois)) + "% (" +str(nbr_salaire_par_mois) +" offres)")
print("pourcentage des offres avec salaire donné par an : " + str(int(pourcentage_salaire_an)) + "% (" +str(nbr_salaire_par_an) +" offres)")
print("pourcentage des offres avec salaire donné par jour : " + str(int(pourcentage_salaire_jour)) + "% (" +str(nbr_salaire_par_jour) +" offres)")


print("----------------------------------------------------------------------")

somme_salaire = 0
somme_salaire_stagiaire = 0
nbr_salaire_utilise = 0
nbr_salaire_stagiaire = 0
resultats_sans_stagiaire =[]


for elt in resultats_finaux:

    if elt[1] > 18000 :
        somme_salaire += elt[1]
        nbr_salaire_utilise += 1
        resultats_sans_stagiaire.append(elt[1])
        #if elt[1] <21000 :
            #print(elt[0])
    else :
        somme_salaire_stagiaire += elt[1]
        nbr_salaire_stagiaire += 1
        

nbr_salaire_rejete = nbr_offre_avec_salaire - nbr_salaire_utilise
moyenne_salaire = somme_salaire / nbr_salaire_utilise
print("on exclu les salaires journaliers !")
print("nombre d'offre en stage : " +str(nbr_salaire_stagiaire))
print("nombre d'offre en emploi : " +str(nbr_salaire_utilise))
print("salaire annuel moyen des stagiaires : " + str(int(somme_salaire_stagiaire / nbr_salaire_stagiaire)) + " euros")
print("salaire annuel moyen des personnes travaillant dans la data : " + str(int(somme_salaire / nbr_salaire_utilise))+ " euros")
print("----------------------------------------------------------------------")




plt.hist(resultats_sans_stagiaire, range = (15000, 60000), bins = 10, color = 'grey',
            edgecolor = 'red')
plt.xlabel('salaire annuel')
plt.ylabel('nombres d\'occurences')
plt.title('Repartition des salaires dans la data')


plt.figure(figsize = (6, 6))
x = [pourcentage_salaire_an, pourcentage_salaire_mois, pourcentage_salaire_jour]
plt.pie(x, labels = ['Salaire par année', 'Salaire par mois', 'salaire par jour'])
plt.legend()






fig, ax = plt.subplots(figsize=(6, 3), subplot_kw=dict(aspect="equal"))

recipe = ["Offres Parisiennes",
          "Offres Provinciales"]

data = [nbr_offre_parisienne, nbr_offre_avec_salaire - nbr_offre_parisienne]

wedges, texts = ax.pie(data, wedgeprops=dict(width=0.5), startangle=-40)

bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
kw = dict(arrowprops=dict(arrowstyle="-"),
          bbox=bbox_props, zorder=0, va="center")

for i, p in enumerate(wedges):
    ang = (p.theta2 - p.theta1)/2. + p.theta1
    y = np.sin(np.deg2rad(ang))
    x = np.cos(np.deg2rad(ang))
    horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
    connectionstyle = "angle,angleA=0,angleB={}".format(ang)
    kw["arrowprops"].update({"connectionstyle": connectionstyle})
    ax.annotate(recipe[i], xy=(x, y), xytext=(1.35*np.sign(x), 1.4*y),
                horizontalalignment=horizontalalignment, **kw)

ax.legend(wedges, recipe,
          title="repartition géograpgique des offres",
          loc="center left",
          bbox_to_anchor=(1, 0, 0.5, 1))

plt.show()




"""




fig = go.Figure(
        data=[go.Bar(x=resultats_sans_stagiaire)],
        layout_title_text="A Figure Displayed with fig.show()"
        )
fig.show()

"""







       


