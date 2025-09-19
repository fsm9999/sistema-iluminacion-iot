CREATE DATABASE sistema_iluminacion;
USE sistema_iluminacion;

CREATE TABLE datos_iluminacion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nivel_luz INT NOT NULL,
    estado_led_principal VARCHAR(10),
    estado_led_extra VARCHAR(10),
    estado_sistema VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);