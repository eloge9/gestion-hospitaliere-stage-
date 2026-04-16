-- Table pour les paiements
CREATE TABLE IF NOT EXISTS paiement (
    id INT AUTO_INCREMENT PRIMARY KEY,
    facture_id INT NOT NULL,
    montant_paiement DECIMAL(10,2) NOT NULL,
    date_paiement DATE NOT NULL,
    mode_paiement ENUM('espece', 'carte_bancaire', 'virement', 'mobile_money', 'cheque', 'autre') NOT NULL,
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
    telephone VARCHAR(50) DEFAULT NULL,
    email VARCHAR(255) DEFAULT NULL,
    logo VARCHAR(255) DEFAULT NULL,
    rccm VARCHAR(255) DEFAULT NULL,
    compte_bancaire VARCHAR(255) DEFAULT NULL,
    numero_contribuable VARCHAR(255) DEFAULT NULL,
    site_web VARCHAR(255) DEFAULT NULL,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insérer les données par défaut de la clinique
INSERT IGNORE INTO clinique (id, nom, adresse, telephone, email, rccm, compte_bancaire) 
VALUES (1, 'Clinique Floréal', '123 Avenue des Champs-Élysées, Paris, France', '+33 1 23 45 67 89', 'contact@cliniquefloreal.com', 'FR 12 345 678 901', 'FR76 3000 6000 0112 3456 7890 189');

-- Mettre à jour la table facture pour ajouter les champs manquants s'ils n'existent pas
ALTER TABLE facture 
ADD COLUMN IF NOT EXISTS montant_total DECIMAL(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS montant_paye DECIMAL(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS statut_paiement ENUM('en_attente', 'partiellement_paye', 'paye') DEFAULT 'en_attente';
