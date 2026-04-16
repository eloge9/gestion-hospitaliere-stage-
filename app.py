"""
Application Flask modulaire - Gestion Hospitalière
"""
from flask import Flask
from flask_mysqldb import MySQL
from flask_mail import Mail
from credentials import *

# Import des modules
from modules.auth import init_auth
from modules.admin import init_admin
from modules.patient import init_patient
from modules.docteur import init_docteur
from modules.pharmacie import init_pharmacie
from modules.facturation import init_facturation

# Initialisation de l'application
app = Flask(__name__)

# Configuration base de données
app.config['SECRET_KEY'] = my_token
app.config['MYSQL_HOST'] = my_host
app.config['MYSQL_USER'] = my_user
app.config['MYSQL_PASSWORD'] = my_password
app.config['MYSQL_DB'] = my_db
app.config['MYSQL_CURSORCLASS'] = my_CURSORCLASS

# Configuration email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = my_email
app.config['MAIL_PASSWORD'] = my_password_generer
app.config['MAIL_DEFAULT_SENDER'] = ('Gestion Hospitaliere', 'elogegomina@gmail.com')

# Initialisation des extensions
mail = Mail(app)
mysql = MySQL()
mysql.init_app(app)
app.secret_key = my_secret_key

init_auth(app, mysql)
init_admin(app, mysql, mail)
init_patient(app, mysql, mail)
init_docteur(app, mysql)
init_pharmacie(app, mysql)
init_facturation(app, mysql)

if __name__ == "__main__":
    app.run(debug=True)