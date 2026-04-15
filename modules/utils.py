"""
Fonctions utilitaires partagées entre les modules
"""
import hashlib
from flask import session, flash, redirect, url_for
from functools import wraps


def login_required(role=None):
    """Décorateur d'authentification"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user_role = session.get('role')
            email_keys = {
                'admin': 'email_admin',
            }

            if not user_role or not session.get(email_keys.get(user_role)):
                flash("Vous devez être connecté", "warning")
                return redirect(url_for('login'))

            if role:
                # Gère liste ou string
                if isinstance(role, (list, tuple)):
                    if user_role not in role:
                        flash("Accès refusé", "danger")
                        return redirect(url_for('index'))
                else:
                    if user_role != role:
                        flash("Accès refusé", "danger")
                        return redirect(url_for('index'))

            return f(*args, **kwargs)

        return wrapped

    return decorator


def getLogin(session_key, table, mysql):
    """Récupère les informations de connexion"""
    cur = mysql.connection.cursor()

    loggedIn = False
    firstName = ''

    if session_key in session:
        loggedIn = True

        # Limiter les tables autorisées
        allowed_tables = [
            'admin',
            'doctor',
            'patient',
            'secretaire_medicale',
            'ambulancier',
            'caissier',
            'gestionnaire_logistique',
            'gestionnaire_stock',
            'infirmier',
            'interne_medecine'
        ]
        if table not in allowed_tables:
            raise ValueError("Table non autorisée")

        query = f"SELECT nom FROM {table} WHERE {session_key} = %s"
        cur.execute(query, (session[session_key],))
        result = cur.fetchone()
        if result:
            (firstName,) = result

    cur.close()
    return loggedIn, firstName


def is_valid(email, email_field, password, table, mysql):
    """Valide les identifiants de connexion"""
    cur = mysql.connection.cursor()

    # Hasher le mot de passe
    hashed_password = hashlib.md5(password.encode()).hexdigest()

    # Sécuriser les noms de table
    allowed_tables = [
        'admin',
        'doctor',
        'patient',
        'secretaire_medicale',
        'ambulancier',
        'caissier',
        'gestionnaire_logistique',
        'gestionnaire_stock',
        'infirmier',
        'interne_medecine'
    ]
    if table not in allowed_tables:
        return False

    # Utiliser une requête paramétrée
    query = f"SELECT * FROM {table} WHERE {email_field} = %s AND password = %s"
    cur.execute(query, (email, hashed_password))
    result = cur.fetchone()
    cur.close()

    return result is not None


def envoie_email_connection(email, mot_de_passe, nom, prenom, mail):
    """Envoie un email de connexion"""
    from flask_mail import Message
    
    # Envoi de l'e-mail automatique
    msg = Message(
        subject="Bienvenue sur la Clinique Floréal - Gestion Hospitalière",
        recipients=[email],
        body=f"""Bonjour {nom} {prenom},

        Félicitations ! Votre compte sur la Clinique Floréal, notre application de gestion hospitalière, a été créé avec succès.
    
        Vous pouvez désormais vous connecter avec les identifiants suivants :
    
            Email : {email}
            Mot de passe : {mot_de_passe}
    
        Nous vous recommandons de changer votre mot de passe dès votre première connexion pour plus de sécurité.
    
        Merci de votre confiance et bienvenue dans notre communauté !
    
        Cordialement,  
        L'équipe de la Clinique Floréal
        """
    )
    mail.send(msg)
    return True
