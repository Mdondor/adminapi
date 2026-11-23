"""Authentification de l'API : deux tokens, deux rôles (lecteur et admin)."""  # Rôle du module

import os                                                 # Lecture des variables d'environnement
import secrets                                            # compare_digest : comparaison en temps constant
from fastapi import Depends, HTTPException                # Depends : dépendance exécutée avant la route ; HTTPException : erreur HTTP
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer  # Lecture du header "Authorization: Bearer ..."

API_TOKEN_ADMIN = os.environ["API_TOKEN_ADMIN"]           # Token admin, sans valeur par défaut : l'API refuse de démarrer sans lui
API_TOKEN_READER = os.environ["API_TOKEN_READER"]         # Token lecteur, sans valeur par défaut non plus

bearer = HTTPBearer(auto_error=False)                     # Lit le token ; auto_error=False : c'est nous qui choisissons le code d'erreur


def role_de(token: HTTPAuthorizationCredentials | None) -> str:  # Renvoie le rôle associé au token reçu
    if token is not None:                                 # Un header Authorization: Bearer a bien été envoyé
        recu = token.credentials.encode()                 # Token reçu, converti en octets pour la comparaison
        if secrets.compare_digest(recu, API_TOKEN_ADMIN.encode()):   # Comparaison en temps constant avec le token admin
            return "admin"                                # Le client est l'administrateur
        if secrets.compare_digest(recu, API_TOKEN_READER.encode()):  # Comparaison en temps constant avec le token lecteur
            return "lecteur"                              # Le client est un lecteur
    raise HTTPException(status_code=401,                  # Token absent ou inconnu : on ne sait pas qui parle
                        detail="Token absent ou inconnu", # Message renvoyé au client
                        headers={"WWW-Authenticate": "Bearer"})  # Indique au client le mode d'authentification attendu


def exiger_lecture(token=Depends(bearer)) -> str:         # Dépendance des routes de lecture
    return role_de(token)                                 # Admin ou lecteur acceptés ; sinon 401


def exiger_admin(token=Depends(bearer)) -> str:           # Dépendance des routes d'écriture
    role = role_de(token)                                 # D'abord authentifier : 401 si on ne sait pas qui parle
    if role != "admin":                                   # Ensuite autoriser : seul l'admin peut écrire
        raise HTTPException(status_code=403, detail="Action réservée au rôle admin")  # On sait qui parle, il n'a pas le droit
    return role                                           # Rôle renvoyé à la route
