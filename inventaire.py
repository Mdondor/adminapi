#!/usr/bin/env python3


# ============== TP2 : inventaire des conteneurs Docker + relevé NetBox ======================

# ===================== ÉTAPE A : lister les conteneurs =====================

# A1. Imports
import os                                                 # Accès aux variables d'environnement
import sys                                                # Sortie du script avec un message et un code d'erreur
import json                                               # Écriture du fichier inventaire.json
from datetime import datetime                             # Date et heure du relevé
import requests                                           # Appels HTTP vers les API

# A2. Configuration Docker
DOCKER = os.environ.get("DOCKER_API_URL", "http://127.0.0.1:2375")  # Adresse de l'API Docker, avec une valeur par défaut
TIMEOUT = 10                                              # Délai maximum d'attente d'une réponse, en secondes

# D1. Configuration NetBox
NETBOX = os.environ.get("NETBOX_URL", "http://127.0.0.1:8080")      # Adresse de NetBox, avec une valeur par défaut
try:                                                      # Lecture du token NetBox
    JETON = os.environ["NETBOX_TOKEN"]                    # Token lu sans valeur par défaut : c'est un secret
except KeyError:                                          # Cas où la variable n'est pas définie dans le terminal
    sys.exit("NETBOX_TOKEN absent : chargez le .env avec 'set -a; source .env; set +a'")  # Message clair, code de retour 1

# A3. Session Docker
docker = requests.Session()                               # Connexion réutilisée pour tous les appels à l'API Docker

# D2. Session NetBox
netbox = requests.Session()                               # Connexion réutilisée pour tous les appels à NetBox
netbox.headers.update({                                   # En-têtes envoyés automatiquement à chaque requête NetBox
    "Authorization": f"Bearer {JETON}",                   # Authentification par token
    "Accept": "application/json",                         # Réponses demandées au format JSON
})

# E1. Appel à la liste Docker protégé par try/except
try:                                                      # Début du bloc surveillé
    # A4. GET /containers/json
    r = docker.get(f"{DOCKER}/containers/json",           # Requête qui liste les conteneurs
                   params={"all": "true"},                # Inclut les conteneurs arrêtés
                   timeout=TIMEOUT)                       # Abandon si aucune réponse dans le délai
    # A5. Vérification du code de statut
    r.raise_for_status()                                  # Lève HTTPError si le code est 4xx ou 5xx
    # A6. Conversion en liste Python
    conteneurs = r.json()                                 # Le JSON devient une liste de dictionnaires, un par conteneur
except requests.ConnectionError:                          # E2. API injoignable (service arrêté, mauvaise adresse)
    sys.exit(f"API Docker injoignable sur {DOCKER} : est-elle démarrée ? L'adresse est-elle bonne ?")  # Message clair, code 1
except requests.Timeout:                                  # E3. API trop lente à répondre
    sys.exit(f"Aucune réponse de l'API Docker en {TIMEOUT} s : service surchargé ou réseau coupé.")    # Message clair, code 1
except requests.HTTPError as erreur:                      # E4. API qui répond avec un code d'erreur
    sys.exit(f"L'API Docker a refusé : {erreur.response.status_code} {erreur.response.text[:200]}")    # Code reçu et début du message

