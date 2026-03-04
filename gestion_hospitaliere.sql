-- Création de la base de données
CREATE DATABASE IF NOT EXISTS gestion_hospitaliere;

-- Utilisation de la base de données
USE gestion_hospitaliere;

-- Création de la table admin
CREATE TABLE admin (
  id INT(11) AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(225) DEFAULT NULL,
  prenom VARCHAR(225) DEFAULT NULL,
  email_admin VARCHAR(255) NOT NULL UNIQUE,
  numero_telephone VARCHAR(15) DEFAULT NULL,
  password VARCHAR(255) NOT NULL,
  date_inscription TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Creation de la table patient
CREATE TABLE patient (
  ident INT(11) AUTO_INCREMENT PRIMARY KEY,
  nom_complet VARCHAR(225) NOT NULL,
  date_naissance DATE DEFAULT NULL,
  sexe ENUM('Homme', 'Femme') DEFAULT NULL,
  adresse TEXT DEFAULT NULL,
  ville VARCHAR(30) DEFAULT NULL,
  pays VARCHAR(30) DEFAULT NULL,
  numero_telephone VARCHAR(15) DEFAULT NULL,
  date_inscription TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;