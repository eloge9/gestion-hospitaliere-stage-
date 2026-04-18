-- Script pour ajouter la gestion multi-assurance à la base de données existante
-- À exécuter sur la base de données floreal_db

USE floreal_db;

-- Création de la table de liaison facture_assurance
-- Permet d'associer plusieurs assurances à une facture
CREATE TABLE IF NOT EXISTS facture_assurance (
  id INT AUTO_INCREMENT PRIMARY KEY,
  facture_id INT NOT NULL,
  assurance_id INT NOT NULL,
  pourcentage_applique DECIMAL(5,2) NOT NULL DEFAULT 0,
  montant_couvert DECIMAL(10,2) NOT NULL DEFAULT 0,
  date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY (facture_id) REFERENCES facture(id) ON DELETE CASCADE,
  FOREIGN KEY (assurance_id) REFERENCES assurance(id) ON DELETE CASCADE,
  
  -- Empêcher la même assurance d'être appliquée deux fois à la même facture
  UNIQUE KEY unique_facture_assurance (facture_id, assurance_id)
);

-- Ajout d'index pour optimiser les recherches
CREATE INDEX IF NOT EXISTS idx_facture_assurance_facture ON facture_assurance(facture_id);
CREATE INDEX IF NOT EXISTS idx_facture_assurance_assurance ON facture_assurance(assurance_id);

-- Afficher un message de confirmation
SELECT 'Table facture_assurance créée avec succès!' as message;
