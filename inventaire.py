#!/usr/bin/env python3                                    # Permet de lancer le script directement avec ./inventaire.py
"""TP2 : inventaire des conteneurs Docker + relevé NetBox."""  # Description du script

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

# C1. Liste qui recevra les informations de chaque conteneur
liste = []                                                # Liste vide, remplie dans la boucle

# A7. Parcours des conteneurs
for c in conteneurs:                                      # Un conteneur à chaque tour de boucle
    nom = c["Names"][0].lstrip("/")                       # Nom du conteneur sans le "/" ajouté par Docker
    image = c["Image"]                                    # Image utilisée par le conteneur
    etat = c["State"]                                     # État : running, exited, created...

    # C2. Informations du conteneur rangées dans un dictionnaire
    info = {"nom": nom, "image": image, "etat": etat}     # Nom, image et état

    # ===================== ÉTAPE B : CPU et mémoire =====================

    # B1. Stats uniquement pour un conteneur démarré
    if etat == "running":                                 # Condition : le conteneur tourne
        try:                                              # Appel des stats protégé par try/except
            # B2. GET /containers/{id}/stats
            rs = docker.get(f"{DOCKER}/containers/{c['Id']}/stats",  # Requête des statistiques du conteneur
                            params={"stream": "false"},   # Un seul relevé au lieu d'un flux continu
                            timeout=TIMEOUT)              # Abandon si aucune réponse dans le délai
            rs.raise_for_status()                         # Lève HTTPError si le code est 4xx ou 5xx
        except requests.ConnectionError:                  # API Docker devenue injoignable
            sys.exit(f"API Docker injoignable pendant les stats de {nom}.")  # Message clair, code 1
        except requests.Timeout:                          # Stats trop longues à arriver
            sys.exit(f"Aucune réponse en {TIMEOUT} s pour les stats de {nom}.")  # Message clair, code 1
        except requests.HTTPError as erreur:              # Code d'erreur sur les stats
            sys.exit(f"Stats refusées pour {nom} : {erreur.response.status_code} {erreur.response.text[:200]}")  # Code reçu et message

        stats = rs.json()                                 # Les stats deviennent un dictionnaire Python

        # B3. Pourcentage de CPU
        cpu, avant = stats["cpu_stats"], stats["precpu_stats"]  # Relevé actuel et relevé précédent
        delta_cpu = cpu["cpu_usage"]["total_usage"] - avant["cpu_usage"]["total_usage"]  # CPU consommé par le conteneur entre les deux relevés
        delta_systeme = cpu.get("system_cpu_usage", 0) - avant.get("system_cpu_usage", 0)  # CPU consommé par la machine entre les deux relevés
        pourcent = delta_cpu / delta_systeme * cpu.get("online_cpus", 1) * 100 if delta_systeme else 0.0  # Part du conteneur en %, 0 si division par zéro

        # B4. Mémoire en Mo
        memoire_mo = stats["memory_stats"].get("usage", 0) / 1024 / 1024  # Conversion octets -> Ko -> Mo

        info["cpu_pct"] = round(pourcent, 2)              # % CPU ajouté au dictionnaire, arrondi à 2 décimales
        info["memoire_mo"] = round(memoire_mo, 1)         # Mémoire ajoutée au dictionnaire, arrondie à 1 décimale

        # B5. Affichage d'un conteneur démarré
        print(f"{nom:<30} {image:<35} {etat:<10} CPU {pourcent:6.2f} %  MEM {memoire_mo:8.1f} Mo")  # Colonnes alignées
    else:                                                 # Conteneur non démarré
        print(f"{nom:<30} {image:<35} {etat:<10}")        # Affichage sans CPU ni mémoire

    liste.append(info)                                    # C2. Dictionnaire du conteneur ajouté à la liste

# ===================== ÉTAPE D : relevé NetBox =====================

try:                                                      # Appels NetBox protégés par try/except
    # D3. Version de NetBox
    rn = netbox.get(f"{NETBOX}/api/status/", timeout=TIMEOUT)  # Requête du statut de NetBox
    rn.raise_for_status()                                 # Lève HTTPError si le code est 4xx ou 5xx
    version = rn.json()["netbox-version"]                 # Version de NetBox lue dans la réponse

    # D4. Pagination des types d'objets
    url = f"{NETBOX}/api/core/object-types/?limit=50"     # Adresse de la première page, 50 résultats maximum
    total = 0                                             # Compteur des types d'objets reçus
    count = None                                          # Total annoncé par NetBox
    while url:                                            # Boucle tant qu'une page reste à lire
        rn = netbox.get(url, timeout=TIMEOUT)             # Requête de la page courante
        rn.raise_for_status()                             # Lève HTTPError si le code est 4xx ou 5xx
        page = rn.json()                                  # La page devient un dictionnaire Python
        total += len(page["results"])                     # Nombre de résultats de la page ajouté au compteur
        count = page["count"]                             # Total annoncé par NetBox, présent sur chaque page
        url = page["next"]                                # Adresse de la page suivante, ou None à la dernière page
except requests.ConnectionError:                          # NetBox injoignable
    sys.exit(f"NetBox injoignable sur {NETBOX} : est-elle démarrée ? L'adresse est-elle bonne ?")  # Message clair, code 1
except requests.Timeout:                                  # NetBox trop lente à répondre
    sys.exit(f"Aucune réponse de NetBox en {TIMEOUT} s : service surchargé ou réseau coupé.")    # Message clair, code 1
except requests.HTTPError as erreur:                      # NetBox qui répond avec un code d'erreur (ex. 403 : token invalide)
    sys.exit(f"NetBox a refusé : {erreur.response.status_code} {erreur.response.text[:200]}")    # Code reçu et début du message

# D5. Comparaison avec le champ "count"
coherent = (total == count)                               # True si le compteur est égal au total annoncé par NetBox

# ===================== ÉTAPE C : fichier inventaire.json =====================

# C3. Dictionnaire final avec la date du relevé
inventaire = {                                            # Structure écrite dans le fichier
    "date": datetime.now().isoformat(timespec="seconds"), # Date et heure du relevé, ex. 2026-11-21T23:00:00
    "conteneurs": liste,                                  # Liste des conteneurs
    "netbox": {                                           # D6. Informations NetBox
        "version": version,                               # Version de NetBox
        "types_objets": total,                            # Nombre compté en suivant la pagination
        "count": count,                                   # Nombre annoncé par NetBox
        "coherent": coherent,                             # Résultat de la comparaison
    },
}

# C4. Écriture dans inventaire.json
with open("inventaire.json", "w", encoding="utf-8") as f:  # Fichier ouvert en écriture, refermé automatiquement à la fin du bloc
    json.dump(inventaire, f, indent=2, ensure_ascii=False)  # JSON indenté pour être lisible, accents conservés

# C5. Résumé lisible
demarres = sum(1 for c in liste if c["etat"] == "running")  # Nombre de conteneurs démarrés
print()                                                   # Ligne vide pour aérer l'affichage
print(f"Relevé du {inventaire['date']}")                  # Date du relevé
print(f"{len(liste)} conteneurs, dont {demarres} démarrés")  # Ex. : « 24 conteneurs, dont 7 démarrés »
print(f"NetBox {version} : {total} types d'objets (count = {count}) -> {'OK' if coherent else 'INCOHÉRENT'}")  # D6. Résumé NetBox
print("Résultat écrit dans inventaire.json")              # Confirmation de l'écriture du fichier
