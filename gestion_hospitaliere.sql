-- Création de la base de données
CREATE DATABASE IF NOT EXISTS floreal_db;

-- Utilisation de la base de données
USE floreal_db;

-- Création de la table admin
CREATE TABLE admin (
  id INT(11) AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(225) DEFAULT NULL,
  prenom VARCHAR(225) DEFAULT NULL,
  email_admin VARCHAR(255) NOT NULL UNIQUE,
  numero_telephone VARCHAR(15) DEFAULT NULL,
  password VARCHAR(255) NOT NULL,
  date_inscription TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  date_modification TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Creation de la table patient
CREATE TABLE patient (
  id INT(11) AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(225) NOT NULL,
  prenom VARCHAR(225) NOT NULL,
  email_patient VARCHAR(255) DEFAULT NULL,
  date_naissance DATE DEFAULT NULL,
  sexe ENUM('Homme', 'Femme') DEFAULT NULL,
  adresse TEXT DEFAULT NULL,
  ville VARCHAR(30) DEFAULT NULL,
  numero_telephone VARCHAR(15) DEFAULT NULL,
  profession VARCHAR(100) DEFAULT NULL,
  date_inscription TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  date_modification TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;




-- Creation de la table perssonne a prevenir
CREATE TABLE personne_prevenir (
  id INT AUTO_INCREMENT PRIMARY KEY,
  patient_id INT NOT NULL,

  nom VARCHAR(100) NOT NULL,
  prenom VARCHAR(100) NOT NULL,
  profession VARCHAR(100) DEFAULT NULL,
  telephone VARCHAR(15) NOT NULL,
  type_personne VARCHAR(50) DEFAULT NULL, -- ex: parent, ami, conjoint

  FOREIGN KEY (patient_id) REFERENCES patient(id) ON DELETE CASCADE
);

-- Creation de la table assurance
CREATE TABLE assurance (
  id INT AUTO_INCREMENT PRIMARY KEY,
  patient_id INT NOT NULL,

  type_assurance VARCHAR(100) NOT NULL,
  numero_assurance VARCHAR(100) NOT NULL,
  pourcentage DECIMAL(5,2) DEFAULT 0,

  FOREIGN KEY (patient_id) REFERENCES patient(id) ON DELETE CASCADE
);


-- Creation de la table categorie_medicament
CREATE TABLE categorie_medicament (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(100) NOT NULL UNIQUE,
  description TEXT DEFAULT NULL,
  date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO categorie_medicament (nom, description) VALUES
('Antibiotiques', 'Médicaments utilisés pour traiter les infections bactériennes'),
('Antalgiques', 'Médicaments contre la douleur'),
('Anti-inflammatoires', 'Médicaments qui réduisent l’inflammation et la douleur'),
('Antipyrétiques', 'Médicaments contre la fièvre'),
('Antipaludiques', 'Médicaments pour le traitement du paludisme'),
('Vitamines et compléments', 'Suppléments nutritionnels et vitamines'),
('Antihypertenseurs', 'Médicaments pour traiter l’hypertension artérielle'),
('Antidiabétiques', 'Médicaments pour le diabète'),
('Antihistaminiques', 'Médicaments contre les allergies'),
('Anesthésiques', 'Médicaments utilisés pour endormir ou réduire la douleur pendant les soins'),
('Antiviraux', 'Médicaments contre les infections virales'),
('Antifongiques', 'Médicaments contre les infections fongiques');


-- Creation de la table medicament
CREATE TABLE medicament (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(255) NOT NULL,
  description TEXT DEFAULT NULL,
  categorie_id INT NOT NULL,
  forme VARCHAR(100) DEFAULT NULL,
  dosage VARCHAR(100) DEFAULT NULL,
  prix_unitaire DECIMAL(10,2) DEFAULT 0,
  quantite_stock INT DEFAULT 0,
  seuil_alerte INT DEFAULT 5,
  date_expiration DATE DEFAULT NULL,
  date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  FOREIGN KEY (categorie_id) REFERENCES categorie_medicament(id)
);