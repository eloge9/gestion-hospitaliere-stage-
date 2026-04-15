"""
Module d'authentification - routes login, logout, reset password
"""
from flask import render_template, redirect, url_for, request, flash, session
from .utils import is_valid, getLogin


def init_auth(app, mysql):
    """Initialise les routes d'authentification"""
    
    @app.route('/', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['pwd']
            print(email)
            print(password)

            # Vérification des informations
            if is_valid(email, 'email_admin', password, 'admin', mysql):
                session['email_admin'] = email
                session['role'] = 'admin'
                return redirect(url_for('index'))

            else:
                flash('Email ou mot de passe incorrect.', 'danger')
                return redirect(url_for('login'))
        return render_template('admin/connexion/login.html')

    @app.route('/logout')
    def logout():
        # Détection du rôle
        role = None
        nom = session.get('nom', '')

        if 'email_admin' in session:
            role = 'admin'
            session.pop('email_admin')

        session.clear()
        return redirect(url_for('login'))

    @app.route("/Renistialiser_mot_de_passe")
    def reset_pasword():
        return render_template("admin/connexion/reset_password.html")

    @app.route("/mot_de_passe_oublié")
    def forgot_password():
        return render_template("admin/connexion/forgot_password.html")
