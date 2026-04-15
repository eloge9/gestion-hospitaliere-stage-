"""
Module docteur - routes pour la gestion des docteurs
"""
import MySQLdb.cursors
from flask import render_template, redirect, url_for, flash
from .utils import login_required


def init_docteur(app, mysql):
    """Initialise les routes docteur"""
    
    @app.route("/admin/liste_docteur")
    @login_required("admin")
    def liste_docteur_admin():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM doctor")
        doctors = cursor.fetchall()
        return render_template("admin/gestion_docteur/Liste_docteur.html", doctors=doctors)

    @app.route('/admin/supprimer_docteur/<int:id>')
    @login_required("admin")
    def supprimer_docteur(id):
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM doctor WHERE id = %s", (id,))
        mysql.connection.commit()
        flash("Médecin supprimé avec succès.", "success")
        return redirect(url_for('liste_docteur_admin'))
