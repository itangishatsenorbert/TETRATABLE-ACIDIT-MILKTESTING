CREATE DATABASE IF NOT EXISTS TA_milkTest;

USE TA_milkTest;

-- Table to store milk test details
CREATE TABLE milk_test (
    milk_test_id INT AUTO_INCREMENT PRIMARY KEY,
    titrable_acidity DECIMAL(5, 3) NOT NULL,
    status ENUM('Fresh', 'Bad', 'Spoiled') NOT NULL
);

-- Table to store temperature data linked to each milk test
CREATE TABLE temperature (
    temperature_id INT AUTO_INCREMENT PRIMARY KEY,
    milk_test_id INT NOT NULL,
    temperature_value DECIMAL(5, 2) NOT NULL,
    FOREIGN KEY (milk_test_id) REFERENCES milk_test(milk_test_id) ON DELETE CASCADE
);

-- Table to store pH data linked to each milk test
CREATE TABLE ph (
    ph_id INT AUTO_INCREMENT PRIMARY KEY,
    milk_test_id INT NOT NULL,
    ph_value DECIMAL(4, 2) NOT NULL,
    temperature_compensated DECIMAL(4, 2) NOT NULL,
    FOREIGN KEY (milk_test_id) REFERENCES milk_test(milk_test_id) ON DELETE CASCADE
);

-- Table to store conductivity data linked to each milk test
CREATE TABLE conductivity (
    conductivity_id INT AUTO_INCREMENT PRIMARY KEY,
    milk_test_id INT NOT NULL,
    conductivity_value DECIMAL(5, 2) NOT NULL,
    FOREIGN KEY (milk_test_id) REFERENCES milk_test(milk_test_id) ON DELETE CASCADE
);

-- Optional: Table to store timestamp for each milk test
CREATE TABLE test_timestamp (
    timestamp_id INT AUTO_INCREMENT PRIMARY KEY,
    milk_test_id INT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (milk_test_id) REFERENCES milk_test(milk_test_id) ON DELETE CASCADE
);
