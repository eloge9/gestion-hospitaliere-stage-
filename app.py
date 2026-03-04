from flask import Flask, render_template, redirect, url_for, session, request, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import hashlib
from credentials import *
from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)

# pour la base de donner
app.config['SECRET_KEY']=my_token
app.config['MYSQL_HOST'] = my_host
app.config['MYSQL_USER'] = my_user
app.config['MYSQL_PASSWORD'] = my_password
app.config['MYSQL_DB'] =  my_db
app.config['MYSQL_CURSORCLASS'] =my_CURSORCLASS


#pour l'envoie de Email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = my_email
app.config['MAIL_PASSWORD'] = my_password_generer
app.config['MAIL_DEFAULT_SENDER'] = ('Gestion Hospitaliere', 'elogegomina@gmail.com')

mail = Mail(app)

mysql = MySQL()
mysql.init_app(app)

app.secret_key = my_secret_key



"""debut admin"""
#admin
@app.route("/admin")
def index():
    return render_template("admin/index_admin.html")

#admin liste admin
@app.route('/admin/liste_admin')
def liste_admin():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT id, nom, prenom, email_admin, numero_telephone FROM admin")
    admins = cursor.fetchall()
    cursor.close()
    return render_template("admin/gestion_admin/liste_admin.html", admins=admins)

#suprimer admin
@app.route('/admin/supprimer/<int:id>', methods=['GET', 'POST'])
def supprimer_admin(id):
    cursor = mysql.connection.cursor()
    try:
        # Supprimer l’admin avec l’identifiant donné
        cursor.execute("DELETE FROM admin WHERE id = %s", (id,))
        mysql.connection.commit()
        flash("Administrateur supprimé avec succès.", "success")
    except Exception as e:
        flash("Erreur lors de la suppression : " + str(e), "danger")
    finally:
        cursor.close()

    # Redirection vers la liste des admins (ou une autre page)
    return redirect(url_for('liste_admin'))


#modifier admin
@app.route("/modifier-admin/<int:id>", methods=["GET", "POST"])
def modifier_admin(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == "POST":
        nom_complet = request.form['nom_complet']
        email = request.form['email_admin']
        numero_telephone = request.form['numero_telephone']

        # Exécution de la requête UPDATE
        cursor.execute("""
            UPDATE admin SET nom_complet=%s, email_admin=%s, numero_telephone=%s 
            WHERE id=%s
        """, (nom_complet, email, numero_telephone, id))

        mysql.connection.commit()
        flash("Les informations ont été modifiées avec succès.", "success")
        return redirect(url_for('liste_admin'))  # attention au nom exact de la fonction liste

    # Sinon (GET), on affiche les infos actuelles dans le formulaire
    cursor.execute("SELECT * FROM admin WHERE id = %s", (id,))
    admin = cursor.fetchone()
    return render_template("admin/gestion_admin/modifier_admin.html", admin=admin)


#liste docteur admin
@app.route("/admin/liste_docteur")
def liste_docteur_admin():
    if 'email_admin' not in session:
        flash("Connectez-vous d'abord", "warning")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM doctor")
    doctors = cursor.fetchall()
    return render_template("admin/gestion_docteur/Liste_docteur.html", doctors=doctors)

# uprimer admin
@app.route('/admin/supprimer_docteur/<int:id>')
def supprimer_docteur(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM doctor WHERE id = %s", (id,))
    mysql.connection.commit()
    flash("Médecin supprimé avec succès.", "success")
    return redirect(url_for('liste_docteur_admin'))

#profile admin
@app.route('/admin/voir/<int:id>')
def voir_admin(id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT id, nom_complet, email_admin, numero_telephone, date_inscription FROM admin WHERE id = %s", (id,))
    admin = cursor.fetchone()  # Un seul admin

    if not admin:
        flash("Administrateur introuvable.", "warning")
        return redirect(url_for('liste_admin'))

    return render_template("admin/gestion_admin/profile_admin.html", admin=admin)

# mmodifier profile docteur par admin
@app.route('/admin/docteur/<int:id>')
def profile_doctor_admin(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM doctor WHERE id = %s", (id,))
    mysql.connection.commit()
    flash("Médecin supprimé avec succès.", "success")
    return render_template("admin/gestion_docteur/voir_profile_doctor.html")

@app.route('/admin/docteur/<int:id>')
def modifier_profile_doctor_admin(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM doctor WHERE id = %s", (id,))
    mysql.connection.commit()
    flash("Médecin supprimé avec succès.", "success")
    return render_template("admin/gestion_docteur/voir_profile_doctor.html")
"""fin admin"""



"""debut caissier"""
@app.route("/caissier")
def index_caissier():
    return render_template("caissier/index_caissier.html")

"""fin caissier"""






"""debut docteur"""
# docteur
@app.route("/doctor")
def index_doctor():
    return render_template("doctor/index_doctor.html")

# liste docteur docteur
@app.route("/doctor/liste_doctor")
def liste_doctor():
    return render_template("doctor/gestion_docteur/liste_doctor.html")

# modification profile docteur
@app.route("/doctor/modifier_profile", methods=['GET', 'POST'])
def modifier_profile_doctor():
    if 'email_doctor' not in session:
        flash("Veuillez vous connecter.", "warning")
        return redirect(url_for('login'))

    email = session['email_doctor']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        donnes = request.form
        nom_utilisateur = donnes.get('username')
        nom = donnes.get('nom')
        prenom = donnes.get('prenom')
        nom_complet = (nom + ' ' + prenom) if nom and prenom else None
        date_naissance = donnes.get('date_naissance')
        sexe = donnes.get('sexe')
        situation_matrimoniale = donnes.get('situation_matrimoniale')
        groupe_sanguin = donnes.get('groupe_sanguin')
        photo = donnes.get('photo')
        description = donnes.get('biography')
        adresse = donnes.get('adresse')
        pays = donnes.get('pays')
        ville = donnes.get('ville')
        code_postal = donnes.get('code_postal')
        numero_telephone = donnes.get('telephone')
        qualification = donnes.get('qualification')
        designation = donnes.get('designation')
        password = donnes.get('new_password')
        confirm_password = donnes.get('confirm_new_password')
        heure_debut_dimanche = donnes.get('dimanche_debut')
        heure_fin_dimanche = donnes.get('dimanche_fin')
        heure_debut_lundi = donnes.get('lundi_debut')
        heure_fin_lundi = donnes.get('lundi_fin')
        heure_debut_mardi = donnes.get('mardi_debut')
        heure_fin_mardi = donnes.get('mardi_fin')
        heure_debut_mercredi = donnes.get('mercredi_debut')
        heure_fin_mercredi = donnes.get('mercredi_fin')
        heure_debut_jeudi = donnes.get('jeudi_debut')
        heure_fin_jeudi = donnes.get('jeudi_fin')
        heure_debut_vendredi = donnes.get('vendredi_debut')
        heure_fin_vendredi = donnes.get('vendredi_fin')
        heure_debut_samedi = donnes.get('samedi_debut')
        heure_fin_samedi = donnes.get('samedi_fin')

        print(heure_fin_samedi)
        # Récupérer les anciennes données
        cursor.execute("SELECT * FROM doctor WHERE email_doctor = %s", (email,))
        ancien_profil = cursor.fetchone()

        if not ancien_profil:
            flash("Profil non trouvé.", "danger")
            return redirect(url_for('index_doctor'))

        # Vérification du nom d'utilisateur déjà utilisé par un autre compte
        if nom_utilisateur and nom_utilisateur != ancien_profil['nom_utilisateur']:
            cursor.execute("SELECT * FROM doctor WHERE nom_utilisateur = %s AND email_doctor != %s",
                           (nom_utilisateur, email))
            existing_user = cursor.fetchone()
            if existing_user:
                flash("Ce nom d'utilisateur est déjà utilisé. Veuillez en utiliser un autre.", "danger")
                return redirect(request.url)

        # Gestion mot de passe
        if password:
            if password != confirm_password:
                flash("Les mots de passe ne correspondent pas. Veuillez réessayer.", "danger")
                return redirect(request.url)
            hashed_password = hashlib.md5(password.encode()).hexdigest()
        else:
            hashed_password = ancien_profil['password']

        # Préparer les valeurs, en gardant l'ancienne si champ vide
        nom_utilisateur = nom_utilisateur or ancien_profil['nom_utilisateur']
        nom_complet = nom_complet or ancien_profil['nom_complet']
        date_naissance = date_naissance or ancien_profil['date_naissance']
        sexe = sexe or ancien_profil['sexe']
        situation_matrimoniale = situation_matrimoniale or ancien_profil['situation_matrimoniale']
        groupe_sanguin = groupe_sanguin or ancien_profil['groupe_sanguin']
        photo = photo or ancien_profil['photo']
        description = description or ancien_profil['description']
        adresse = adresse or ancien_profil['adresse']
        pays = pays or ancien_profil['pays']
        ville = ville or ancien_profil['ville']
        code_postal = code_postal or ancien_profil['code_postal']
        numero_telephone = numero_telephone or ancien_profil['numero_telephone']
        qualification = qualification or ancien_profil['qualification']
        designation = designation or ancien_profil['designation']
        heure_debut_dimanche = heure_debut_dimanche or ancien_profil.get('heure_debut_dimanche')
        heure_fin_dimanche = heure_fin_dimanche or ancien_profil.get('heure_fin_dimanche')
        heure_debut_lundi = heure_debut_lundi or ancien_profil.get('heure_debut_lundi')
        heure_fin_lundi = heure_fin_lundi or ancien_profil.get('heure_fin_lundi')
        heure_debut_mardi = heure_debut_mardi or ancien_profil.get('heure_debut_mardi')
        heure_fin_mardi = heure_fin_mardi or ancien_profil.get('heure_fin_mardi')
        heure_debut_mercredi = heure_debut_mercredi or ancien_profil.get('heure_debut_mercredi')
        heure_fin_mercredi = heure_fin_mercredi or ancien_profil.get('heure_fin_mercredi')
        heure_debut_jeudi = heure_debut_jeudi or ancien_profil.get('heure_debut_jeudi')
        heure_fin_jeudi = heure_fin_jeudi or ancien_profil.get('heure_fin_jeudi')
        heure_debut_vendredi = heure_debut_vendredi or ancien_profil.get('heure_debut_vendredi')
        heure_fin_vendredi = heure_fin_vendredi or ancien_profil.get('heure_fin_vendredi')
        heure_debut_samedi = heure_debut_samedi or ancien_profil.get('heure_debut_samedi')
        heure_fin_samedi = heure_fin_samedi or ancien_profil.get('heure_fin_samedi')

        try:
            cursor.execute("""
                            UPDATE doctor SET
                                nom_utilisateur=%s,
                                nom_complet=%s,
                                date_naissance=%s,
                                sexe=%s,
                                situation_matrimoniale=%s,
                                groupe_sanguin=%s,
                                photo=%s,
                                description=%s,
                                adresse=%s,
                                pays=%s,
                                ville=%s,
                                code_postal=%s,
                                numero_telephone=%s,
                                qualification=%s,
                                designation=%s,
                                password=%s,
                                heure_debut_dimanche=%s,
                                heure_fin_dimanche=%s,
                                heure_debut_lundi=%s,
                                heure_fin_lundi=%s,
                                heure_debut_mardi=%s,
                                heure_fin_mardi=%s,
                                heure_debut_mercredi=%s,
                                heure_fin_mercredi=%s,
                                heure_debut_jeudi=%s,
                                heure_fin_jeudi=%s,
                                heure_debut_vendredi=%s,
                                heure_fin_vendredi=%s,
                                heure_debut_samedi=%s,
                                heure_fin_samedi=%s
                            WHERE email_doctor=%s
                        """, (
                nom_utilisateur, nom_complet, date_naissance, sexe,
                situation_matrimoniale, groupe_sanguin, photo, description,
                adresse, pays, ville, code_postal, numero_telephone,
                qualification, designation, hashed_password,
                heure_debut_dimanche, heure_fin_dimanche,
                heure_debut_lundi, heure_fin_lundi,
                heure_debut_mardi, heure_fin_mardi,
                heure_debut_mercredi, heure_fin_mercredi,
                heure_debut_jeudi, heure_fin_jeudi,
                heure_debut_vendredi, heure_fin_vendredi,
                heure_debut_samedi, heure_fin_samedi,
                email
            ))

            mysql.connection.commit()
            cursor.close()
            flash("Profil mis à jour avec succès.", "success")
            return redirect(url_for('index_doctor'))

        except Exception as e:
            print("Erreur lors de la modification du profil :", e)
            flash("Erreur lors de la modification du profil.", "danger")
            return redirect(request.url)

    # En GET : Pré-remplir les champs
    cursor.execute("SELECT * FROM doctor WHERE email_doctor = %s", (email,))
    doctor = cursor.fetchone()
    cursor.close()

    # pour tout les pays
    pays = [
        "Afghanistan", "Afrique du Sud", "Albanie", "Algérie", "Allemagne", "Andorre", "Angola", "Antigua-et-Barbuda",
        "Arabie Saoudite", "Argentine", "Arménie", "Australie", "Autriche", "Azerbaïdjan", "Bahamas", "Bahreïn",
        "Bangladesh", "Barbade", "Belgique", "Belize", "Bénin", "Bhoutan", "Biélorussie", "Birmanie", "Bolivie",
        "Bosnie-Herzégovine", "Botswana", "Brésil", "Brunei", "Bulgarie", "Burkina Faso", "Burundi", "Cambodge",
        "Cameroun", "Canada", "Cap-Vert", "République centrafricaine", "Chili", "Chine", "Chypre", "Colombie",
        "Comores",
        "Congo (Brazzaville)", "Congo (RDC)", "Corée du Nord", "Corée du Sud", "Costa Rica", "Côte d'Ivoire", "Croatie",
        "Cuba", "Danemark", "Djibouti", "Dominique", "Égypte", "Émirats arabes unis", "Équateur", "Érythrée", "Espagne",
        "Estonie", "Eswatini", "États-Unis", "Éthiopie", "Fidji", "Finlande", "France", "Gabon", "Gambie", "Géorgie",
        "Ghana", "Grèce", "Grenade", "Guatemala", "Guinée", "Guinée-Bissau", "Guinée équatoriale", "Guyana", "Haïti",
        "Honduras", "Hongrie", "Inde", "Indonésie", "Irak", "Iran", "Irlande", "Islande", "Israël", "Italie",
        "Jamaïque",
        "Japon", "Jordanie", "Kazakhstan", "Kenya", "Kirghizistan", "Kiribati", "Koweït", "Laos", "Lesotho", "Lettonie",
        "Liban", "Libéria", "Libye", "Liechtenstein", "Lituanie", "Luxembourg", "Macédoine du Nord", "Madagascar",
        "Malaisie", "Malawi", "Maldives", "Mali", "Malte", "Maroc", "Îles Marshall", "Maurice", "Mauritanie", "Mexique",
        "Micronésie", "Moldavie", "Monaco", "Mongolie", "Monténégro", "Mozambique", "Namibie", "Nauru", "Népal",
        "Nicaragua", "Niger", "Nigeria", "Norvège", "Nouvelle-Zélande", "Oman", "Ouganda", "Ouzbékistan", "Pakistan",
        "Palaos", "Palestine", "Panama", "Papouasie-Nouvelle-Guinée", "Paraguay", "Pays-Bas", "Pérou", "Philippines",
        "Pologne", "Portugal", "Qatar", "Roumanie", "Royaume-Uni", "Russie", "Rwanda", "Saint-Kitts-et-Nevis",
        "Sainte-Lucie", "Saint-Marin", "Saint-Vincent-et-les-Grenadines", "Salomon", "Salvador", "Samoa",
        "São Tomé-et-Príncipe",
        "Sénégal", "Serbie", "Seychelles", "Sierra Leone", "Singapour", "Slovaquie", "Slovénie", "Somalie", "Soudan",
        "Soudan du Sud", "Sri Lanka", "Suède", "Suisse", "Suriname", "Syrie", "Tadjikistan", "Tanzanie", "Tchad",
        "République tchèque", "Thaïlande", "Timor oriental", "Togo", "Tonga", "Trinité-et-Tobago", "Tunisie",
        "Turkménistan",
        "Turquie", "Tuvalu", "Ukraine", "Uruguay", "Vanuatu", "Vatican", "Venezuela", "Viêt Nam", "Yémen", "Zambie",
        "Zimbabwe"
    ]

    return render_template("doctor/gestion_docteur/modifier_profile.html", pays=pays, doctor=doctor)

@app.route("/doctor/profile_doctor")
def profile_doctor():
    return render_template("doctor/gestion_docteur/profile_doctor.html")

#doctor patient
@app.route("/doctor/liste_patient")
def liste_patient_doctor():
    return render_template("doctor/gestion_patient/liste_patient.html")

@app.route("/doctor/ajout_patient")
def add_patient_doctor():
    return render_template("doctor/gestion_patient/ajout_patient.html")

@app.route("/doctor/modifier_patient")
def modifier_patient_doctor():
    return render_template("doctor/gestion_patient/modifier_patient.html")

#doctor rendevous
@app.route("/doctor/rendez-vous")
def rendez_vous_doctor():
    return render_template("doctor/gestion_rendezvous/rendezvous.html")

@app.route("/doctor/rendez-vous/prendre_rendez-vous")
def prendre_rendez_vous_doctor():
    return render_template("doctor/gestion_rendezvous/prendre_rendezvous.html")

@app.route("/doctor/rendez-vous/modifier_rendez-vous")
def modifier_rendez_vous_doctor():
    return render_template("doctor/gestion_rendezvous/modifier_rendezvous.html")

@app.route("/doctor/rendez-vous/liste_rendez-vous")
def liste_rendez_vous_doctor():
    return render_template("doctor/gestion_rendezvous/liste_rendevous.html")

#doctor conge presence
@app.route("/doctor/conge_presence/congé")
def conge_doctor():
    return render_template("doctor/conge_presence/conge.html")

@app.route("/doctor/conge_presence/présence")
def presence_doctor():
    return render_template("doctor/conge_presence/presence.html")

# doctor galeri et evenement
@app.route("/doctor/actualiter")
def actualiter_doctor():
    return render_template("doctor/galerie_&_evenement/actualiter.html")

@app.route("/doctor/evenement")
def evenement_doctor():
    return render_template("doctor/galerie_&_evenement/evenement.html")

@app.route("/doctor/galerie")
def galerie_doctor():
    return render_template("doctor/galerie_&_evenement/galerie.html")

# doctor ia
@app.route("/doctor/ia/resumer_dossier_medical")
def resumer_dossier_doctor():
    return render_template("doctor/gestion_ia/resumer_dossier.html")

@app.route("/doctor/ia/sugection_de_traitement")
def sugetion_doctor():
    return render_template("doctor/gestion_ia/sugection_traitement.html")

@app.route("/doctor/ia/surleillance_patient")
def surveillance_dossier_doctor():
    return render_template("doctor/gestion_ia/survellanc_patient.html")

# doctor messagerie
@app.route("/doctor/messagerie")
def messageire_doctor():
    return render_template("doctor/gestion_messagerie/messagerie.html")

#doctor hospitalisation
@app.route("/doctor/hospitalisation")
def hospitalisation_doctor():
    return render_template("doctor/hospitalisation/hospitalisation.html")

#parametre dcoctor
@app.route("/doctor/parametre")
def parametre_doctor():
    return render_template("doctor/parametre/parametre.html")

# fiche de paie doctor
@app.route("/doctor/salaire/fiche_de_paie")
def fiche_de_paie_doctor():
    return render_template("doctor/salaire/fiche_de_paie.html")

# dossiermedical doctor
@app.route("/doctor/dossier_medical")
def dossier_medical_doctor():
    return render_template("doctor/dossier_medical/dossier_medical.html")

# consultation
@app.route("/doctor/consultation")
def consultation_doctor():
    return render_template("doctor/consultation/consultation.html")

"""fin docteur"""




#gestonaire de stoCK
@app.route("/gestionaire_stock")
def index_gestionaire_stock():
    return render_template("gestionaire_stock/index_gestionaire_stock.html")

@app.route("/infirmier")
def index_infirmier():
    return render_template("infirmier/index_infirmier.html")

@app.route("/patient")
def index_patient():
    return render_template("patient/index_patient.html")




#secretaiere medical
@app.route("/secretaire_medicales")
def index_secretaire_medicales():
    return render_template("secretaire_medicales/index_secretaire_medicales.html")

#admission_patient  secretaire medicale
@app.route("/secretaire_medicales/admission_patient")
def admission_patient():
    return render_template("secretaire_medicales/gestion_patients/admissions_patient.html")

#modification_patients secretaire medicale
@app.route("/secretaire_medicales/modification_patients")
def modif_patients():
    return render_template("secretaire_medicales/gestion_patients/modification_patients.html")

#gestion_rendezvous secretaire medicale
@app.route("/secretaire_medicales/gestion_rendezvous")
def gestion_rendezvous():
    return render_template("secretaire_medicales/gestion_rendez_vous/gestion_rendezvous.html")

#gestion_rendezvous secretaire medicale
@app.route("/secretaire_medicales/liste_rendezvous")
def liste_rendezvous():
    return render_template("secretaire_medicales/gestion_rendez_vous/liste_rendezvous.html")

#Modifier_rendezvous secretaire medicale
@app.route("/secretaire_medicales/Modifier_rendezvous")
def Modifier_rendezvous():
    return render_template("secretaire_medicales/gestion_rendez_vous/Modifier_rendezvous.html")

#prendre_rendezvous secretaire medicale
@app.route("/secretaire_medicales/prendre_rendezvous")
def prendre_rendezvous():
    return render_template("secretaire_medicales/gestion_rendez_vous/prendre_rendezvous.html")

#fiche_de_paie secretaire medicale
@app.route("/secretaire_medicales/fiche_de_paie")
def fiche_de_paie():
    return render_template("secretaire_medicales/gestion_salaire/fiche_de_paie.html")

#messagerie secretaire medicale
@app.route("/secretaire_medicales/messagerie")
def messagerie():
    return render_template("secretaire_medicales/gestion_messageries/messagerie.html")

#liste_departement secretaire medicale
@app.route("/secretaire_medicales/liste_departement")
def liste_departement():
    return render_template("secretaire_medicales/gestion_departement/liste_departement.html")

#congé_personnel secretaire medicale
@app.route("/secretaire_medicales/congé_personnel")
def congé_personnel():
    return render_template("secretaire_medicales/gestion_congé_presence/congé_personnel.html")

#présence_assiduité secretaire medicale
@app.route("/secretaire_medicales/presence_assiduite")
def presence_assiduite():
    return render_template("secretaire_medicales/gestion_congé_presence/presence_assiduite.html")

#Reserver_chambre secretaire medicale
@app.route("/secretaire_medicales/Reserver_chambre")
def Reserver_chambre():
    return render_template("secretaire_medicales/Gestion_chambre/Reserver_chambre.html")

#add_ambulance secretaire medicale
@app.route("/secretaire_medicales/add_ambulance")
def add_ambulance():
    return render_template("secretaire_medicales/gestion_ambulance/add_ambulance.html")

#ambulance_call_list secretaire medicale
@app.route("/secretaire_medicales/ambulance_call_list")
def ambulance_call_list():
    return render_template("secretaire_medicales/gestion_ambulance/ambulance_call_list.html")

#ambulance_list secretaire medicale
@app.route("/secretaire_medicales/ambulance_list")
def ambulance_list():
    return render_template("secretaire_medicales/gestion_ambulance/ambulance_list.html")


#edit_ambulance secretaire medicale
@app.route("/secretaire_medicales/edit_ambulance")
def edit_ambulance():
    return render_template("secretaire_medicales/gestion_ambulance/edit_ambulance.html")



#ajouter_patient  secretaire medicale
@app.route("/secretaire_medicales/ajouter_patient")
def ajouter_patient():
    return render_template("secretaire_medicales/gestion_patients/ajouter_patient.html")

#liste_admissions secretaire medicale
@app.route("/secretaire_medicales/liste_admissions")
def liste_admissions():
    return render_template("secretaire_medicales/gestion_patients/liste_admissions.html")







@app.route("/interne_medecine")
def index_interne_medecine():
    return render_template("interne_medecine/index_interne_medecine.html")

@app.route("/gestionnaire_logistique")
def index_gestionnaire_logistique():
    return render_template("gestionaire_logistique/index_logistique.html")

#modification_patients secretaire medicale
@app.route("/secretaire_medicales/modification_patients")
def modification_patients():
    return render_template("secretaire_medicales/gestion_patients/modification_patients.html")

#les connection
#connection de l'admin
def getLogin(session_key, table):
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

        query = f"SELECT nom_complet FROM {table} WHERE {session_key} = %s"
        cur.execute(query, (session[session_key],))
        result = cur.fetchone()
        if result:
            (firstName,) = result

    cur.close()
    return loggedIn, firstName

# Fonction is_valid

def is_valid(email, email_field, password, table):
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

#fonction login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['pwd']
        print(email)
        print(password)

        # Vérification des informations
        if is_valid(email, 'email_admin', password, 'admin'):
            session['email_admin'] = email
            return redirect(url_for('index'))

        elif is_valid(email, "email_doctor", password, "doctor"):

            session['email_doctor'] = email

            # Connexion à la base

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            cursor.execute("SELECT nom_utilisateur FROM doctor WHERE email_doctor = %s", (email,))

            result = cursor.fetchone()

            cursor.close()

            if result and result['nom_utilisateur']:  # Si rempli

                return redirect(url_for('index_doctor'))

            else:  # Si vide ou NULL

                return redirect(url_for('modifier_profile_doctor'))


        elif is_valid(email, "email_patient", password, "patient"):

            session['email_patient'] = email

            # Connexion à la base

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            cursor.execute("SELECT nom_utilisateur FROM patient WHERE email_patient = %s", (email,))

            result = cursor.fetchone()

            cursor.close()

            if result and result['nom_utilisateur']:  # Si rempli

                return redirect(url_for('index_patient'))

            else:  # Si vide ou NULL

                return redirect(url_for('modifier_profile_patient'))


        elif is_valid(email, "email_secretaire", password, "secretaire_medicale"):

            session['email_secretaire'] = email

            # Connexion à la base

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            cursor.execute("SELECT nom_utilisateur FROM secretaire_medicale WHERE email_secretaire = %s", (email,))

            result = cursor.fetchone()

            cursor.close()

            if result and result['nom_utilisateur']:  # Si rempli

                return redirect(url_for('index_secretaire_medicales'))

            else:  # Si vide ou NULL

                return redirect(url_for('modifier_profile_secretaire'))



        elif is_valid(email, "email_ambulancier", password, "ambulancier"):

            session['email_ambulancier'] = email

            # Connexion à la base

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            cursor.execute("SELECT nom_utilisateur FROM ambulancier WHERE email_ambulancier = %s", (email,))

            result = cursor.fetchone()

            cursor.close()

            if result and result['nom_utilisateur']:  # Si rempli

                return redirect(url_for('index_ambulancier'))

            else:  # Si vide ou NULL

                return redirect(url_for('modifier_profile_ambulancier'))



        elif is_valid(email, "email_caissier", password, "caissier"):

            session['email_caissier'] = email

            # Connexion à la base

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            cursor.execute("SELECT nom_utilisateur FROM caissier WHERE email_caissier = %s", (email,))

            result = cursor.fetchone()

            cursor.close()

            if result and result['nom_utilisateur']:  # Si rempli

                return redirect(url_for('index_caissier'))

            else:  # Si vide ou NULL

                return redirect(url_for('modifier_profile_caissier'))



        elif is_valid(email, "email_logistique", password, "gestionnaire_logistique"):

            session['email_logistique'] = email

            # Connexion à la base

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            cursor.execute("SELECT nom_utilisateur FROM gestionnaire_logistique WHERE email_logistique = %s", (email,))

            result = cursor.fetchone()

            cursor.close()

            if result and result['nom_utilisateur']:  # Si rempli

                return redirect(url_for('index_logistique'))

            else:  # Si vide ou NULL

                return redirect(url_for('modifier_profile_logistique'))



        elif is_valid(email, "email_stock", password, "gestionnaire_stock"):

            session['email_stock'] = email

            # Connexion à la base

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            cursor.execute("SELECT nom_utilisateur FROM gestionnaire_stock WHERE email_stock = %s", (email,))

            result = cursor.fetchone()

            cursor.close()

            if result and result['nom_utilisateur']:  # Si rempli

                return redirect(url_for('index_stock'))

            else:  # Si vide ou NULL

                return redirect(url_for('modifier_profile_stock'))



        elif is_valid(email, "email_infirmier", password, "infirmier"):

            session['email_infirmier'] = email

            # Connexion à la base

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            cursor.execute("SELECT nom_utilisateur FROM infirmier WHERE email_infirmier = %s", (email,))

            result = cursor.fetchone()

            cursor.close()

            if result and result['nom_utilisateur']:  # Si rempli

                return redirect(url_for('index_infirmier'))

            else:  # Si vide ou NULL

                return redirect(url_for('modifier_profile_infirmier'))



        elif is_valid(email, "email_interne", password, "interne_medecine"):

            session['email_interne'] = email

            # Connexion à la base

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            cursor.execute("SELECT nom_utilisateur FROM interne_medecine WHERE email_interne = %s", (email,))

            result = cursor.fetchone()

            cursor.close()

            if result and result['nom_utilisateur']:  # Si rempli

                return redirect(url_for('index_interne'))

            else:  # Si vide ou NULL

                return redirect(url_for('modifier_profile_interne'))

        else:
            flash('Email ou mot de passe incorrect.', 'danger')
            return redirect(url_for('login'))
    return render_template('admin/connexion/login.html')





# les deconnection
@app.route('/logout')
def logout():
    # Détection du rôle
    role = None
    nom = session.get('nom', '')

    if 'email_admin' in session:
        role = 'admin'
        session.pop('email_admin')
    elif 'email_doctor' in session:
        role = 'docteur'
        session.pop('email_doctor')
    elif 'email_patient' in session:
        role = 'patient'
        session.pop('email_patient')
    elif 'email_secretaire' in session:
        role = 'secrétaire médicale'
        session.pop('email_secretaire')
    elif 'email_ambulancier' in session:
        role = 'ambulancier'
        session.pop('email_ambulancier')
    elif 'email_caissier' in session:
        role = 'caissier'
        session.pop('email_caissier')
    elif 'email_logistique' in session:
        role = 'gestionnaire logistique'
        session.pop('email_logistique')
    elif 'email_stock' in session:
        role = 'gestionnaire stock'
        session.pop('email_stock')
    elif 'email_infirmier' in session:
        role = 'infirmier'
        session.pop('email_infirmier')
    elif 'email_interne' in session:
        role = 'interne en médecine'
        session.pop('email_interne')

    # Optionnel : vider complètement la session
    session.clear()

    flash(f"Déconnexion de {role or 'utilisateur inconnu'} {nom}", 'success')
    return redirect(url_for('login'))






# les inscription
#systeme denvoie Email
def envoie_email_connection(email, mot_de_passe):

    # ... ici tu enregistres le personnel dans la base de données ...

    # Envoi de l'e-mail automatique
    msg = Message(
        subject="Bienvenue sur notre application",
        recipients=[email],
        body=f"""Bonjour,

            Bienvenue sur MediJutsu ! Votre compte a été créé avec succès. Vous pouvez désormais vous connecter à notre 
            application de gestion hospitalière à l'aide des identifiants suivants :
            
            - Email : {email}
            - Mot de passe : {mot_de_passe}
            
            Merci de votre confiance.
            
            L'équipe de support.
            """
    )
    mail.send(msg)

    return redirect(url_for("index"))  # ou une page de succès
# inscription de l'admininsatrateur
@app.route("/signup_admin", methods=['GET', 'POST'])
def signup():
    if 'email_admin' in session:
        loggedIn, firstName = getLogin('email_admin', 'admin')
        if request.method == 'POST':
            donnes = request.form
            name = (donnes.get('name') or '').strip()
            prenom = (donnes.get('prenom') or '').strip()
            nom_complet = name + ' ' + prenom
            email = donnes.get('email')
            numero_telephone = donnes.get('tel')
            password = donnes.get('pwd')
            confirm_password = donnes.get('conf_pwd')

            if password != confirm_password:
                return "Les mots de passe ne correspondent pas. Veuillez réessayer."

            hashed_password = hashlib.md5(password.encode()).hexdigest()
            cursor = mysql.connection.cursor()

            # Vérifier si l'email est déjà utilisé
            cursor.execute("SELECT * FROM admin WHERE email_admin = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("Cet email est déjà utilisé. Veuillez en utiliser un autre.", "danger")
                return redirect(request.url)

            try:
                cursor.execute("""INSERT INTO admin (nom_complet, email_admin, numero_telephone, password)
                                VALUES (%s, %s, %s, %s)""",
                               (nom_complet, email, numero_telephone, hashed_password))
                mysql.connection.commit()
                # Envoi de l'email de confirmation (HTML bien design)

                flash("Compte créé avec succès. Un email de confirmation a été envoyé.", "success")
                return redirect(url_for('liste_admin'))

            except Exception as e:
                return f"Erreur lors de l'inscription : {e}"

        return render_template('admin/connexion/signup.html', loggedIn=loggedIn, firstName=firstName, role = "admin")
    else:
        return redirect(url_for('login'))

#inscription du docteur
@app.route("/signup_docteur", methods=['POST', 'GET'])
def signup_doctor():
    if 'email_admin' in session:
        loggedIn, firstName = getLogin('email_admin', 'admin')
        if request.method == 'POST':
            donnes = request.form
            email = donnes.get('email')
            password = donnes.get('pwd')
            confirm_password = donnes.get('conf_pwd')

            if password != confirm_password:
                return "Les mots de passe ne correspondent pas. Veuillez réessayer."

            hashed_password = hashlib.md5(password.encode()).hexdigest()
            cursor = mysql.connection.cursor()

            # Vérifier si l'email est déjà utilisé
            cursor.execute("SELECT * FROM doctor WHERE email_doctor = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("Cet email est déjà utilisé. Veuillez en utiliser un autre.", "danger")
                return redirect(request.url)

            try:

                cursor.execute("""INSERT INTO doctor (email_doctor, password)
                                VALUES (%s, %s)""",
                               (email, hashed_password))
                mysql.connection.commit()

                # Envoi de l'email pour informer le personnel
                try:
                    envoie_email_connection(email, password)
                except Exception as e:
                    print(e)

                flash("Compte créé avec succès. Un email de confirmation a été envoyé.", "success")
                return redirect(url_for('liste_docteur_admin'))

            except Exception as e:
                return f"Erreur lors de l'inscription : {e}"

        return render_template('admin/connexion/signup.html', loggedIn=loggedIn, firstName=firstName, role = "doctor")
    else:
        return redirect(url_for('login'))

# #inscription du patient
@app.route("/signup_patient_admin", methods=['GET', 'POST'])
def signup_patient_admin():
    def signup_patient_admin():
        if 'email_admin' in session:
            loggedIn, firstName = getLogin('email_admin', 'admin')
            if request.method == 'POST':
                donnes = request.form
                email = donnes.get('email')
                password = donnes.get('pwd')
                confirm_password = donnes.get('conf_pwd')

                if password != confirm_password:
                    return "Les mots de passe ne correspondent pas. Veuillez réessayer."

                hashed_password = hashlib.md5(password.encode()).hexdigest()
                cursor = mysql.connection.cursor()

                # Vérifier si l'email est déjà utilisé
                cursor.execute("SELECT * FROM patient WHERE email_patient = %s", (email,))
                existing_user = cursor.fetchone()

                if existing_user:
                    flash("Cet email est déjà utilisé. Veuillez en utiliser un autre.", "danger")
                    return redirect(request.url)

                try:
                    cursor.execute("""INSERT INTO patient (email_patient, password)
                                      VALUES (%s, %s)""",
                                   (email, hashed_password))
                    mysql.connection.commit()

                    # Envoi de l'email pour informer le patient
                    try:
                        envoie_email_connection(email, password)
                    except Exception as e:
                        print(e)

                    flash("Compte créé avec succès. Un email de confirmation a été envoyé.", "success")
                    return redirect(url_for('index'))

                except Exception as e:
                    return f"Erreur lors de l'inscription : {e}"

            return render_template('admin/connexion/signup.html', loggedIn=loggedIn, firstName=firstName,
                                   role="patient")
        else:
            return redirect(url_for('login'))


@app.route("/signup_patient", methods=['GET', 'POST'])
def signup_patient():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['pwd']
        confirm_password = request.form['conf_pwd']

        if password != confirm_password:
            return "Les mots de passe ne correspondent pas. Veuillez réessayer."

        hashed_password = hashlib.md5(password.encode()).hexdigest()
        cursor = mysql.connection.cursor()

        cursor.execute("SELECT * FROM patient WHERE email_patient = %s", (email,))
        existing_user = cursor.fetchone()


        if existing_user:
            flash("Cet email est déjà utilisé. Veuillez en utiliser un autre.", "danger")
            return redirect(request.url)

        try:
            cursor.execute("""INSERT INTO patient (email_patient, password) 
                            VALUES (%s, %s)""",
                           ( email, hashed_password))

            mysql.connection.commit()
            # Envoi de l'email de confirmation (HTML bien design)

            flash("Compte créé avec succès. Un email de confirmation a été envoyé.", "success")
            return redirect(url_for('index_patient'))

        except Exception as e:

            return f"Erreur lors de l'inscription : {e}"

    return render_template('patient/connexion/signup_patient.html')

# inscription du secretaire medical
@app.route("/signup_secretaire_medical", methods=['POST', 'GET'])
def signup_secretaire():
    if 'email_admin' in session:
        loggedIn, firstName = getLogin('email_admin', 'admin')
        if request.method == 'POST':
            donnes = request.form
            email = donnes.get('email')
            password = donnes.get('pwd')
            confirm_password = donnes.get('conf_pwd')

            if password != confirm_password:
                return "Les mots de passe ne correspondent pas. Veuillez réessayer."

            hashed_password = hashlib.md5(password.encode()).hexdigest()
            cursor = mysql.connection.cursor()

            # Vérifier si l'email est déjà utilisé
            cursor.execute("SELECT * FROM secretaire_medicale WHERE email_secretaire = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("Cet email est déjà utilisé. Veuillez en utiliser un autre.", "danger")
                return redirect(request.url)

            try:
                cursor.execute("""INSERT INTO secretaire_medicale (email_secretaire, password)
                                  VALUES (%s, %s)""",
                               (email, hashed_password))
                mysql.connection.commit()

                # Envoi de l'email pour informer le personnel
                try:
                    envoie_email_connection(email, password)
                except Exception as e:
                    print(e)

                flash("Compte créé avec succès. Un email de confirmation a été envoyé.", "success")
                return redirect(url_for('index'))

            except Exception as e:
                return f"Erreur lors de l'inscription : {e}"

        return render_template('admin/connexion/signup.html', loggedIn=loggedIn, firstName=firstName, role="secretaire")
    else:
        return redirect(url_for('login'))


@app.route("/signup_ambulancier", methods=['GET', 'POST'])
def signup_ambulancier():
    if 'email_admin' in session:
        loggedIn, firstName = getLogin('email_admin', 'admin')
        if request.method == 'POST':
            donnes = request.form
            email = donnes.get('email')
            password = donnes.get('pwd')
            confirm_password = donnes.get('conf_pwd')

            if password != confirm_password:
                return "Les mots de passe ne correspondent pas. Veuillez réessayer."

            hashed_password = hashlib.md5(password.encode()).hexdigest()
            cursor = mysql.connection.cursor()

            # Vérifier si l'email est déjà utilisé
            cursor.execute("SELECT * FROM ambulancier WHERE email_ambulancier = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("Cet email est déjà utilisé. Veuillez en utiliser un autre.", "danger")
                return redirect(request.url)

            try:
                cursor.execute("""INSERT INTO ambulancier (email_ambulancier, password)
                                  VALUES (%s, %s)""",
                               (email, hashed_password))
                mysql.connection.commit()

                # Envoi de l'email pour informer l'ambulancier
                try:
                    envoie_email_connection(email, password)
                except Exception as e:
                    print(e)

                flash("Compte créé avec succès. Un email de confirmation a été envoyé.", "success")
                return redirect(url_for('index_admin'))

            except Exception as e:
                return f"Erreur lors de l'inscription : {e}"

        return render_template('admin/connexion/signup.html', loggedIn=loggedIn, firstName=firstName, role="ambulancier")
    else:
        return redirect(url_for('login'))


# inscription du caissier
@app.route("/signup_ambulancier", methods=['POST', 'GET'])
def signup_caissier():
    if 'email_admin' in session:
        loggedIn, firstName = getLogin('email_admin', 'admin')
        if request.method == 'POST':
            donnes = request.form
            email = donnes.get('email')
            password = donnes.get('pwd')
            confirm_password = donnes.get('conf_pwd')

            if password != confirm_password:
                return "Les mots de passe ne correspondent pas. Veuillez réessayer."

            hashed_password = hashlib.md5(password.encode()).hexdigest()
            cursor = mysql.connection.cursor()

            # Vérifier si l'email est déjà utilisé
            cursor.execute("SELECT * FROM caissier WHERE email_caissier = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("Cet email est déjà utilisé. Veuillez en utiliser un autre.", "danger")
                return redirect(request.url)

            try:
                cursor.execute("""INSERT INTO caissier (email_caissier, password)
                                  VALUES (%s, %s)""",
                               (email, hashed_password))
                mysql.connection.commit()

                # Envoi de l'email pour informer le caissier
                try:
                    envoie_email_connection(email, password)
                except Exception as e:
                    print(e)

                flash("Compte créé avec succès. Un email de confirmation a été envoyé.", "success")
                return redirect(url_for('index_admin'))

            except Exception as e:
                return f"Erreur lors de l'inscription : {e}"

        return render_template('admin/connexion/signup.html', loggedIn=loggedIn, firstName=firstName, role="caissier")
    else:
        return redirect(url_for('login'))


# inscription du gestionnaire_logistique
@app.route("/signup_gestionnaire_logistique", methods=['POST', 'GET'])
def signup_logistique():
    if 'email_admin' in session:
        loggedIn, firstName = getLogin('email_admin', 'admin')
        if request.method == 'POST':
            donnes = request.form
            email = donnes.get('email')
            password = donnes.get('pwd')
            confirm_password = donnes.get('conf_pwd')

            if password != confirm_password:
                return "Les mots de passe ne correspondent pas. Veuillez réessayer."

            hashed_password = hashlib.md5(password.encode()).hexdigest()
            cursor = mysql.connection.cursor()

            # Vérifier si l'email est déjà utilisé
            cursor.execute("SELECT * FROM gestionnaire_logistique WHERE email_logistique = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("Cet email est déjà utilisé. Veuillez en utiliser un autre.", "danger")
                return redirect(request.url)

            try:
                cursor.execute("""INSERT INTO gestionnaire_logistique (email_logistique, password)
                                  VALUES (%s, %s)""",
                               (email, hashed_password))
                mysql.connection.commit()

                # Envoi de l'email pour informer le gestionnaire logistique
                try:
                    envoie_email_connection(email, password)
                except Exception as e:
                    print(e)

                flash("Compte créé avec succès. Un email de confirmation a été envoyé.", "success")
                return redirect(url_for('index_admin'))

            except Exception as e:
                return f"Erreur lors de l'inscription : {e}"

        return render_template('admin/connexion/signup.html', loggedIn=loggedIn, firstName=firstName, role="logistique")
    else:
        return redirect(url_for('login'))


#inscription du gestionnaire_stock
@app.route("/signup_gestionnaire_stock", methods=['POST', 'GET'])
def signup_stock():
    if 'email_admin' in session:
        loggedIn, firstName = getLogin('email_admin', 'admin')
        if request.method == 'POST':
            donnes = request.form
            email = donnes.get('email')
            password = donnes.get('pwd')
            confirm_password = donnes.get('conf_pwd')

            if password != confirm_password:
                return "Les mots de passe ne correspondent pas. Veuillez réessayer."

            hashed_password = hashlib.md5(password.encode()).hexdigest()
            cursor = mysql.connection.cursor()

            # Vérifier si l'email est déjà utilisé
            cursor.execute("SELECT * FROM gestionnaire_stock WHERE email_stock = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("Cet email est déjà utilisé. Veuillez en utiliser un autre.", "danger")
                return redirect(request.url)

            try:
                cursor.execute("""INSERT INTO gestionnaire_stock (email_stock, password)
                                  VALUES (%s, %s)""",
                               (email, hashed_password))
                mysql.connection.commit()

                # Envoi de l'email pour informer le gestionnaire de stock
                try:
                    envoie_email_connection(email, password)
                except Exception as e:
                    print(e)

                flash("Compte créé avec succès. Un email de confirmation a été envoyé.", "success")
                return redirect(url_for('index'))

            except Exception as e:
                return f"Erreur lors de l'inscription : {e}"

        return render_template('admin/connexion/signup.html', loggedIn=loggedIn, firstName=firstName, role="stock")
    else:
        return redirect(url_for('login'))


#inscription du infirmier
@app.route("/signup_infirmier", methods=['POST', 'GET'])
def signup_infirmier():
    if 'email_admin' in session:
        loggedIn, firstName = getLogin('email_admin', 'admin')
        if request.method == 'POST':
            donnes = request.form
            email = donnes.get('email')
            password = donnes.get('pwd')
            confirm_password = donnes.get('conf_pwd')

            if password != confirm_password:
                return "Les mots de passe ne correspondent pas. Veuillez réessayer."

            hashed_password = hashlib.md5(password.encode()).hexdigest()
            cursor = mysql.connection.cursor()

            # Vérifier si l'email est déjà utilisé
            cursor.execute("SELECT * FROM infirmier WHERE email_infirmier = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("Cet email est déjà utilisé. Veuillez en utiliser un autre.", "danger")
                return redirect(request.url)

            try:
                cursor.execute("""INSERT INTO infirmier (email_infirmier, password)
                                  VALUES (%s, %s)""",
                               (email, hashed_password))
                mysql.connection.commit()

                # Envoi de l'email pour informer l'infirmier
                try:
                    envoie_email_connection(email, password)
                except Exception as e:
                    print(e)

                flash("Compte créé avec succès. Un email de confirmation a été envoyé.", "success")
                return redirect(url_for('index'))

            except Exception as e:
                return f"Erreur lors de l'inscription : {e}"

        return render_template('admin/connexion/signup.html', loggedIn=loggedIn, firstName=firstName, role="infirmier")
    else:
        return redirect(url_for('login'))


#inscription du interne_medecine
@app.route("/signup_infirmier", methods=['POST', 'GET'])
def signup_interne():
    if 'email_admin' in session:
        loggedIn, firstName = getLogin('email_admin', 'admin')
        if request.method == 'POST':
            donnes = request.form
            email = donnes.get('email')
            password = donnes.get('pwd')
            confirm_password = donnes.get('conf_pwd')

            if password != confirm_password:
                return "Les mots de passe ne correspondent pas. Veuillez réessayer."

            hashed_password = hashlib.md5(password.encode()).hexdigest()
            cursor = mysql.connection.cursor()

            # Vérifier si l'email est déjà utilisé
            cursor.execute("SELECT * FROM interne_medecine WHERE email_interne = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("Cet email est déjà utilisé. Veuillez en utiliser un autre.", "danger")
                return redirect(request.url)

            try:
                cursor.execute("""INSERT INTO interne_medecine (email_interne, password)
                                  VALUES (%s, %s)""",
                               (email, hashed_password))
                mysql.connection.commit()

                # Envoi de l'email pour informer l'interne
                try:
                    envoie_email_connection(email, password)
                except Exception as e:
                    print(e)

                flash("Compte créé avec succès. Un email de confirmation a été envoyé.", "success")
                return redirect(url_for('index'))

            except Exception as e:
                return f"Erreur lors de l'inscription : {e}"

        return render_template('admin/connexion/signup.html', loggedIn=loggedIn, firstName=firstName, role="interne")
    else:
        return redirect(url_for('login'))






#modifier renistaliser mot de pass
@app.route("/Renistialiser_mot_de_passe")
def reset_pasword():
    return render_template("admin/connexion/reset_password.html")

# mot de pass oublier
@app.route("/mot_de_passe_oublié")
def forgot_password():
    return render_template("admin/connexion/forgot_password.html")



@app.route("/list_patient")
def list_patient():
    return render_template("admin/liste_des_utilisateur/list_patient.html")

@app.route("/list_doctor")
def list_doctor():
    return  render_template("admin/liste_des_utilisateur/list_doctor.html")

@app.route("/list_admin")
def list_admin():
    return  render_template("admin/liste_des_utilisateur/list_admin.html")

@app.route("/list_personnel")
def list_personnel():
    return  render_template("admin/liste_des_utilisateur/list_personnel.html")


if __name__ == "__main__":
    app.run(debug=True)