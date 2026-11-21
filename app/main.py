"""adminapi : API d'administration des conteneurs, version en lecture seule."""  # Description du module

# --- Imports
import os                                                 # Lecture des variables d'environnement
import json                                               # Encodage du filtre de labels envoyé à Docker
import requests                                           # Appels HTTP vers l'API Docker
from fastapi import FastAPI, HTTPException                # FastAPI : l'application ; HTTPException : renvoyer une erreur HTTP propre

# --- Configuration
DOCKER = os.environ.get("DOCKER_API_URL", "http://127.0.0.1:2375")  # Adresse de l'API Docker, lue dans l'environnement
TIMEOUT = 10                                              # Délai maximum d'attente d'une réponse de Docker, en secondes
LABEL = "adminapi.managed"                                # Label qui désigne les conteneurs gérés par l'API

# --- Session
docker = requests.Session()                               # Connexion réutilisée pour tous les appels à l'API Docker

# --- Application
app = FastAPI(title="adminapi")                           # Création de l'application ; le titre s'affiche dans /docs


# --- GET /health
@app.get("/health")                                       # Associe la fonction health à la route GET /health
def health():                                             # Fonction exécutée à chaque requête sur /health
    return {"status": "ok"}                               # Dictionnaire converti en JSON par FastAPI, avec le code 200



# --- Conversion d'un conteneur de la LISTE Docker au format du contrat
def depuis_liste(c):                                      # Reçoit un conteneur tel que le renvoie /containers/json
    return {                                              # Renvoie un dictionnaire au format du contrat
        "id": c["Id"],                                    # Identifiant complet de 64 caractères
        "name": c["Names"][0].lstrip("/"),                # Premier nom, sans le "/" ajouté par Docker
        "image": c["Image"],                              # Image du conteneur
        "state": c["State"],                              # État ; dans la liste, c'est directement une chaîne
    }


# --- GET /containers
@app.get("/containers")                                   # Associe la fonction lister à la route GET /containers
def lister():                                             # Fonction exécutée à chaque requête sur /containers
    filtre = json.dumps({"label": [f"{LABEL}=true"]})     # Filtre Docker encodé en JSON : seulement les conteneurs étiquetés
    r = docker.get(f"{DOCKER}/containers/json",           # Requête de la liste des conteneurs
                   params={"all": "true", "filters": filtre},  # all=true : y compris arrêtés ; filters : par label
                   timeout=TIMEOUT)                       # Abandon si aucune réponse dans le délai
    r.raise_for_status()                                  # Lève une erreur si Docker répond 4xx ou 5xx
    return [depuis_liste(c) for c in r.json()]            # Chaque conteneur converti au format du contrat




# --- Conversion d'un conteneur du DÉTAIL Docker au format du contrat
def depuis_detail(d):                                     # Reçoit un conteneur tel que le renvoie /containers/{id}/json
    return {                                              # Renvoie un dictionnaire au format du contrat
        "id": d["Id"],                                    # Identifiant complet de 64 caractères
        "name": d["Name"].lstrip("/"),                    # Dans le détail, le nom est "Name" (et non "Names[0]")
        "image": d["Config"]["Image"],                    # Image déclarée à la création du conteneur
        "state": d["State"]["Status"],                    # Dans le détail, l'état est un objet : on prend son champ "Status"
    }


# --- GET /containers/{id}
@app.get("/containers/{id}")                              # Route avec un paramètre dans le chemin
def detail(id: str):                                      # FastAPI place la valeur de {id} dans la variable id
    r = docker.get(f"{DOCKER}/containers/{id}/json",      # Requête du détail de ce conteneur
                   timeout=TIMEOUT)                       # Abandon si aucune réponse dans le délai
    if r.status_code == 404:                              # Docker ne connaît pas ce conteneur
        raise HTTPException(status_code=404, detail="Conteneur inconnu")  # Erreur 404 propre renvoyée au client
    r.raise_for_status()                                  # Lève une erreur pour tout autre code 4xx ou 5xx
    d = r.json()                                          # Le détail devient un dictionnaire Python
    labels = d["Config"].get("Labels") or {}              # Labels du conteneur ; "or {}" remplace None par un dictionnaire vide
    if labels.get(LABEL) != "true":                       # Conteneur sans le label adminapi.managed=true
        raise HTTPException(status_code=404, detail="Conteneur inconnu")  # Même 404 : l'API ne révèle pas son existence
    return depuis_detail(d)                               # Conteneur au format du contrat
