"""Appels à l'API Docker Engine : toutes les URL Docker du projet sont dans ce fichier."""  # Rôle du module

import os                                                 # Lecture des variables d'environnement
import json                                               # Encodage du filtre de labels envoyé à Docker
import requests                                           # Appels HTTP vers l'API Docker
from fastapi import HTTPException                         # Erreurs HTTP propres renvoyées au client de l'API

DOCKER = os.environ.get("DOCKER_API_URL", "http://127.0.0.1:2375")  # Adresse de l'API Docker, lue dans l'environnement
TIMEOUT = 10                                              # Délai maximum par défaut d'un appel à Docker, en secondes
LABEL = "adminapi.managed"                                # Label qui désigne les conteneurs gérés par l'API

session = requests.Session()                              # Connexion réutilisée pour tous les appels à Docker


def appeler(methode, chemin, **options):                  # Point de passage unique de tous les appels à Docker
    options.setdefault("timeout", TIMEOUT)                # Timeout par défaut si l'appelant n'en précise pas
    try:                                                  # Appel protégé contre les pannes réseau
        reponse = session.request(methode, f"{DOCKER}{chemin}", **options)  # Requête HTTP vers Docker
    except (requests.ConnectionError, requests.Timeout):  # Docker injoignable ou trop lent
        raise HTTPException(status_code=502, detail="API Docker injoignable")  # 502 : c'est l'amont qui a échoué
    if reponse.status_code >= 500:                        # Docker a répondu, mais avec une erreur interne
        raise HTTPException(status_code=502, detail=f"API Docker en erreur ({reponse.status_code})")  # 502 également
    return reponse                                        # Réponse brute, analysée par la fonction appelante


def depuis_liste(c):                                      # Conversion d'un conteneur de la LISTE Docker au format du contrat
    return {                                              # Dictionnaire au format du contrat
        "id": c["Id"],                                    # Identifiant complet de 64 caractères
        "name": c["Names"][0].lstrip("/"),                # Premier nom, sans le "/" ajouté par Docker
        "image": c["Image"],                              # Image du conteneur
        "state": c["State"],                              # État ; dans la liste, c'est directement une chaîne
    }


def depuis_detail(d):                                     # Conversion d'un conteneur du DÉTAIL Docker au format du contrat
    return {                                              # Dictionnaire au format du contrat
        "id": d["Id"],                                    # Identifiant complet de 64 caractères
        "name": d["Name"].lstrip("/"),                    # Dans le détail, le nom est "Name"
        "image": d["Config"]["Image"],                    # Image déclarée à la création du conteneur
        "state": d["State"]["Status"],                    # Dans le détail, l'état est un objet : on prend "Status"
    }


def lister():                                             # Liste des conteneurs gérés, au format du contrat
    filtre = json.dumps({"label": [f"{LABEL}=true"]})     # Filtre Docker encodé en JSON : seulement les conteneurs étiquetés
    r = appeler("GET", "/containers/json",                # Requête de la liste des conteneurs
                params={"all": "true", "filters": filtre})  # all=true : y compris arrêtés ; filters : par label
    r.raise_for_status()                                  # Lève une erreur pour un code 4xx inattendu
    return [depuis_liste(c) for c in r.json()]            # Chaque conteneur converti au format du contrat


def lire(ident):                                          # Détail d'un conteneur géré ; 404 s'il est inconnu ou non géré
    r = appeler("GET", f"/containers/{ident}/json")       # Requête du détail du conteneur
    if r.status_code == 404:                              # Docker ne connaît pas ce conteneur
        raise HTTPException(status_code=404, detail="Conteneur inconnu")  # 404 propre
    r.raise_for_status()                                  # Lève une erreur pour un autre code 4xx inattendu
    d = r.json()                                          # Le détail devient un dictionnaire Python
    labels = d["Config"].get("Labels") or {}              # Labels du conteneur ; "or {}" remplace None par un dictionnaire vide
    if labels.get(LABEL) != "true":                       # Conteneur sans le label adminapi.managed=true
        raise HTTPException(status_code=404, detail="Conteneur inconnu")  # Même 404 : l'API ne révèle pas son existence
    return depuis_detail(d)                               # Conteneur au format du contrat


