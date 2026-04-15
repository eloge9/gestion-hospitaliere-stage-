"""
Module admin - routes pour la gestion des administrateurs
"""
import MySQLdb.cursors
import hashlib
from flask import render_template, redirect, url_for, request, flash, session
from .utils import login_required, getLogin, envoie_email_connection


def init_admin(app, mysql, mail):
    """Initialise les routes admin"""
    
    @app.route("/admin")
    @login_required("admin")
    def index():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Récupère l'email de l'admin connecté depuis la session
        email_admin = session.get('email_admin')

        cursor.execute("SELECT nom, prenom FROM admin WHERE email_admin = %s", (email_admin,))
        admin = cursor.fetchone()
        cursor.close()

        if admin:
            session['nom'] = admin['nom']
            session['prenom'] = admin['prenom']
        else:
            session['nom'] = None
            session['prenom'] = None
        return render_template("admin/index_admin.html")

    @app.route('/admin/liste_admin')
    @login_required("admin")
    def liste_admin():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT id, nom, prenom, email_admin, numero_telephone FROM admin")
        admins = cursor.fetchall()
        cursor.close()
        return render_template("admin/gestion_admin/liste_admin.html", admins=admins)

    @app.route('/admin/supprimer/<int:id>', methods=['GET', 'POST'])
    @login_required("admin")
    def supprimer_admin(id):
        cursor = mysql.connection.cursor()
        try:
            # Supprimer l'admin avec l'identifiant donné
            cursor.execute("DELETE FROM admin WHERE id = %s", (id,))
            mysql.connection.commit()
            flash("Administrateur supprimé avec succès.", "success")
        except Exception as e:
            flash("Erreur lors de la suppression : " + str(e), "danger")
        finally:
            cursor.close()

        # Redirection vers la liste des admins (ou une autre page)
        return redirect(url_for('liste_admin'))

    @app.route("/modifier-admin/<int:id>", methods=["GET", "POST"])
    @login_required("admin")
    def modifier_admin(id):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        if request.method == "POST":
            nom = request.form.get('nom')
            prenom = request.form.get('prenom')
            email = request.form['email_admin']
            numero_telephone = request.form['numero_telephone']

            # Exécution de la requête UPDATE
            cursor.execute("""
                UPDATE admin SET nom=%s, prenom=%s, email_admin=%s, numero_telephone=%s 
                WHERE id=%s
            """, (nom, prenom, email, numero_telephone, id))

            mysql.connection.commit()
            flash("Les informations ont été modifiées avec succès.", "success")
            return redirect(url_for('liste_admin'))

        # Sinon (GET), on affiche les infos actuelles dans le formulaire
        cursor.execute("SELECT * FROM admin WHERE id = %s", (id,))
        admin = cursor.fetchone()
        cursor.close()
        
        # Debug: afficher les données récupérées
        print(f"Admin récupéré: {admin}")
        
        return render_template("admin/gestion_admin/modifier_admin.html", admin=admin)

    @app.route('/admin/voir/<int:id>')
    @login_required("admin")
    def voir_admin(id):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT id, nom, prenom, email_admin, numero_telephone, date_inscription FROM admin WHERE id = %s", (id,))
        admin = cursor.fetchone()  # Un seul admin
        cursor.close()

        if not admin:
            flash("Administrateur introuvable.", "warning")
            return redirect(url_for('liste_admin'))

        return render_template("admin/gestion_admin/profile_admin.html", admin=admin)

    @app.route("/signup_admin", methods=['GET', 'POST'])
    @login_required("admin")
    def signup():
        if 'email_admin' in session:
            loggedIn, firstName = getLogin('email_admin', 'admin', mysql)
            if request.method == 'POST':
                donnes = request.form
                name = (donnes.get('name') or '').strip()
                prenom = (donnes.get('prenom') or '').strip()
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
                    cursor.execute("""INSERT INTO admin (nom, prenom, email_admin, numero_telephone, password)
                                    VALUES (%s, %s, %s, %s, %s)""",
                                   (name, prenom, email, numero_telephone, hashed_password))
                    mysql.connection.commit()

                    flash("Compte créé avec succès. Un email de confirmation a été envoyé.", "success")
                    return redirect(url_for('liste_admin'))

                except Exception as e:
                    return f"Erreur lors de l'inscription : {e}"

            return render_template('admin/connexion/signup.html', loggedIn=loggedIn, firstName=firstName, role="admin")
        else:
            return redirect(url_for('login'))

    @app.route('/admin/verifier_admin', methods=['POST'])
    @login_required("admin")
    def verifier_admin():
        """Vérifier si un admin existe déjà"""
        if 'email_admin' in session:
            email = request.form.get('email')
            cursor = mysql.connection.cursor()
            
            try:
                cursor.execute("SELECT COUNT(*) FROM admin WHERE email_admin = %s", (email,))
                count = cursor.fetchone()[0]
                cursor.close()
                
                if count > 0:
                    return {'exists': True, 'message': 'Cet admin existe déjà'}
                else:
                    return {'exists': False, 'message': 'Admin disponible'}
                    
            except Exception as e:
                return {'exists': False, 'message': f'Erreur: {str(e)}'}
        else:
            return redirect(url_for('login'))
