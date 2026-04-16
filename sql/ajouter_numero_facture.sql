-- Ajouter la colonne numero_facture à la table facture
ALTER TABLE facture 
ADD COLUMN IF NOT EXISTS numero_facture VARCHAR(50) DEFAULT NULL;

-- Mettre à jour les factures existantes avec un numéro automatique
UPDATE facture 
SET numero_facture = CONCAT('FAC-', YEAR(date_facture), '-', LPAD(id, 6, '0')) 
WHERE numero_facture IS NULL;
