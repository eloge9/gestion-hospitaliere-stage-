-- Table pour les paiements (spécifique Togo)
CREATE TABLE IF NOT EXISTS paiement (
    id INT AUTO_INCREMENT PRIMARY KEY,
    facture_id INT NOT NULL,
    montant_paiement DECIMAL(10,2) NOT NULL,
    date_paiement DATE NOT NULL,
    mode_paiement ENUM('espece', 'tmoney_flooz', 'virement_bancaire', 'cheque', 'autre') NOT NULL,
    reference_paiement VARCHAR(255) DEFAULT NULL,
    description TEXT DEFAULT NULL,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (facture_id) REFERENCES facture(id) ON DELETE CASCADE,
    INDEX idx_facture_paiement (facture_id),
    INDEX idx_date_paiement (date_paiement),
    INDEX idx_mode_paiement (mode_paiement)
);

-- Table pour les informations de la clinique
CREATE TABLE IF NOT EXISTS clinique (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(255) NOT NULL DEFAULT 'Clinique Floréal',
    adresse TEXT DEFAULT NULL,
    telephone VARCHAR(255) DEFAULT NULL,
    email VARCHAR(255) DEFAULT NULL,
    site_web VARCHAR(255) DEFAULT NULL,
    logo VARCHAR(255) DEFAULT NULL,
    rccm VARCHAR(255) DEFAULT NULL,
    compte_bancaire VARCHAR(255) DEFAULT NULL,
    numero_contribuable VARCHAR(255) DEFAULT NULL,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insérer les données de Clinique Floréal (Togo)
INSERT IGNORE INTO clinique (id, nom, adresse, telephone, email, site_web) 
VALUES (1, 'Clinique Floréal', 'Agoè Anomé, en face de l\'Hôtel Saint Manick, Lomé, Togo', '+228 93 43 66 66 / +228 22 50 85 83', 'florealclinique@gmail.com', '[Pas de site web officiel actif recensé]');

-- Mettre à jour la table facture pour ajouter les champs manquants s'ils n'existent pas
ALTER TABLE facture 
ADD COLUMN IF NOT EXISTS montant_total DECIMAL(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS montant_paye DECIMAL(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS statut_paiement ENUM('en_attente', 'partiellement_paye', 'paye') DEFAULT 'en_attente';
