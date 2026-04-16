"""
Module patient - routes pour la gestion des patients
"""
import MySQLdb.cursors
import re
from flask import render_template, redirect, url_for, request, flash, session
from .utils import login_required, getLogin, envoie_email_connection


def init_patient(app, mysql, mail):
    """Initialise les routes patient"""
    
    @app.route("/admin/liste/patient")
    @login_required("admin")
    def liste_patient_admin():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM patient")
        patients = cursor.fetchall()
        return render_template("admin/gestion_patient/liste_patient.html", patients=patients)

    @app.route("/admin/patient/ajouter", methods=['GET', 'POST'])
    @login_required("admin")
    def signup_patient_admin():
        """Nouvelle page d'ajout de patient avec personnes à prévenir et assurances"""
        if 'email_admin' in session:
            loggedIn, firstName = getLogin('email_admin', 'admin', mysql)
            
            if request.method == 'POST':
                # Récupérer les données du patient
                donnees = request.form
                nom = donnees.get('nom')
                prenom = donnees.get('prenom')
                email = donnees.get('email')
                date_naissance = donnees.get('date_naissance')
                sexe = donnees.get('sexe')
                adresse = donnees.get('adresse')
                ville = donnees.get('ville')
                numero_telephone = donnees.get('tel')
                profession = donnees.get('profession', '')

                cursor = mysql.connection.cursor()

                # Vérifier si le patient existe déjà (nom + prénom + date de naissance + sexe)
                cursor.execute("SELECT * FROM patient WHERE nom = %s AND prenom = %s AND date_naissance = %s AND sexe = %s", 
                           (nom, prenom, date_naissance, sexe))
                existing_patient = cursor.fetchone()

                if existing_patient:
                    flash("Ce patient existe déjà dans le système.", "danger")
                    return redirect(request.url)

                try:
                    # 1. Insérer le patient
                    cursor.execute("""INSERT INTO patient 
                                    (nom, prenom, email_patient, date_naissance, sexe, adresse, ville, numero_telephone, profession)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                                   (nom, prenom, email, date_naissance, sexe, adresse, ville, numero_telephone, profession))
                    mysql.connection.commit()
                    
                    # 2. Récupérer l'ID du patient inséré
                    patient_id = cursor.lastrowid
                    print(f"Patient inséré avec ID: {patient_id}")

                    # 3. ===== TRAITEMENT DES PERSONNES À PRÉVENIR =====
                    personnes_data = {}
                    for key, value in donnees.items():
                        if key.startswith('personnes['):
                            # Extraire l'index et le champ
                            # Format: personnes[0][nom] -> index=0, champ=nom
                            match = re.match(r'personnes\[(\d+)\]\[(\w+)\]', key)
                            if match:
                                index = int(match.group(1))
                                champ = match.group(2)
                                if index not in personnes_data:
                                    personnes_data[index] = {}
                                personnes_data[index][champ] = value

                    # Insérer les personnes à prévenir
                    for personne_data in personnes_data.values():
                        if personne_data.get('nom') and personne_data.get('telephone'):  # Vérifier les champs requis
                            # Gérer le type de personne (si "autre", utiliser la précision)
                            type_personne = personne_data.get('type_personne', '')
                            if type_personne == 'autre' and personne_data.get('type_personne_autre'):
                                type_personne = personne_data.get('type_personne_autre')
                            
                            cursor.execute("""INSERT INTO personne_prevenir 
                                            (patient_id, nom, prenom, profession, telephone, type_personne)
                                            VALUES (%s, %s, %s, %s, %s, %s)""",
                                           (patient_id, 
                                            personne_data.get('nom', ''),
                                            personne_data.get('prenom', ''),
                                            personne_data.get('profession', ''),
                                            personne_data.get('telephone', ''),
                                            type_personne))
                    print(f"Personnes à prévenir insérées: {len(personnes_data)}")

                    # 4. ===== TRAITEMENT DES ASSURANCES =====
                    assurances_data = {}
                    for key, value in donnees.items():
                        if key.startswith('assurances['):
                            # Format: assurances[0][type_assurance] -> index=0, champ=type_assurance
                            match = re.match(r'assurances\[(\d+)\]\[(\w+)\]', key)
                            if match:
                                index = int(match.group(1))
                                champ = match.group(2)
                                if index not in assurances_data:
                                    assurances_data[index] = {}
                                assurances_data[index][champ] = value

                    # Insérer les assurances
                    for assurance_data in assurances_data.values():
                        if assurance_data.get('type_assurance') and assurance_data.get('numero_assurance'):  # Vérifier les champs requis
                            # Gérer le type d'assurance (si "autre", utiliser la précision)
                            type_assurance = assurance_data.get('type_assurance', '')
                            if type_assurance == 'autre' and assurance_data.get('type_assurance_autre'):
                                type_assurance = assurance_data.get('type_assurance_autre')
                            
                            cursor.execute("""INSERT INTO assurance 
                                            (patient_id, type_assurance, numero_assurance, pourcentage)
                                            VALUES (%s, %s, %s, %s)""",
                                           (patient_id, 
                                            type_assurance,
                                            assurance_data.get('numero_assurance', ''),
                                            float(assurance_data.get('pourcentage', 0) or 0)))
                    print(f"Assurances insérées: {len(assurances_data)}")

                    mysql.connection.commit()

                    # Envoi de l'email pour informer le patient
                    try:
                        envoie_email_connection(email, "password_placeholder", nom, prenom, mail)
                    except Exception as e:
                        print(e)

                    flash(f"Patient ajouté avec succès! {len(personnes_data)} personne(s) à prévenir et {len(assurances_data)} assurance(s) enregistrée(s).", "success")
                    return redirect(url_for('liste_patient_admin'))

                except Exception as e:
                    mysql.connection.rollback()
                    print(f"Erreur lors de l'inscription: {e}")
                    return f"Erreur lors de l'inscription : {e}"

            # GET : afficher le formulaire
            return render_template('admin/gestion_patient/ajouter_patient.html', loggedIn=loggedIn, firstName=firstName)

    # ===== ROUTES ADMIN POUR LA GESTION DES PATIENTS =====
    
    @app.route("/admin/patient/<int:patient_id>/gestion")
    @login_required("admin")
    def admin_gestion_patient(patient_id):
        """Page de gestion du patient avec actions multiples"""
        if 'email_admin' in session:
            loggedIn, firstName = getLogin('email_admin', 'admin', mysql)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Récupérer les infos du patient
            cursor.execute("SELECT * FROM patient WHERE id = %s", (patient_id,))
            patient = cursor.fetchone()
            
            if not patient:
                flash("Patient non trouvé.", "danger")
                return redirect(url_for('liste_patient_admin'))
            
            # Récupérer les personnes à prévenir
            cursor.execute("SELECT * FROM personne_prevenir WHERE patient_id = %s", (patient_id,))
            personnes_a_prevenir = cursor.fetchall()
            
            # Récupérer les assurances
            cursor.execute("SELECT * FROM assurance WHERE patient_id = %s", (patient_id,))
            assurances = cursor.fetchall()
            
            return render_template('admin/gestion_patient/gestion_patient.html',
                             patient=patient, 
                             personnes_a_prevenir=personnes_a_prevenir,
                             assurances=assurances,
                             loggedIn=loggedIn, firstName=firstName)
        else:
            return redirect(url_for('login'))

    @app.route("/admin/patient/<int:patient_id>")
    @login_required("admin")
    def admin_voir_patient(patient_id):
        """Voir les détails d'un patient"""
        if 'email_admin' in session:
            loggedIn, firstName = getLogin('email_admin', 'admin', mysql)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Récupérer les infos du patient
            cursor.execute("SELECT * FROM patient WHERE id = %s", (patient_id,))
            patient = cursor.fetchone()
            
            if not patient:
                flash("Patient non trouvé.", "danger")
                return redirect(url_for('liste_patient_admin'))
            
            # Récupérer les personnes à prévenir
            cursor.execute("SELECT * FROM personne_prevenir WHERE patient_id = %s", (patient_id,))
            personnes_a_prevenir = cursor.fetchall()
            
            # Récupérer les assurances
            cursor.execute("SELECT * FROM assurance WHERE patient_id = %s", (patient_id,))
            assurances = cursor.fetchall()
            
            return render_template('admin/gestion_patient/detail_patient.html',
                             patient=patient, 
                             personnes_a_prevenir=personnes_a_prevenir,
                             assurances=assurances,
                             loggedIn=loggedIn, firstName=firstName)
        else:
            return redirect(url_for('login'))

    @app.route("/admin/patient/<int:patient_id>/modifier", methods=['GET', 'POST'])
    @login_required("admin")
    def admin_modifier_patient(patient_id):
        """Modifier un patient et ses données associées"""
        if 'email_admin' in session:
            loggedIn, firstName = getLogin('email_admin', 'admin', mysql)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Récupérer les infos du patient
            cursor.execute("SELECT * FROM patient WHERE id = %s", (patient_id,))
            patient = cursor.fetchone()
            
            if not patient:
                flash("Patient non trouvé.", "danger")
                return redirect(url_for('liste_patient_admin'))
            
            if request.method == 'POST':
                # Récupérer les données du formulaire
                donnees = request.form
                nom = donnees.get('nom')
                prenom = donnees.get('prenom')
                email = donnees.get('email')
                date_naissance = donnees.get('date_naissance')
                sexe = donnees.get('sexe')
                adresse = donnees.get('adresse')
                ville = donnees.get('ville')
                numero_telephone = donnees.get('tel')
                profession = donnees.get('profession', '')

                # Vérifier si un autre patient avec mêmes infos existe déjà
                cursor.execute("SELECT * FROM patient WHERE nom = %s AND prenom = %s AND date_naissance = %s AND sexe = %s AND id != %s", 
                           (nom, prenom, date_naissance, sexe, patient_id))
                existing_patient = cursor.fetchone()

                if existing_patient:
                    flash("Un autre patient avec les mêmes informations existe déjà dans le système.", "danger")
                    return redirect(request.url)

                try:
                    # 1. Mettre à jour le patient
                    cursor.execute("""UPDATE patient 
                                    SET nom = %s, prenom = %s, email_patient = %s, 
                                        date_naissance = %s, sexe = %s, adresse = %s, 
                                        ville = %s, numero_telephone = %s, profession = %s
                                    WHERE id = %s""",
                                   (nom, prenom, email, date_naissance, sexe, adresse, 
                                    ville, numero_telephone, profession, patient_id))
                    
                    # 2. Supprimer anciennes personnes à prévenir et assurances
                    cursor.execute("DELETE FROM personne_prevenir WHERE patient_id = %s", (patient_id,))
                    cursor.execute("DELETE FROM assurance WHERE patient_id = %s", (patient_id,))
                    
                    # 3. ===== TRAITEMENT DES NOUVELLES PERSONNES À PRÉVENIR =====
                    personnes_data = {}
                    for key, value in donnees.items():
                        if key.startswith('personnes['):
                            match = re.match(r'personnes\[(\d+)\]\[(\w+)\]', key)
                            if match:
                                index = int(match.group(1))
                                champ = match.group(2)
                                if index not in personnes_data:
                                    personnes_data[index] = {}
                                personnes_data[index][champ] = value

                    # Insérer les nouvelles personnes à prévenir
                    for personne_data in personnes_data.values():
                        if personne_data.get('nom') and personne_data.get('telephone'):
                            type_personne = personne_data.get('type_personne', '')
                            if type_personne == 'autre' and personne_data.get('type_personne_autre'):
                                type_personne = personne_data.get('type_personne_autre')
                            
                            cursor.execute("""INSERT INTO personne_prevenir 
                                            (patient_id, nom, prenom, profession, telephone, type_personne)
                                            VALUES (%s, %s, %s, %s, %s, %s)""",
                                           (patient_id, 
                                            personne_data.get('nom', ''),
                                            personne_data.get('prenom', ''),
                                            personne_data.get('profession', ''),
                                            personne_data.get('telephone', ''),
                                            type_personne))

                    # 4. ===== TRAITEMENT DES NOUVELLES ASSURANCES =====
                    assurances_data = {}
                    for key, value in donnees.items():
                        if key.startswith('assurances['):
                            match = re.match(r'assurances\[(\d+)\]\[(\w+)\]', key)
                            if match:
                                index = int(match.group(1))
                                champ = match.group(2)
                                if index not in assurances_data:
                                    assurances_data[index] = {}
                                assurances_data[index][champ] = value

                    # Insérer les nouvelles assurances
                    for assurance_data in assurances_data.values():
                        if assurance_data.get('type_assurance') and assurance_data.get('numero_assurance'):
                            type_assurance = assurance_data.get('type_assurance', '')
                            if type_assurance == 'autre' and assurance_data.get('type_assurance_autre'):
                                type_assurance = assurance_data.get('type_assurance_autre')
                            
                            cursor.execute("""INSERT INTO assurance 
                                            (patient_id, type_assurance, numero_assurance, pourcentage)
                                            VALUES (%s, %s, %s, %s)""",
                                           (patient_id, 
                                            type_assurance,
                                            assurance_data.get('numero_assurance', ''),
                                            float(assurance_data.get('pourcentage', 0) or 0)))

                    mysql.connection.commit()
                    flash(f"Patient {nom} {prenom} modifié avec succès!", "success")
                    return redirect(url_for('admin_voir_patient', patient_id=patient_id))

                except Exception as e:
                    mysql.connection.rollback()
                    print(f"Erreur lors de la modification: {e}")
                    return f"Erreur lors de la modification : {e}"

            # GET : afficher le formulaire avec données pré-remplies
            # Récupérer les personnes à prévenir existantes
            cursor.execute("SELECT * FROM personne_prevenir WHERE patient_id = %s", (patient_id,))
            personnes_a_prevenir = cursor.fetchall()
            
            # Récupérer les assurances existantes
            cursor.execute("SELECT * FROM assurance WHERE patient_id = %s", (patient_id,))
            assurances = cursor.fetchall()
            
            return render_template('admin/gestion_patient/modifier_patient.html',
                             patient=patient,
                             personnes_a_prevenir=personnes_a_prevenir,
                             assurances=assurances,
                             loggedIn=loggedIn, firstName=firstName)
        else:
            return redirect(url_for('login'))

    @app.route("/admin/patients/supprimer/<int:patient_id>", methods=['GET', 'POST'])
    @login_required("admin")
    def admin_supprimer_patient(patient_id):
        """Supprimer un patient et ses données associées"""
        if 'email_admin' in session:
            cursor = mysql.connection.cursor()
            
            try:
                # Vérifier si le patient existe
                cursor.execute("SELECT nom, prenom FROM patient WHERE id = %s", (patient_id,))
                patient = cursor.fetchone()
                
                if not patient:
                    flash("Patient non trouvé.", "danger")
                    return redirect(url_for('liste_patient_admin'))
                
                # Supprimer le patient (les tables liées seront supprimées en cascade grâce aux FOREIGN KEY)
                cursor.execute("DELETE FROM patient WHERE id = %s", (patient_id,))
                mysql.connection.commit()
                
                flash(f"Patient {patient[0]} {patient[1]} supprimé avec succès!", "success")
                return redirect(url_for('liste_patient_admin'))
                
            except Exception as e:
                mysql.connection.rollback()
                print(f"Erreur lors de la suppression: {e}")
                return f"Erreur lors de la suppression : {e}"
        else:
            return redirect(url_for('login'))

