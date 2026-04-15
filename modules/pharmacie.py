import re
from flask import render_template, request, redirect, url_for, flash, session
from modules.utils import login_required, getLogin
import MySQLdb

def init_pharmacie(app, mysql):
    """
    Initialise toutes les routes pour la gestion de pharmacie
    """
    
    # ========================================
    # ROUTES CATÉGORIES DE MÉDICAMENTS
    # ========================================
    
    @app.route("/admin/pharmacie/categories")
    @login_required("admin")
    def liste_categories_pharmacie():
        """Liste de toutes les catégories de médicaments"""
        if 'email_admin' in session:
            loggedIn, firstName = getLogin('email_admin', 'admin', mysql)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            cursor.execute("""
                SELECT c.*, COUNT(m.id) as nombre_medicaments
                FROM categorie_medicament c
                LEFT JOIN medicament m ON c.id = m.categorie_id
                GROUP BY c.id
                ORDER BY c.nom
            """)
            categories = cursor.fetchall()
            
            return render_template('admin/gestion_pharmacie/liste_categories.html',
                                 categories=categories, 
                                 loggedIn=loggedIn, firstName=firstName)
        else:
            return redirect(url_for('login'))
    
    @app.route("/admin/pharmacie/categorie/ajouter", methods=['GET', 'POST'])
    @login_required("admin")
    def ajouter_categorie_pharmacie():
        """Ajouter une nouvelle catégorie de médicament"""
        if 'email_admin' in session:
            loggedIn, firstName = getLogin('email_admin', 'admin', mysql)
            
            if request.method == 'POST':
                nom = request.form.get('nom')
                description = request.form.get('description', '')
                
                if not nom:
                    flash("Le nom de la catégorie est obligatoire.", "danger")
                    return redirect(request.url)
                
                cursor = mysql.connection.cursor()
                
                try:
                    # Vérifier si la catégorie existe déjà
                    cursor.execute("SELECT * FROM categorie_medicament WHERE nom = %s", (nom,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        flash("Cette catégorie existe déjà.", "danger")
                        return redirect(request.url)
                    
                    # Insérer la nouvelle catégorie
                    cursor.execute("""
                        INSERT INTO categorie_medicament (nom, description)
                        VALUES (%s, %s)
                    """, (nom, description))
                    
                    mysql.connection.commit()
                    flash("Catégorie ajoutée avec succès!", "success")
                    return redirect(url_for('liste_categories_pharmacie'))
                    
                except Exception as e:
                    mysql.connection.rollback()
                    flash(f"Erreur lors de l'ajout: {e}", "danger")
                    return redirect(request.url)
            
            return render_template('admin/gestion_pharmacie/ajouter_categorie.html',
                                 loggedIn=loggedIn, firstName=firstName)
        else:
            return redirect(url_for('login'))
    
    @app.route("/admin/pharmacie/categorie/<int:categorie_id>/modifier", methods=['GET', 'POST'])
    @login_required("admin")
    def modifier_categorie_pharmacie(categorie_id):
        """Modifier une catégorie de médicament"""
        if 'email_admin' in session:
            loggedIn, firstName = getLogin('email_admin', 'admin', mysql)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Récupérer la catégorie
            cursor.execute("SELECT * FROM categorie_medicament WHERE id = %s", (categorie_id,))
            categorie = cursor.fetchone()
            
            if not categorie:
                flash("Catégorie non trouvée.", "danger")
                return redirect(url_for('liste_categories_pharmacie'))
            
            if request.method == 'POST':
                nom = request.form.get('nom')
                description = request.form.get('description', '')
                
                if not nom:
                    flash("Le nom de la catégorie est obligatoire.", "danger")
                    return redirect(request.url)
                
                try:
                    # Vérifier si une autre catégorie avec ce nom existe
                    cursor.execute("SELECT * FROM categorie_medicament WHERE nom = %s AND id != %s", 
                                 (nom, categorie_id))
                    existing = cursor.fetchone()
                    
                    if existing:
                        flash("Une autre catégorie avec ce nom existe déjà.", "danger")
                        return redirect(request.url)
                    
                    # Mettre à jour la catégorie
                    cursor.execute("""
                        UPDATE categorie_medicament 
                        SET nom = %s, description = %s
                        WHERE id = %s
                    """, (nom, description, categorie_id))
                    
                    mysql.connection.commit()
                    flash("Catégorie modifiée avec succès!", "success")
                    return redirect(url_for('liste_categories_pharmacie'))
                    
                except Exception as e:
                    mysql.connection.rollback()
                    flash(f"Erreur lors de la modification: {e}", "danger")
                    return redirect(request.url)
            
            return render_template('admin/gestion_pharmacie/modifier_categorie.html',
                                 categorie=categorie,
                                 loggedIn=loggedIn, firstName=firstName)
        else:
            return redirect(url_for('login'))
    
    @app.route("/admin/pharmacie/categorie/<int:categorie_id>/supprimer", methods=['GET', 'POST'])
    @login_required("admin")
    def supprimer_categorie_pharmacie(categorie_id):
        """Supprimer une catégorie de médicament"""
        if 'email_admin' in session:
            cursor = mysql.connection.cursor()
            
            try:
                # Vérifier si la catégorie existe
                cursor.execute("SELECT nom FROM categorie_medicament WHERE id = %s", (categorie_id,))
                categorie = cursor.fetchone()
                
                if not categorie:
                    flash("Catégorie non trouvée.", "danger")
                    return redirect(url_for('liste_categories_pharmacie'))
                
                # Vérifier si des médicaments sont associés
                cursor.execute("SELECT COUNT(*) FROM medicament WHERE categorie_id = %s", (categorie_id,))
                count = cursor.fetchone()[0]
                
                if count > 0:
                    flash(f"Impossible de supprimer cette catégorie. {count} médicament(s) y sont associé(s).", "danger")
                    return redirect(url_for('liste_categories_pharmacie'))
                
                # Supprimer la catégorie
                cursor.execute("DELETE FROM categorie_medicament WHERE id = %s", (categorie_id,))
                mysql.connection.commit()
                
                flash(f"Catégorie '{categorie[0]}' supprimée avec succès!", "success")
                return redirect(url_for('liste_categories_pharmacie'))
                
            except Exception as e:
                mysql.connection.rollback()
                flash(f"Erreur lors de la suppression: {e}", "danger")
                return redirect(url_for('liste_categories_pharmacie'))
        else:
            return redirect(url_for('login'))
    
    # ========================================
    # ROUTES MÉDICAMENTS
    # ========================================
    
    @app.route("/admin/pharmacie/medicaments")
    @login_required("admin")
    def liste_medicaments_pharmacie():
        """Liste de tous les médicaments"""
        if 'email_admin' in session:
            loggedIn, firstName = getLogin('email_admin', 'admin', mysql)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            cursor.execute("""
                SELECT m.*, c.nom as categorie_nom,
                       CASE 
                           WHEN m.quantite_stock <= m.seuil_alerte THEN 'alerte'
                           WHEN m.quantite_stock <= m.seuil_alerte * 2 THEN 'attention'
                           ELSE 'normal'
                       END as statut_stock
                FROM medicament m
                LEFT JOIN categorie_medicament c ON m.categorie_id = c.id
                ORDER BY m.nom
            """)
            medicaments = cursor.fetchall()
            
            return render_template('admin/gestion_pharmacie/liste_medicaments.html',
                                 medicaments=medicaments, 
                                 loggedIn=loggedIn, firstName=firstName)
        else:
            return redirect(url_for('login'))
    
    @app.route("/admin/pharmacie/medicament/ajouter", methods=['GET', 'POST'])
    @login_required("admin")
    def ajouter_medicament_pharmacie():
        """Ajouter un nouveau médicament"""
        if 'email_admin' in session:
            loggedIn, firstName = getLogin('email_admin', 'admin', mysql)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            if request.method == 'POST':
                # Récupérer les données du formulaire
                nom = request.form.get('nom')
                description = request.form.get('description', '')
                categorie_id = request.form.get('categorie_id')
                forme = request.form.get('forme', '')
                dosage = request.form.get('dosage', '')
                prix_unitaire = request.form.get('prix_unitaire', 0)
                quantite_stock = request.form.get('quantite_stock', 0)
                seuil_alerte = request.form.get('seuil_alerte', 5)
                date_expiration = request.form.get('date_expiration', '')
                
                # Validation
                if not nom or not categorie_id:
                    flash("Le nom et la catégorie sont obligatoires.", "danger")
                    return redirect(request.url)
                
                try:
                    # Vérifier si le médicament existe déjà
                    cursor.execute("SELECT * FROM medicament WHERE nom = %s AND categorie_id = %s", 
                                 (nom, categorie_id))
                    existing = cursor.fetchone()
                    
                    if existing:
                        flash("Ce médicament existe déjà dans cette catégorie.", "danger")
                        return redirect(request.url)
                    
                    # Insérer le médicament
                    cursor.execute("""
                        INSERT INTO medicament 
                        (nom, description, categorie_id, forme, dosage, prix_unitaire, 
                         quantite_stock, seuil_alerte, date_expiration)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (nom, description, categorie_id, forme, dosage, 
                          float(prix_unitaire), int(quantite_stock), int(seuil_alerte), 
                          date_expiration if date_expiration else None))
                    
                    mysql.connection.commit()
                    flash("Médicament ajouté avec succès!", "success")
                    return redirect(url_for('liste_medicaments_pharmacie'))
                    
                except Exception as e:
                    mysql.connection.rollback()
                    flash(f"Erreur lors de l'ajout: {e}", "danger")
                    return redirect(request.url)
            
            # Récupérer les catégories pour le select
            cursor.execute("SELECT * FROM categorie_medicament ORDER BY nom")
            categories = cursor.fetchall()
            
            return render_template('admin/gestion_pharmacie/ajouter_medicament.html',
                                 categories=categories,
                                 loggedIn=loggedIn, firstName=firstName)
        else:
            return redirect(url_for('login'))
    
    @app.route("/admin/pharmacie/medicament/<int:medicament_id>")
    @login_required("admin")
    def voir_medicament_pharmacie(medicament_id):
        """Voir les détails d'un médicament"""
        if 'email_admin' in session:
            loggedIn, firstName = getLogin('email_admin', 'admin', mysql)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Récupérer le médicament avec sa catégorie
            cursor.execute("""
                SELECT m.*, c.nom as categorie_nom
                FROM medicament m
                LEFT JOIN categorie_medicament c ON m.categorie_id = c.id
                WHERE m.id = %s
            """, (medicament_id,))
            medicament = cursor.fetchone()
            
            if not medicament:
                flash("Médicament non trouvé.", "danger")
                return redirect(url_for('liste_medicaments_pharmacie'))
            
            return render_template('admin/gestion_pharmacie/detail_medicament.html',
                                 medicament=medicament,
                                 loggedIn=loggedIn, firstName=firstName)
        else:
            return redirect(url_for('login'))
    
    @app.route("/admin/pharmacie/medicament/<int:medicament_id>/modifier", methods=['GET', 'POST'])
    @login_required("admin")
    def modifier_medicament_pharmacie(medicament_id):
        """Modifier un médicament"""
        if 'email_admin' in session:
            loggedIn, firstName = getLogin('email_admin', 'admin', mysql)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Récupérer le médicament
            cursor.execute("""
                SELECT m.*, c.nom as categorie_nom
                FROM medicament m
                LEFT JOIN categorie_medicament c ON m.categorie_id = c.id
                WHERE m.id = %s
            """, (medicament_id,))
            medicament = cursor.fetchone()
            
            if not medicament:
                flash("Médicament non trouvé.", "danger")
                return redirect(url_for('liste_medicaments_pharmacie'))
            
            if request.method == 'POST':
                # Récupérer les données du formulaire
                nom = request.form.get('nom')
                description = request.form.get('description', '')
                categorie_id = request.form.get('categorie_id')
                forme = request.form.get('forme', '')
                dosage = request.form.get('dosage', '')
                prix_unitaire = request.form.get('prix_unitaire', 0)
                quantite_stock = request.form.get('quantite_stock', 0)
                seuil_alerte = request.form.get('seuil_alerte', 5)
                date_expiration = request.form.get('date_expiration', '')
                
                # Validation
                if not nom or not categorie_id:
                    flash("Le nom et la catégorie sont obligatoires.", "danger")
                    return redirect(request.url)
                
                try:
                    # Vérifier si un autre médicament avec ce nom existe dans cette catégorie
                    cursor.execute("SELECT * FROM medicament WHERE nom = %s AND categorie_id = %s AND id != %s", 
                                 (nom, categorie_id, medicament_id))
                    existing = cursor.fetchone()
                    
                    if existing:
                        flash("Un autre médicament avec ce nom existe déjà dans cette catégorie.", "danger")
                        return redirect(request.url)
                    
                    # Mettre à jour le médicament
                    cursor.execute("""
                        UPDATE medicament 
                        SET nom = %s, description = %s, categorie_id = %s, forme = %s, 
                            dosage = %s, prix_unitaire = %s, quantite_stock = %s, 
                            seuil_alerte = %s, date_expiration = %s
                        WHERE id = %s
                    """, (nom, description, categorie_id, forme, dosage, 
                          float(prix_unitaire), int(quantite_stock), int(seuil_alerte), 
                          date_expiration if date_expiration else None, medicament_id))
                    
                    mysql.connection.commit()
                    flash("Médicament modifié avec succès!", "success")
                    return redirect(url_for('liste_medicaments_pharmacie'))
                    
                except Exception as e:
                    mysql.connection.rollback()
                    flash(f"Erreur lors de la modification: {e}", "danger")
                    return redirect(request.url)
            
            # Récupérer les catégories pour le select
            cursor.execute("SELECT * FROM categorie_medicament ORDER BY nom")
            categories = cursor.fetchall()
            
            return render_template('admin/gestion_pharmacie/modifier_medicament.html',
                                 medicament=medicament,
                                 categories=categories,
                                 loggedIn=loggedIn, firstName=firstName)
        else:
            return redirect(url_for('login'))
    
    @app.route("/admin/pharmacie/medicament/<int:medicament_id>/supprimer", methods=['GET', 'POST'])
    @login_required("admin")
    def supprimer_medicament_pharmacie(medicament_id):
        """Supprimer un médicament"""
        if 'email_admin' in session:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            try:
                # Vérifier si le médicament existe
                cursor.execute("SELECT nom FROM medicament WHERE id = %s", (medicament_id,))
                medicament = cursor.fetchone()
                
                if not medicament:
                    flash("Médicament non trouvé.", "danger")
                    return redirect(url_for('liste_medicaments_pharmacie'))
                
                # Supprimer le médicament
                cursor.execute("DELETE FROM medicament WHERE id = %s", (medicament_id))
                mysql.connection.commit()
                
                flash(f"Médicament '{medicament['nom']}' supprimé avec succès!", "success")
                return redirect(url_for('liste_medicaments_pharmacie'))
                
            except Exception as e:
                mysql.connection.rollback()
                flash(f"Erreur lors de la suppression: {e}", "danger")
                return redirect(url_for('liste_medicaments_pharmacie'))
        else:
            return redirect(url_for('login'))
