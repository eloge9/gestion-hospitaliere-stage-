"""
Module facturation - routes pour la gestion des factures et cycles
"""
import MySQLdb.cursors
from flask import render_template, redirect, url_for, request, flash, session, jsonify
from .utils import login_required, getLogin


def init_facturation(app, mysql):
    """Initialise les routes de facturation"""
    
    def get_patient_cycles(patient_id):
        """Récupère tous les cycles d'un patient"""
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT DISTINCT cycle_id, 
                   MIN(date_facture) as date_debut_cycle,
                   MAX(date_facture) as date_fin_cycle,
                   MAX(statut) as statut_cycle,
                   COUNT(*) as nb_factures,
                   SUM(total_general) as total_cycle
            FROM facture 
            WHERE patient_id = %s 
            GROUP BY cycle_id
            ORDER BY date_debut_cycle DESC
        """, (patient_id,))
        return cursor.fetchall()
    
    def get_cycle_factures(patient_id, cycle_id):
        """Récupère toutes les factures d'un cycle"""
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT * FROM facture 
            WHERE patient_id = %s AND cycle_id = %s
            ORDER BY date_facture
        """, (patient_id, cycle_id))
        factures = cursor.fetchall()
        
        # Récupérer les détails pour chaque facture
        for facture in factures:
            cursor.execute("""
                SELECT * FROM facture_detail 
                WHERE facture_id = %s
                ORDER BY id
            """, (facture['id'],))
            facture['details'] = cursor.fetchall()
        
        return factures
    
    def is_cycle_termine(patient_id, cycle_id):
        """Vérifie si un cycle est terminé"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT statut FROM facture 
            WHERE patient_id = %s AND cycle_id = %s 
            LIMIT 1
        """, (patient_id, cycle_id))
        result = cursor.fetchone()
        return result and result[0] == 'TERMINE'
    
    def calculer_montants_facture(facture_id):
        """Calcule et met à jour les montants d'une facture"""
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Calculer le total général
        cursor.execute("""
            SELECT SUM(montant) as total FROM facture_detail 
            WHERE facture_id = %s
        """, (facture_id,))
        result = cursor.fetchone()
        total_general = result['total'] or 0
        
        # Récupérer les infos du patient et de son assurance
        cursor.execute("""
            SELECT p.*, a.type_assurance, a.pourcentage
            FROM facture f
            JOIN patient p ON f.patient_id = p.id
            LEFT JOIN assurance a ON p.id = a.patient_id
            WHERE f.id = %s
        """, (facture_id,))
        facture_info = cursor.fetchone()
        
        # Calculer les montants
        base_remboursement = total_general
        montant_assurance = 0
        montant_patient = total_general
        
        if facture_info['type_assurance'] and facture_info['pourcentage']:
            montant_assurance = total_general * (facture_info['pourcentage'] / 100)
            montant_patient = total_general - montant_assurance
        
        # Mettre à jour la facture
        cursor.execute("""
            UPDATE facture 
            SET total_general = %s, base_remboursement = %s, 
                montant_assurance = %s, montant_patient = %s
            WHERE id = %s
        """, (total_general, base_remboursement, montant_assurance, montant_patient, facture_id))
        
        mysql.connection.commit()
        return {
            'total_general': total_general,
            'montant_assurance': montant_assurance,
            'montant_patient': montant_patient
        }
    
    def generer_cycle_id(patient_id):
        """Génère un nouvel ID de cycle pour un patient"""
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT COUNT(DISTINCT cycle_id) as nb_cycles 
            FROM facture WHERE patient_id = %s
        """, (patient_id,))
        result = cursor.fetchone()
        nb_cycles = result[0] or 0
        return f"CYCLE_{patient_id}_{nb_cycles + 1}"
    
    # ===== ROUTES POUR LA FACTURATION =====
    
    @app.route("/admin/patient/<int:patient_id>/facturation")
    @login_required("admin")
    def facturation_patient(patient_id):
        """Page principale de facturation du patient"""
        if 'email_admin' in session:
            loggedIn, firstName = getLogin('email_admin', 'admin', mysql)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Récupérer les infos du patient
            cursor.execute("SELECT * FROM patient WHERE id = %s", (patient_id,))
            patient = cursor.fetchone()
            
            if not patient:
                flash("Patient non trouvé.", "danger")
                return redirect(url_for('liste_patient_admin'))
            
            # Récupérer les cycles du patient
            cycles = get_patient_cycles(patient_id)
            
            # Récupérer les assurances du patient
            cursor.execute("SELECT * FROM assurance WHERE patient_id = %s", (patient_id,))
            assurances = cursor.fetchall()
            
            return render_template('admin/gestion_patient/facturation_patient.html',
                             patient=patient, 
                             cycles=cycles,
                             assurances=assurances,
                             loggedIn=loggedIn, firstName=firstName)
        else:
            return redirect(url_for('login'))
    
    @app.route("/admin/patient/<int:patient_id>/cycle/<string:cycle_id>")
    @login_required("admin")
    def details_cycle(patient_id, cycle_id):
        """Détails d'un cycle de facturation"""
        if 'email_admin' in session:
            loggedIn, firstName = getLogin('email_admin', 'admin', mysql)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Vérifier que le cycle appartient au patient
            cursor.execute("""
                SELECT COUNT(*) as count FROM facture 
                WHERE patient_id = %s AND cycle_id = %s
            """, (patient_id, cycle_id))
            if cursor.fetchone()['count'] == 0:
                flash("Cycle non trouvé.", "danger")
                return redirect(url_for('facturation_patient', patient_id=patient_id))
            
            # Récupérer les infos du patient
            cursor.execute("SELECT * FROM patient WHERE id = %s", (patient_id,))
            patient = cursor.fetchone()
            
            # Récupérer les factures du cycle
            factures = get_cycle_factures(patient_id, cycle_id)
            
            # Calculer le total du cycle
            total_cycle = sum(f['total_general'] for f in factures)
            
            # Vérifier si le cycle est terminé
            cycle_termine = is_cycle_termine(patient_id, cycle_id)
            
            return render_template('admin/gestion_patient/details_cycle.html',
                             patient=patient,
                             cycle_id=cycle_id,
                             factures=factures,
                             total_cycle=total_cycle,
                             cycle_termine=cycle_termine,
                             loggedIn=loggedIn, firstName=firstName)
        else:
            return redirect(url_for('login'))
    
    @app.route("/admin/patient/<int:patient_id>/facturation/historique")
    @login_required("admin")
    def historique_facturation(patient_id):
        """Historique complet de facturation du patient"""
        if 'email_admin' in session:
            loggedIn, firstName = getLogin('email_admin', 'admin', mysql)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Récupérer les infos du patient
            cursor.execute("SELECT * FROM patient WHERE id = %s", (patient_id,))
            patient = cursor.fetchone()
            
            if not patient:
                flash("Patient non trouvé.", "danger")
                return redirect(url_for('liste_patient_admin'))
            
            # Récupérer toutes les factures avec détails
            cursor.execute("""
                SELECT f.*, fd.designation, fd.quantite, fd.prix_unitaire, fd.montant as detail_montant,
                       pa.montant_paiement, pa.date_paiement, pa.mode_paiement
                FROM facture f
                LEFT JOIN facture_detail fd ON f.id = fd.facture_id
                LEFT JOIN paiement pa ON f.id = pa.facture_id
                WHERE f.patient_id = %s
                ORDER BY f.date_facture DESC, f.cycle_id, fd.id, pa.date_paiement
            """, (patient_id,))
            factures_data = cursor.fetchall()
            
            # Organiser les données par facture
            factures_organisees = {}
            for row in factures_data:
                facture_id = row['id']
                if facture_id not in factures_organisees:
                    factures_organisees[facture_id] = {
                        'info': {
                            'id': row['id'],
                            'cycle_id': row['cycle_id'],
                            'date_facture': row['date_facture'],
                            'date_debut_cycle': row['date_debut_cycle'],
                            'date_fin_cycle': row['date_fin_cycle'],
                            'numero_facture': row['numero_facture'],
                            'total_general': row['total_general'],
                            'montant_assurance': row['montant_assurance'],
                            'montant_patient': row['montant_patient'],
                            'statut_paiement': row['statut_paiement'],
                            'statut': row['statut']
                        },
                        'details': [],
                        'paiements': []
                    }
                
                # Ajouter les détails
                if row['designation']:
                    factures_organisees[facture_id]['details'].append({
                        'designation': row['designation'],
                        'quantite': row['quantite'],
                        'prix_unitaire': row['prix_unitaire'],
                        'montant': row['detail_montant']
                    })
                
                # Ajouter les paiements
                if row['montant_paiement']:
                    factures_organisees[facture_id]['paiements'].append({
                        'montant_paiement': row['montant_paiement'],
                        'date_paiement': row['date_paiement'],
                        'mode_paiement': row['mode_paiement']
                    })
            
            # Calculer les totaux globaux
            total_general = sum(f['info']['total_general'] for f in factures_organisees.values())
            total_assurance = sum(f['info']['montant_assurance'] for f in factures_organisees.values())
            total_patient = sum(f['info']['montant_patient'] for f in factures_organisees.values())
            total_paye = sum(sum(p['montant_paiement'] for p in f['paiements']) for f in factures_organisees.values())
            
            return render_template('admin/gestion_patient/historique_facturation.html',
                             patient=patient,
                             factures=factures_organisees,
                             total_general=total_general,
                             total_assurance=total_assurance,
                             total_patient=total_patient,
                             total_paye=total_paye,
                             loggedIn=loggedIn, firstName=firstName)
        else:
            return redirect(url_for('login'))
    
    @app.route("/admin/patient/<int:patient_id>/facturation/statistiques")
    @login_required("admin")
    def statistiques_facturation(patient_id):
        """Statistiques de facturation du patient"""
        if 'email_admin' in session:
            loggedIn, firstName = getLogin('email_admin', 'admin', mysql)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Récupérer les infos du patient
            cursor.execute("SELECT * FROM patient WHERE id = %s", (patient_id,))
            patient = cursor.fetchone()
            
            if not patient:
                flash("Patient non trouvé.", "danger")
                return redirect(url_for('liste_patient_admin'))
            
            # Statistiques globales
            cursor.execute("""
                SELECT 
                    COUNT(*) as nb_factures,
                    COUNT(DISTINCT cycle_id) as nb_cycles,
                    SUM(total_general) as total_general,
                    SUM(montant_assurance) as total_assurance,
                    SUM(montant_patient) as total_patient,
                    SUM(CASE WHEN statut_paiement = 'paye' THEN total_general ELSE 0 END) as total_paye,
                    SUM(CASE WHEN statut_paiement = 'en_attente' THEN total_general ELSE 0 END) as total_en_attente,
                    SUM(CASE WHEN statut_paiement = 'partiellement_paye' THEN total_general ELSE 0 END) as total_partiel
                FROM facture 
                WHERE patient_id = %s
            """, (patient_id,))
            stats_globales = cursor.fetchone()
            
            # Statistiques par cycle
            cursor.execute("""
                SELECT 
                    cycle_id,
                    COUNT(*) as nb_factures,
                    SUM(total_general) as total_cycle,
                    MIN(date_facture) as date_debut,
                    MAX(date_facture) as date_fin,
                    MAX(statut) as statut_cycle
                FROM facture 
                WHERE patient_id = %s
                GROUP BY cycle_id
                ORDER BY date_debut DESC
            """, (patient_id,))
            stats_cycles = cursor.fetchall()
            
            # Services les plus fréquents
            cursor.execute("""
                SELECT 
                    fd.designation,
                    COUNT(*) as frequence,
                    SUM(fd.quantite) as total_quantite,
                    SUM(fd.montant) as total_montant
                FROM facture_detail fd
                JOIN facture f ON fd.facture_id = f.id
                WHERE f.patient_id = %s
                GROUP BY fd.designation
                ORDER BY frequence DESC
                LIMIT 10
            """, (patient_id,))
            services_frequents = cursor.fetchall()
            
            # Évolution mensuelle
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(date_facture, '%Y-%m') as mois,
                    COUNT(*) as nb_factures,
                    SUM(total_general) as total_mois
                FROM facture 
                WHERE patient_id = %s
                GROUP BY DATE_FORMAT(date_facture, '%Y-%m')
                ORDER BY mois DESC
                LIMIT 12
            """, (patient_id,))
            evolution_mensuelle = cursor.fetchall()
            
            # Moyennes
            cursor.execute("""
                SELECT 
                    AVG(total_general) as moyenne_facture,
                    MAX(total_general) as max_facture,
                    MIN(total_general) as min_facture
                FROM facture 
                WHERE patient_id = %s
            """, (patient_id,))
            moyennes = cursor.fetchone()
            
            return render_template('admin/gestion_patient/statistiques_facturation.html',
                             patient=patient,
                             stats_globales=stats_globales,
                             stats_cycles=stats_cycles,
                             services_frequents=services_frequents,
                             evolution_mensuelle=evolution_mensuelle,
                             moyennes=moyennes,
                             loggedIn=loggedIn, firstName=firstName)
        else:
            return redirect(url_for('login'))
    
    @app.route("/admin/patient/<int:patient_id>/facture/ajouter", methods=['GET', 'POST'])
    @login_required("admin")
    def ajouter_facture(patient_id):
        """Ajouter une nouvelle facture avec paiement intégré et cycle automatique"""
        if 'email_admin' in session:
            loggedIn, firstName = getLogin('email_admin', 'admin', mysql)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Vérifier que le patient existe
            cursor.execute("SELECT * FROM patient WHERE id = %s", (patient_id,))
            patient = cursor.fetchone()
            
            if not patient:
                flash("Patient non trouvé.", "danger")
                return redirect(url_for('liste_patient_admin'))
            
            # POST: Créer la facture avec paiement
            if request.method == 'POST':
                try:
                    # Récupérer les données du formulaire
                    services = request.form.getlist('services')
                    medicaments = request.form.getlist('medicaments')
                    assurances = request.form.getlist('assurances')
                    
                    # Données de paiement
                    montant_paiement = float(request.form.get('montant_paiement', 0))
                    mode_paiement = request.form.get('mode_paiement')
                    date_paiement = request.form.get('date_paiement')
                    
                    # Detect cycle en cours or create new
                    cursor.execute("SELECT cycle_id FROM facture WHERE patient_id=%s AND statut='EN_COURS' ORDER BY date_facture DESC LIMIT 1", (patient_id,))
                    cycle_en_cours = cursor.fetchone()
                    if cycle_en_cours:
                        cycle_id = cycle_en_cours['cycle_id']
                    else:
                        cycle_id = generer_cycle_id(patient_id)
                    
                    # Créer la facture
                    cursor.execute("""
                        INSERT INTO facture (patient_id, cycle_id, date_facture, date_debut_cycle, statut)
                        VALUES (%s, %s, CURDATE(), CURDATE(), 'EN_COURS')
                    """, (patient_id, cycle_id))
                    facture_id = cursor.lastrowid
                    
                    # Ajouter les services
                    total_general = 0
                    for service in services:
                        designation, quantite, prix = service.split('|')
                        quantite = int(quantite)
                        prix = float(prix)
                        montant = quantite * prix
                        cursor.execute("""
                            INSERT INTO facture_detail (facture_id, designation, quantite, prix_unitaire)
                            VALUES (%s, %s, %s, %s)
                        """, (facture_id, designation, quantite, prix))
                        total_general += montant
                    
                    # Ajouter les médicaments
                    for med_data in medicaments:
                        med_id, quantite, prix = med_data.split('|')
                        quantite = int(quantite)
                        
                        # Récupérer les infos du médicament
                        cursor.execute("""
                            SELECT nom, prix_unitaire FROM medicament 
                            WHERE id = %s
                        """, (med_id,))
                        medicament = cursor.fetchone()
                        
                        if not medicament:
                            continue
                        
                        # Convertir le prix_unitaire en float
                        prix_unitaire = float(medicament['prix_unitaire'])
                        
                        # Ajouter le médicament à la facture
                        cursor.execute("""
                            INSERT INTO facture_detail 
                            (facture_id, designation, quantite, prix_unitaire)
                            VALUES (%s, %s, %s, %s)
                        """, (facture_id, f"Médicament: {medicament['nom']}", 
                              quantite, prix_unitaire))
                        
                        # Mettre à jour le stock du médicament
                        cursor.execute("""
                            UPDATE medicament 
                            SET quantite_stock = quantite_stock - %s
                            WHERE id = %s AND quantite_stock >= %s
                        """, (quantite, med_id, quantite))
                        
                        # Vérifier si le stock a été mis à jour
                        if cursor.rowcount == 0:
                            mysql.connection.rollback()
                            flash(f"Stock insuffisant pour {medicament['nom']}", "danger")
                            return redirect(url_for('ajouter_facture', patient_id=patient_id))
                        
                        total_general += quantite * prix_unitaire
                    
                    # Calculer les montants avec assurances multiples
                    montant_assurance_total = 0
                    montant_patient = total_general
                    
                    if assurances:
                        # Traiter les assurances sélectionnées
                        for assurance_data in assurances:
                            assurance_id, pourcentage_applique = assurance_data.split('|')
                            assurance_id = int(assurance_id)
                            pourcentage_applique = float(pourcentage_applique)
                            
                            # Récupérer les infos de l'assurance
                            cursor.execute("""
                                SELECT type_assurance, numero_assurance FROM assurance 
                                WHERE id = %s AND patient_id = %s
                            """, (assurance_id, patient_id))
                            assurance_info = cursor.fetchone()
                            
                            if assurance_info:
                                montant_couvert = total_general * (pourcentage_applique / 100)
                                montant_assurance_total += montant_couvert
                                
                                # Ajouter la liaison facture-assurance
                                cursor.execute("""
                                    INSERT INTO facture_assurance 
                                    (facture_id, assurance_id, pourcentage_applique, montant_couvert)
                                    VALUES (%s, %s, %s, %s)
                                """, (facture_id, assurance_id, pourcentage_applique, montant_couvert))
                    
                    # Limiter le total des assurances à ne pas dépasser le montant total
                    montant_assurance_total = min(montant_assurance_total, total_general)
                    montant_patient = total_general - montant_assurance_total
                    
                    # Mettre à jour la facture avec les montants calculés
                    cursor.execute("""
                        UPDATE facture 
                        SET total_general = %s, base_remboursement = %s, 
                            montant_assurance = %s, montant_patient = %s,
                            montant_total = %s
                        WHERE id = %s
                    """, (total_general, total_general, montant_assurance_total, montant_patient, total_general, facture_id))
                    
                    # Ajouter le paiement si montant > 0
                    if montant_paiement > 0:
                        # Valider que le paiement ne dépasse pas le montant du patient
                        if montant_paiement > montant_patient:
                            mysql.connection.rollback()
                            flash(f"Le paiement ne peut pas dépasser la responsabilité du patient de {montant_patient:.0f} FCFA", "danger")
                            return redirect(url_for('ajouter_facture', patient_id=patient_id))
                        
                        # Ajouter le paiement
                        cursor.execute("""
                            INSERT INTO paiement 
                            (facture_id, montant_paiement, date_paiement, mode_paiement)
                            VALUES (%s, %s, %s, %s)
                        """, (facture_id, montant_paiement, date_paiement, mode_paiement))
                        
                        # Mettre à jour le montant payé de la facture
                        cursor.execute("""
                            UPDATE facture 
                            SET montant_paye = %s
                            WHERE id = %s
                        """, (montant_paiement, facture_id))
                        
                        # Mettre à jour le statut de paiement
                        if montant_paiement >= montant_patient:
                            statut_paiement = 'paye'
                        elif montant_paiement > 0:
                            statut_paiement = 'partiellement_paye'
                        else:
                            statut_paiement = 'en_attente'
                        
                        cursor.execute("""
                            UPDATE facture 
                            SET statut_paiement = %s
                            WHERE id = %s
                        """, (statut_paiement, facture_id))
                    
                    mysql.connection.commit()
                    
                    # Message de succès avec détails
                    message = f"Facture créée avec succès! Total: {total_general:.0f} FCFA"
                    if assurances and len(assurances) > 0:
                        message += f" | Assurances: {montant_assurance_total:.0f} FCFA ({len(assurances)} assurance(s))"
                    if montant_paiement > 0:
                        message += f" | Payé: {montant_paiement:.0f} FCFA ({mode_paiement})"
                        reste_a_payer = montant_patient - montant_paiement
                        if reste_a_payer > 0:
                            message += f" | Reste à payer: {reste_a_payer:.0f} FCFA"
                    
                    flash(message, "success")
                    return redirect(url_for('details_cycle', patient_id=patient_id, cycle_id=cycle_id))
                    
                except Exception as e:
                    mysql.connection.rollback()
                    flash(f"Erreur lors de la création: {e}", "danger")
                    return redirect(url_for('facturation_patient', patient_id=patient_id))
            
            # GET: Récupérer les médicaments pour prescription
            cursor.execute("SELECT * FROM medicament ORDER BY nom")
            medicaments = cursor.fetchall()
            
            # Récupérer toutes les assurances du patient
            cursor.execute("""
                SELECT * FROM assurance 
                WHERE patient_id = %s
            """, (patient_id,))
            assurances = cursor.fetchall()
            
            from datetime import datetime
            return render_template('admin/gestion_patient/ajouter_facture_avec_paiement.html',
                             patient=patient,
                             medicaments=medicaments,
                             assurances=assurances,
                             datetime=datetime,
                             loggedIn=loggedIn, firstName=firstName)
        else:
            return redirect(url_for('login'))
    
    @app.route("/admin/facture/<int:facture_id>/paiement/ajouter", methods=['POST'])
    @login_required("admin")
    def ajouter_paiement_facture(facture_id):
        """Ajouter un paiement à une facture"""
        if 'email_admin' in session:
            try:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                
                # Récupérer les infos de la facture
                cursor.execute("""
                    SELECT patient_id, cycle_id FROM facture WHERE id = %s
                """, (facture_id,))
                facture_info = cursor.fetchone()
                
                if not facture_info:
                    return jsonify({'error': 'Facture non trouvée'}), 404
                
                # Vérifier que le cycle n'est pas terminé
                if is_cycle_termine(facture_info['patient_id'], facture_info['cycle_id']):
                    return jsonify({'error': 'Cycle terminé - modification interdite'}), 403
                
                # Récupérer les données du formulaire
                designation = request.form.get('designation')
                quantite = int(request.form.get('quantite', 1))
                prix_unitaire = float(request.form.get('prix_unitaire', 0))
                
                # Ajouter le détail
                cursor.execute("""
                    INSERT INTO facture_detail 
                    (facture_id, designation, quantite, prix_unitaire)
                    VALUES (%s, %s, %s, %s)
                """, (facture_id, designation, quantite, prix_unitaire))
                
                # Recalculer les montants de la facture
                montants = calculer_montants_facture(facture_id)
                
                mysql.connection.commit()
                
                return jsonify({
                    'success': True,
                    'montants': montants
                })
                
            except Exception as e:
                mysql.connection.rollback()
                return jsonify({'error': str(e)}), 500
    
    @app.route("/admin/facture/<int:facture_id>/prescrire_medicament", methods=['POST'])
    @login_required("admin")
    def prescrire_medicament(facture_id):
        """Prescrire un médicament et l'ajouter à la facture"""
        if 'email_admin' in session:
            try:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                
                # Récupérer les infos de la facture
                cursor.execute("""
                    SELECT f.patient_id, f.cycle_id FROM facture f
                    WHERE f.id = %s
                """, (facture_id,))
                facture_info = cursor.fetchone()
                
                if not facture_info:
                    return jsonify({'error': 'Facture non trouvée'}), 404
                
                # Vérifier que le cycle n'est pas terminé
                if is_cycle_termine(facture_info['patient_id'], facture_info['cycle_id']):
                    return jsonify({'error': 'Cycle terminé - modification interdite'}), 403
                
                # Récupérer les données du formulaire
                medicament_id = request.form.get('medicament_id')
                quantite = int(request.form.get('quantite', 1))
                
                # Récupérer les infos du médicament
                cursor.execute("""
                    SELECT nom, prix_unitaire FROM medicament 
                    WHERE id = %s
                """, (medicament_id,))
                medicament = cursor.fetchone()
                
                if not medicament:
                    return jsonify({'error': 'Médicament non trouvé'}), 404
                
                # Ajouter le médicament à la facture
                cursor.execute("""
                    INSERT INTO facture_detail 
                    (facture_id, designation, quantite, prix_unitaire)
                    VALUES (%s, %s, %s, %s)
                """, (facture_id, f"Médicament: {medicament['nom']}", 
                      quantite, medicament['prix_unitaire']))
                
                # Mettre à jour le stock du médicament
                cursor.execute("""
                    UPDATE medicament 
                    SET quantite_stock = quantite_stock - %s
                    WHERE id = %s AND quantite_stock >= %s
                """, (quantite, medicament_id, quantite))
                
                # Vérifier si le stock a été mis à jour
                if cursor.rowcount == 0:
                    mysql.connection.rollback()
                    return jsonify({'error': 'Stock insuffisant'}), 400
                
                # Recalculer les montants de la facture
                montants = calculer_montants_facture(facture_id)
                
                mysql.connection.commit()
                
                return jsonify({
                    'success': True,
                    'montants': montants,
                    'medicament': medicament['nom']
                })
                
            except Exception as e:
                mysql.connection.rollback()
                return jsonify({'error': str(e)}), 500
    
    @app.route("/admin/facture/<int:facture_id>/detail/<int:detail_id>/supprimer", methods=['POST'])
    @login_required("admin")
    def supprimer_detail_facture(facture_id, detail_id):
        """Supprimer une ligne de détail d'une facture"""
        if 'email_admin' in session:
            try:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                
                # Récupérer les infos de la facture
                cursor.execute("""
                    SELECT patient_id, cycle_id FROM facture WHERE id = %s
                """, (facture_id,))
                facture_info = cursor.fetchone()
                
                if not facture_info:
                    return jsonify({'error': 'Facture non trouvée'}), 404
                
                # Vérifier que le cycle n'est pas terminé
                if is_cycle_termine(facture_info['patient_id'], facture_info['cycle_id']):
                    return jsonify({'error': 'Cycle terminé - modification interdite'}), 403
                
                # Supprimer le détail
                cursor.execute("""
                    DELETE FROM facture_detail 
                    WHERE id = %s AND facture_id = %s
                """, (detail_id, facture_id))
                
                # Recalculer les montants de la facture
                montants = calculer_montants_facture(facture_id)
                
                mysql.connection.commit()
                
                return jsonify({
                    'success': True,
                    'montants': montants
                })
                
            except Exception as e:
                mysql.connection.rollback()
                return jsonify({'error': str(e)}), 500
    
    @app.route("/admin/patient/<int:patient_id>/cycle/<string:cycle_id>/terminer", methods=['POST'])
    @login_required("admin")
    def terminer_cycle(patient_id, cycle_id):
        """Terminer un cycle de facturation"""
        if 'email_admin' in session:
            try:
                cursor = mysql.connection.cursor()
                
                # Vérifier que le cycle appartient au patient
                cursor.execute("""
                    SELECT COUNT(*) as count FROM facture 
                    WHERE patient_id = %s AND cycle_id = %s
                """, (patient_id, cycle_id))
                if cursor.fetchone()[0] == 0:
                    flash("Cycle non trouvé.", "danger")
                    return redirect(url_for('facturation_patient', patient_id=patient_id))
                
                # Vérifier que le cycle n'est pas déjà terminé
                if is_cycle_termine(patient_id, cycle_id):
                    flash("Cycle déjà terminé.", "warning")
                    return redirect(url_for('details_cycle', patient_id=patient_id, cycle_id=cycle_id))
                
                # Mettre à jour toutes les factures du cycle
                cursor.execute("""
                    UPDATE facture 
                    SET statut = 'TERMINE'
                    WHERE patient_id = %s AND cycle_id = %s
                """, (patient_id, cycle_id))
                
                mysql.connection.commit()
                flash("Cycle terminé avec succès! Les données sont maintenant verrouillées.", "success")
                return redirect(url_for('details_cycle', patient_id=patient_id, cycle_id=cycle_id))
                
            except Exception as e:
                mysql.connection.rollback()
                flash(f"Erreur lors de la terminaison: {e}", "danger")
                return redirect(url_for('details_cycle', patient_id=patient_id, cycle_id=cycle_id))
    
    @app.route("/admin/facture/<int:facture_id>/supprimer", methods=['POST'])
    @login_required("admin")
    def supprimer_facture(facture_id):
        """Supprimer une facture"""
        if 'email_admin' in session:
            try:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                
                # Récupérer les infos de la facture
                cursor.execute("""
                    SELECT patient_id, cycle_id FROM facture WHERE id = %s
                """, (facture_id,))
                facture_info = cursor.fetchone()
                
                if not facture_info:
                    flash("Facture non trouvée.", "danger")
                    return redirect(url_for('facturation_patient', patient_id=facture_info['patient_id']))
                
                # Vérifier que le cycle n'est pas terminé
                if is_cycle_termine(facture_info['patient_id'], facture_info['cycle_id']):
                    flash("Impossible de supprimer une facture d'un cycle terminé.", "danger")
                    return redirect(url_for('details_cycle', patient_id=facture_info['patient_id'], cycle_id=facture_info['cycle_id']))
                
                # Supprimer la facture (les détails seront supprimés en cascade)
                cursor.execute("DELETE FROM facture WHERE id = %s", (facture_id,))
                
                # Vérifier s'il reste des factures dans le cycle
                cursor.execute("""
                    SELECT COUNT(*) as count FROM facture 
                    WHERE patient_id = %s AND cycle_id = %s
                """, (facture_info['patient_id'], facture_info['cycle_id']))
                remaining = cursor.fetchone()[0]
                
                if remaining == 0:
                    # Plus de factures dans le cycle, on peut supprimer le cycle
                    pass  # Le cycle n'existe plus vraiment
                else:
                    # Mettre à jour les dates du cycle
                    cursor.execute("""
                        SELECT MIN(date_facture) as min_date, MAX(date_facture) as max_date
                        FROM facture WHERE patient_id = %s AND cycle_id = %s
                    """, (facture_info['patient_id'], facture_info['cycle_id']))
                    cycle_dates = cursor.fetchone()
                    
                    cursor.execute("""
                        UPDATE facture 
                        SET date_debut_cycle = %s, date_fin_cycle = %s
                        WHERE patient_id = %s AND cycle_id = %s
                    """, (cycle_dates['min_date'], cycle_dates['max_date'], 
                          facture_info['patient_id'], facture_info['cycle_id']))
                
                mysql.connection.commit()
                flash("Facture supprimée avec succès!", "success")
                return redirect(url_for('details_cycle', patient_id=facture_info['patient_id'], cycle_id=facture_info['cycle_id']))
                
            except Exception as e:
                mysql.connection.rollback()
                flash(f"Erreur lors de la suppression: {e}", "danger")
                return redirect(url_for('facturation_patient', patient_id=facture_info['patient_id']))
    
    @app.route("/admin/facture/<int:facture_id>/generer_pdf")
    @login_required("admin")
    def generer_facture_pdf(facture_id):
        """Générer une facture PDF professionnelle"""
        if 'email_admin' in session:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            facture = None
            
            try:
                # Récupérer les infos complètes de la facture
                cursor.execute("""
                    SELECT f.*, p.nom as patient_nom, p.prenom as patient_prenom, 
                           p.adresse, p.numero_telephone, p.email_patient,
                           a.type_assurance, a.pourcentage
                    FROM facture f
                    JOIN patient p ON f.patient_id = p.id
                    LEFT JOIN assurance a ON p.id = a.patient_id
                    WHERE f.id = %s
                """, (facture_id,))
                
                facture = cursor.fetchone()
                
                if not facture:
                    flash("Facture non trouvée.", "danger")
                    return redirect(url_for('facturation_patient', patient_id=facture_id))
                
                # Récupérer les détails de la facture
                cursor.execute("""
                    SELECT * FROM facture_detail 
                    WHERE facture_id = %s
                    ORDER BY id
                """, (facture_id,))
                details = cursor.fetchall()
                
                # Récupérer les paiements
                cursor.execute("""
                    SELECT * FROM paiement 
                    WHERE facture_id = %s
                    ORDER BY date_paiement
                """, (facture_id,))
                paiements = cursor.fetchall()
                
                # Récupérer les infos de la clinique
                cursor.execute("""
                    SELECT * FROM clinique 
                    LIMIT 1
                """)
                clinique = cursor.fetchone()
                
                # Créer une réponse simple pour le moment (sans reportlab)
                from flask import make_response
                import io
                
                # Créer un contenu HTML simple pour le PDF
                numero_facture = facture.get('numero_facture', f'FAC-{facture["id"]}')
                date_facture = facture['date_facture'].strftime('%d/%m/%Y') if facture['date_facture'] else 'N/A'
                
                html_content = f"""
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Facture {numero_facture}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; }}
                        .header {{ text-align: center; margin-bottom: 30px; }}
                        .patient-info {{ margin: 20px 0; }}
                        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        th {{ background-color: #f2f2f2; }}
                        .total {{ font-weight: bold; }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>Clinique Floréal</h1>
                        <p>Agoè Anomé, en face de l'Hôtel Saint Manick, Lomé, Togo</p>
                        <p>Tél: +228 93 43 66 66 / +228 22 50 85 83</p>
                        <h2>FACTURE</h2>
                        <p>Numéro: {numero_facture}</p>
                        <p>Date: {date_facture}</p>
                    </div>
                    
                    <div class="patient-info">
                        <h3>Patient: {facture.get('patient_nom', 'N/A')} {facture.get('patient_prenom', 'N/A')}</h3>
                        <p>Adresse: {facture.get('adresse', 'Non spécifiée')}</p>
                        <p>Téléphone: {facture.get('numero_telephone', 'Non spécifié')}</p>
                        <p>Email: {facture.get('email_patient', 'Non spécifié')}</p>
                    </div>
                    
                    <table>
                        <tr>
                            <th>Désignation</th>
                            <th>Quantité</th>
                            <th>Prix Unitaire</th>
                            <th>Total</th>
                        </tr>
                """
                
                # Ajouter les détails
                for detail in details:
                    html_content += f"""
                        <tr>
                            <td>{detail['designation']}</td>
                            <td>{detail['quantite']}</td>
                            <td>{detail['prix_unitaire']:.0f} FCFA</td>
                            <td>{detail['montant']:.0f} FCFA</td>
                        </tr>
                    """
                
                html_content += f"""
                        <tr class="total">
                            <td colspan="3">Total Général:</td>
                            <td>{facture['total_general']:.0f} FCFA</td>
                        </tr>
                        <tr>
                            <td colspan="3">Montant Assurance:</td>
                            <td>{facture['montant_assurance']:.0f} FCFA</td>
                        </tr>
                        <tr>
                            <td colspan="3">Montant Patient:</td>
                            <td>{facture['montant_patient']:.0f} FCFA</td>
                        </tr>
                        <tr>
                            <td colspan="3">Montant Payé:</td>
                            <td>{facture['montant_paye']:.0f} FCFA</td>
                        </tr>
                        <tr class="total">
                            <td colspan="3">Montant Restant:</td>
                            <td>{facture['total_general'] - facture['montant_paye']:.0f} FCFA</td>
                        </tr>
                    </table>
                    
                    <h3>Paiements Effectués:</h3>
                    <table>
                        <tr>
                            <th>Date</th>
                            <th>Montant</th>
                            <th>Mode</th>
                        </tr>
                """
                
                # Ajouter les paiements
                for paiement in paiements:
                    html_content += f"""
                        <tr>
                            <td>{paiement['date_paiement'].strftime('%d/%m/%Y')}</td>
                            <td>{paiement['montant_paiement']:.0f} FCFA</td>
                            <td>{paiement['mode_paiement']}</td>
                        </tr>
                    """
                
                html_content += """
                    </table>
                    
                    <div style="margin-top: 50px; text-align: center;">
                        <p>Merci de votre confiance</p>
                        <p>Conditions de paiement: Paiement sous 30 jours</p>
                    </div>
                </body>
                </html>
                """
                
                # Pour le moment, retourner le HTML comme réponse
                # Plus tard, vous pourrez installer reportlab pour générer un vrai PDF
                response = make_response(html_content.encode('utf-8'))
                response.headers['Content-Type'] = 'text/html; charset=utf-8'
                response.headers['Content-Disposition'] = f'inline; filename=facture_{facture.get("numero_facture", facture["id"])}.html'
                
                return response
                
            except Exception as e:
                flash(f"Erreur lors de la génération du PDF: {e}", "danger")
                if facture:
                    return redirect(url_for('details_cycle', patient_id=facture['patient_id'], cycle_id=facture['cycle_id']))
                else:
                    return redirect(url_for('facturation_patient', patient_id=facture_id))
    
    @app.route("/admin/patient/<int:patient_id>/cycle/<string:cycle_id>/facture_generale")
    @login_required("admin")
    def generer_facture_generale_cycle(patient_id, cycle_id):
        """Générer une facture générale consolidée pour tout un cycle"""
        if 'email_admin' in session:
            try:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                
                # Vérifier que le cycle appartient au patient
                cursor.execute("""
                    SELECT COUNT(*) as count FROM facture 
                    WHERE patient_id = %s AND cycle_id = %s
                """, (patient_id, cycle_id))
                if cursor.fetchone()['count'] == 0:
                    flash("Cycle non trouvé.", "danger")
                    return redirect(url_for('facturation_patient', patient_id=patient_id))
                
                # Récupérer toutes les factures du cycle
                cursor.execute("""
                    SELECT f.*, p.nom as patient_nom, p.prenom as patient_prenom, 
                           p.adresse, p.numero_telephone, p.email_patient,
                           a.type_assurance, a.pourcentage
                    FROM facture f
                    JOIN patient p ON f.patient_id = p.id
                    LEFT JOIN assurance a ON p.id = a.patient_id
                    WHERE f.patient_id = %s AND f.cycle_id = %s
                    ORDER BY f.date_facture
                """, (patient_id, cycle_id))
                factures = cursor.fetchall()
                
                if not factures:
                    flash("Aucune facture dans ce cycle.", "danger")
                    return redirect(url_for('details_cycle', patient_id=patient_id, cycle_id=cycle_id))
                
                # Récupérer tous les détails des factures du cycle
                cursor.execute("""
                    SELECT fd.* FROM facture_detail fd
                    JOIN facture f ON fd.facture_id = f.id
                    WHERE f.patient_id = %s AND f.cycle_id = %s
                    ORDER BY f.date_facture, fd.id
                """, (patient_id, cycle_id))
                all_details = cursor.fetchall()
                
                # Récupérer tous les paiements du cycle
                cursor.execute("""
                    SELECT p.* FROM paiement p
                    JOIN facture f ON p.facture_id = f.id
                    WHERE f.patient_id = %s AND f.cycle_id = %s
                    ORDER BY p.date_paiement
                """, (patient_id, cycle_id))
                all_paiements = cursor.fetchall()
                
                # Récupérer les infos de la clinique
                cursor.execute("""
                    SELECT * FROM clinique 
                    LIMIT 1
                """)
                clinique = cursor.fetchone()
                
                # Calculer les totaux consolidés
                total_general = sum(f['total_general'] for f in factures)
                total_assurance = sum(f['montant_assurance'] for f in factures)
                total_patient = sum(f['montant_patient'] for f in factures)
                total_paye = sum(p['montant_paiement'] for p in all_paiements)
                
                # Calcul correct du montant restant
                # Si assurance prend en charge, le montant restant = total_patient - total_paye
                # Sinon, montant restant = total_general - total_paye
                if total_assurance > 0:
                    montant_restant = total_patient - total_paye
                else:
                    montant_restant = total_general - total_paye
                
                # Créer la facture générale
                from flask import make_response
                import io
                from datetime import datetime
                
                numero_facture_generale = f"GEN-{cycle_id}"
                date_debut_cycle = min(f['date_facture'] for f in factures).strftime('%d/%m/%Y')
                date_fin_cycle = max(f['date_facture'] for f in factures).strftime('%d/%m/%Y')
                
                html_content = f"""
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Facture Générale - {numero_facture_generale}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; }}
                        .header {{ text-align: center; margin-bottom: 30px; }}
                        .patient-info {{ margin: 20px 0; }}
                        .summary {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin: 20px 0; }}
                        .summary h3 {{ margin: 0; }}
                        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        th {{ background-color: #f2f2f2; }}
                        .total {{ font-weight: bold; font-size: 1.1em; }}
                        .montant-restant {{ color: #dc3545; font-weight: bold; }}
                        .montant-payé {{ color: #28a745; font-weight: bold; }}
                        .section-title {{ border-left: 4px solid #667eea; padding-left: 15px; margin: 30px 0 15px 0; }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>Clinique Floréal</h1>
                        <p>Agoè Anomé, en face de l'Hôtel Saint Manick, Lomé, Togo</p>
                        <p>Tél: +228 93 43 66 66 / +228 22 50 85 83</p>
                        <p>Email: florealclinique@gmail.com</p>
                        <h2 style="color: #667eea;">FACTURE GÉNÉRALE</h2>
                        <p><strong>Numéro:</strong> {numero_facture_generale}</p>
                        <p><strong>Période:</strong> {date_debut_cycle} au {date_fin_cycle}</p>
                        <p><strong>Date d'émission:</strong> {datetime.now().strftime('%d/%m/%Y')}</p>
                    </div>
                    
                    <div class="patient-info">
                        <h3>Informations Patient</h3>
                        <p><strong>Nom:</strong> {factures[0].get('patient_nom', 'N/A')} {factures[0].get('patient_prenom', 'N/A')}</p>
                        <p><strong>Adresse:</strong> {factures[0].get('adresse', 'Non spécifiée')}</p>
                        <p><strong>Téléphone:</strong> {factures[0].get('numero_telephone', 'Non spécifié')}</p>
                        <p><strong>Email:</strong> {factures[0].get('email_patient', 'Non spécifié')}</p>
                        {f"<p><strong>Assurance:</strong> {factures[0].get('type_assurance', 'Non spécifiée')} ({factures[0].get('pourcentage', 0)}%)</p>" if factures[0].get('type_assurance') else ""}
                    </div>
                    
                    <div class="summary">
                        <h3>Résumé Financier du Cycle</h3>
                        <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
                            <div style="text-align: center;">
                                <div style="font-size: 2em; font-weight: bold;">{total_general:.0f}</div>
                                <div>Total Général (FCFA)</div>
                            </div>
                            <div style="text-align: center;">
                                <div style="font-size: 2em; font-weight: bold;">{total_assurance:.0f}</div>
                                <div>Assurance (FCFA)</div>
                            </div>
                            <div style="text-align: center;">
                                <div style="font-size: 2em; font-weight: bold;">{total_patient:.0f}</div>
                                <div>Responsabilité Patient (FCFA)</div>
                            </div>
                        </div>
                        <div style="text-align: center; margin-top: 20px;">
                            <div style="font-size: 2.2em; font-weight: bold;">{total_paye:.0f}</div>
                                <div>Montant Payé (FCFA)</div>
                        </div>
                        <div style="text-align: center; margin-top: 20px;">
                            <div class="montant-restant">{montant_restant:.0f}</div>
                            <div>Montant Restant à Payer (FCFA)</div>
                        </div>
                        <div style="text-align: center; margin-top: 15px; font-size: 0.9em; color: #666;">
                            {"<em>Montant restant = Responsabilité Patient - Montant Payé</em>" if total_assurance > 0 else "<em>Montant restant = Total Général - Montant Payé</em>"}
                        </div>
                    </div>
                    
                    <div class="section-title">
                        <h3>Détail des Factures du Cycle</h3>
                    </div>
                    
                    <table>
                        <tr>
                            <th>Date</th>
                            <th>Numéro Facture</th>
                            <th>Désignation</th>
                            <th>Quantité</th>
                            <th>Prix U.</th>
                            <th>Total</th>
                        </tr>
                """
                
                # Ajouter tous les détails
                for detail in all_details:
                    # Trouver la facture correspondante pour la date
                    facture_date = None
                    for f in factures:
                        if f['id'] == detail['facture_id']:
                            facture_date = f['date_facture'].strftime('%d/%m/%Y')
                            break
                    
                    html_content += f"""
                        <tr>
                            <td>{facture_date}</td>
                            <td>{detail.get('facture_id', '')}</td>
                            <td>{detail.get('designation', 'N/A')}</td>
                            <td>{detail.get('quantite', 0)}</td>
                            <td>{detail.get('prix_unitaire', 0):.0f}</td>
                            <td>{detail.get('montant', 0):.0f}</td>
                        </tr>
                    """
                
                html_content += f"""
                        <tr class="total">
                            <td colspan="5">TOTAL GÉNÉRAL:</td>
                            <td>{total_general:.0f} FCFA</td>
                        </tr>
                    </table>
                    
                    <div class="section-title">
                        <h3>Historique des Paiements</h3>
                    </div>
                    
                    <table>
                        <tr>
                            <th>Date</th>
                            <th>Montant</th>
                            <th>Mode</th>
                            <th>Référence</th>
                        </tr>
                """
                
                # Ajouter tous les paiements
                for paiement in all_paiements:
                    html_content += f"""
                        <tr>
                            <td>{paiement['date_paiement'].strftime('%d/%m/%Y')}</td>
                            <td>{paiement['montant_paiement']:.0f} FCFA</td>
                            <td>{paiement['mode_paiement']}</td>
                            <td>{paiement.get('reference_paiement', 'N/A')}</td>
                        </tr>
                    """
                
                html_content += f"""
                        <tr class="total">
                            <td colspan="3">TOTAL PAYÉ:</td>
                            <td>{total_paye:.0f} FCFA</td>
                            <td></td>
                        </tr>
                    </table>
                    
                    <div style="margin-top: 50px; text-align: center;">
                        <h3>Conditions de Paiement</h3>
                        <p><strong>Paiement sous 30 jours</strong></p>
                        <p><strong>Merci de votre confiance</strong></p>
                        <p><small>Clinique Floréal - Agoè Anomé, Lomé, Togo</small></p>
                    </div>
                </body>
                </html>
                """
                
                # Créer la réponse avec encodage UTF-8
                response = make_response(html_content.encode('utf-8'))
                response.headers['Content-Type'] = 'text/html; charset=utf-8'
                response.headers['Content-Disposition'] = f'inline; filename=facture_generale_{cycle_id}.html'
                
                return response
                
            except Exception as e:
                flash(f"Erreur lors de la génération de la facture générale: {e}", "danger")
                return redirect(url_for('details_cycle', patient_id=patient_id, cycle_id=cycle_id))
