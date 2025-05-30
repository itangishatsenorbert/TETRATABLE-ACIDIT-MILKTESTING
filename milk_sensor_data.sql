-- =============================================
-- MILK QUALITY MONITORING DATABASE - UPDATED VERSION
-- =============================================

-- 1. Remove existing database if needed
DROP DATABASE IF EXISTS milk_sensor_data;

-- 2. Create new database
CREATE DATABASE milk_sensor_data;
USE milk_sensor_data;

-- 3. Set character encoding
ALTER DATABASE milk_sensor_data CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 4. Create main measurement table
CREATE TABLE milk_test (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titrable_acidity FLOAT NOT NULL,
    calculated_ta FLOAT DEFAULT NULL, -- New column for Arduino-calculated TA
    status ENUM('Fresh','Acceptable','Bad','Spoiled','Simulated','Unknown') NOT NULL DEFAULT 'Unknown',
    is_simulated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_ta_range CHECK (titrable_acidity BETWEEN 0 AND 1),
    INDEX idx_status (status),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Create temperature table
CREATE TABLE temperature (
    id INT AUTO_INCREMENT PRIMARY KEY,
    milk_test_id INT NOT NULL,
    temperature_value FLOAT NOT NULL,
    raw_temperature_value FLOAT DEFAULT NULL, -- New column for raw sensor data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_temp_range CHECK (temperature_value BETWEEN -20 AND 100),
    FOREIGN KEY (milk_test_id) REFERENCES milk_test(id) ON DELETE CASCADE,
    INDEX idx_milk_test (milk_test_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Create pH measurements table
CREATE TABLE ph (
    id INT AUTO_INCREMENT PRIMARY KEY,
    milk_test_id INT NOT NULL,
    ph_value FLOAT NOT NULL,
    raw_ph_value FLOAT DEFAULT NULL, -- New column for raw sensor data
    temperature_compensated FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_ph_range CHECK (ph_value BETWEEN 0 AND 14),
    FOREIGN KEY (milk_test_id) REFERENCES milk_test(id) ON DELETE CASCADE,
    INDEX idx_milk_test (milk_test_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Create conductivity table
CREATE TABLE conductivity (
    id INT AUTO_INCREMENT PRIMARY KEY,
    milk_test_id INT NOT NULL,
    conductivity_value FLOAT NOT NULL,
    raw_conductivity_value FLOAT DEFAULT NULL, -- New column for raw sensor data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_cond_range CHECK (conductivity_value >= 0),
    FOREIGN KEY (milk_test_id) REFERENCES milk_test(id) ON DELETE CASCADE,
    INDEX idx_milk_test (milk_test_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. Create optimized view
CREATE OR REPLACE VIEW sensor_readings AS
SELECT 
    m.id,
    m.titrable_acidity AS ta,
    m.calculated_ta, -- Include Arduino-calculated TA
    m.status,
    m.is_simulated,
    t.temperature_value AS temp,
    t.raw_temperature_value AS raw_temp, -- Include raw temperature
    p.ph_value AS ph,
    p.raw_ph_value AS raw_ph, -- Include raw pH
    p.temperature_compensated AS adjusted_ph,
    c.conductivity_value AS cond,
    c.raw_conductivity_value AS raw_cond, -- Include raw conductivity
    m.created_at
FROM milk_test m
LEFT JOIN temperature t ON m.id = t.milk_test_id
LEFT JOIN ph p ON m.id = p.milk_test_id
LEFT JOIN conductivity c ON m.id = c.milk_test_id
ORDER BY m.created_at DESC;

-- 9. Create stored procedure
DELIMITER //
CREATE PROCEDURE insert_sensor_data(
    IN p_ta FLOAT,
    IN p_temp FLOAT,
    IN p_raw_temp FLOAT, -- New parameter for raw temperature
    IN p_ph FLOAT,
    IN p_raw_ph FLOAT, -- New parameter for raw pH
    IN p_cond FLOAT,
    IN p_raw_cond FLOAT, -- New parameter for raw conductivity
    IN p_status VARCHAR(20),
    IN p_is_simulated BOOLEAN
)
BEGIN
    DECLARE v_milk_id INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    INSERT INTO milk_test (titrable_acidity, calculated_ta, status, is_simulated)
    VALUES (p_ta, p_ta, p_status, p_is_simulated); -- Store calculated TA
    
    SET v_milk_id = LAST_INSERT_ID();
    
    INSERT INTO temperature (milk_test_id, temperature_value, raw_temperature_value)
    VALUES (v_milk_id, p_temp, p_raw_temp);
    
    INSERT INTO ph (milk_test_id, ph_value, raw_ph_value, temperature_compensated)
    VALUES (v_milk_id, p_ph, p_raw_ph, p_ph + (0.03 * (p_temp - 20)));
    
    INSERT INTO conductivity (milk_test_id, conductivity_value, raw_conductivity_value)
    VALUES (v_milk_id, p_cond, p_raw_cond);
    
    COMMIT;
END //
DELIMITER ;

-- 10. Create error logging table (for event error handling)
CREATE TABLE error_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message VARCHAR(255) NOT NULL,
    error_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_error_time (error_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 11. Enable event scheduler (must be done with SUPER privileges)
SET GLOBAL event_scheduler = ON;

-- 12. Create cleanup event with improved error handling
DELIMITER //
CREATE EVENT IF NOT EXISTS purge_old_data
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP + INTERVAL 1 DAY
DO
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        INSERT INTO error_logs (message) 
        VALUES (CONCAT('Purge failed at ', NOW(), ': ', COALESCE(ERROR_MESSAGE(), 'Unknown error')));
    END;
    
    DELETE FROM milk_test WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
    
    -- Optional: Add logging of purge operation
    INSERT INTO error_logs (message)
    VALUES (CONCAT('Purge completed at ', NOW(), ': ', ROW_COUNT(), ' records deleted'));
END //
DELIMITER ;

-- 13. Verification queries
SHOW VARIABLES LIKE 'event_scheduler';
SHOW EVENTS FROM milk_sensor_data;
SELECT TABLE_NAME FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'milk_sensor_data';