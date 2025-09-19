import mysql.connector
import paho.mqtt.client as mqtt
import json
from datetime import datetime
import time

# Configuración de la conexión a MySQL
db_config = {
    'host': 'localhost',          #IP del servidor MySQL
    'user': 'root',   #usuario de MySQL
    'password': '56FN8tanK@w.', #contraseña de MySQL
    'database': 'sistema_iluminacion'  #Base de datos
}

# Configuración del broker MQTT
broker_address = "broker.hivemq.com"
broker_port = 1883

# Tópicos a los que nos suscribiremos
topics = [
    "SistemaIluminacion/NivelLuz",
    "SistemaIluminacion/EstadoLED", 
    "SistemaIluminacion/Estado"
]

# Variables globales para almacenar los datos recibidos
datos_sensor = {
    'nivel_luz': None,
    'estado_leds': None,
    'estado_sistema': None,
    'timestamp': None
}

def crear_base_datos():
    """Crear la base de datos y tabla si no existen"""
    try:
        # Conectar sin especificar base de datos para crearla
        conn = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password']
        )
        cursor = conn.cursor()
        
        # Crear base de datos
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
        cursor.execute(f"USE {db_config['database']}")
        
        # Crear tabla para datos del sistema de iluminación
        create_table_query = """
        CREATE TABLE IF NOT EXISTS datos_iluminacion (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nivel_luz INT NOT NULL,
            estado_led_principal VARCHAR(10),
            estado_led_extra VARCHAR(10),
            estado_sistema VARCHAR(255),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_table_query)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Base de datos y tabla creadas correctamente")
        
    except mysql.connector.Error as error:
        print(f"Error al crear la base de datos: {error}")

def conectar_mysql():
    """Establecer conexión con MySQL"""
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as error:
        print(f"Error al conectar con MySQL: {error}")
        return None

def parsear_estado_leds(estado_leds_str):
    """Extraer el estado individual de cada LED"""
    try:
        # Formato: "LED_PRINCIPAL:ON,LED_EXTRA:OFF"
        estados = estado_leds_str.split(',')
        led_principal = estados[0].split(':')[1]  # ON/OFF
        led_extra = estados[1].split(':')[1]      # ON/OFF
        return led_principal, led_extra
    except:
        return "UNKNOWN", "UNKNOWN"

def insertar_datos():
    """Insertar datos completos en MySQL cuando estén todos disponibles"""
    if all(v is not None for v in [datos_sensor['nivel_luz'], 
                                   datos_sensor['estado_leds'], 
                                   datos_sensor['estado_sistema']]):
        
        connection = conectar_mysql()
        if connection is None:
            return
            
        try:
            cursor = connection.cursor()
            
            # Parsear estado de LEDs
            led_principal, led_extra = parsear_estado_leds(datos_sensor['estado_leds'])
            
            # Insertar datos
            insert_query = """
            INSERT INTO datos_iluminacion 
            (nivel_luz, estado_led_principal, estado_led_extra, estado_sistema) 
            VALUES (%s, %s, %s, %s)
            """
            
            valores = (
                datos_sensor['nivel_luz'],
                led_principal,
                led_extra,
                datos_sensor['estado_sistema']
            )
            
            cursor.execute(insert_query, valores)
            connection.commit()
            
            print("=" * 50)
            print(f"DATOS GUARDADOS EN MySQL - {datetime.now()}")
            print(f"Nivel de luz: {datos_sensor['nivel_luz']}")
            print(f"LED Principal: {led_principal}")
            print(f"LED Extra: {led_extra}")
            print(f"Estado: {datos_sensor['estado_sistema']}")
            print("=" * 50)
            
            # Resetear datos después de guardar
            for key in datos_sensor:
                if key != 'timestamp':
                    datos_sensor[key] = None
                    
        except mysql.connector.Error as error:
            print(f"Error al insertar datos: {error}")
        finally:
            cursor.close()
            connection.close()

def on_connect(client, userdata, flags, rc):
    """Callback cuando se conecta al broker MQTT"""
    if rc == 0:
        print("Conectado exitosamente al broker MQTT HiveMQ")
        print("Suscribiéndose a los tópicos del sistema de iluminación...")
        
        # Suscribirse a todos los tópicos
        for topic in topics:
            client.subscribe(topic)
            print(f"  - Suscrito a: {topic}")
            
    else:
        print(f"Fallo en la conexión al broker. Código: {rc}")

def on_message(client, userdata, msg):
    """Callback cuando se recibe un mensaje MQTT"""
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    
    print(f"Mensaje recibido -> Tópico: {topic}, Datos: {payload}")
    
    # Procesar según el tópico
    if topic == "SistemaIluminacion/NivelLuz":
        datos_sensor['nivel_luz'] = int(payload)
        
    elif topic == "SistemaIluminacion/EstadoLED":
        datos_sensor['estado_leds'] = payload
        
    elif topic == "SistemaIluminacion/Estado":
        datos_sensor['estado_sistema'] = payload
    
    datos_sensor['timestamp'] = datetime.now()
    
    # Intentar insertar datos si están completos
    insertar_datos()

def main():
    """Función principal"""
    print("Iniciando sistema de recepción MQTT para MySQL")
    print("Sistema de Iluminación IoT - Escalado desde evidencia 1")
    print("-" * 60)
    
    # Crear base de datos y tabla
    crear_base_datos()
    
    # Configurar cliente MQTT
    client_id = f"PythonReceiver_{int(time.time())}"
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id)
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        # Conectar al broker
        print(f"Conectando a {broker_address}:{broker_port}")
        client.connect(broker_address, broker_port, 60)
        
        print("Sistema listo para recibir datos del ESP32...")
        print("Presiona Ctrl+C para detener")
        
        # Mantener el cliente ejecutándose
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\nDeteniendo el sistema...")
        client.disconnect()
        print("Sistema detenido correctamente")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()