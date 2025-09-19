//Librerias
#include <WiFi.h>
#include <PubSubClient.h>


// Configuración de WiFi
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// Configuración del broker MQTT HiveMQ
const char* mqtt_server = "broker.hivemq.com";  // Broker público de HiveMQ
const int mqtt_port = 1883; // Puerto MQTT
const char* mqtt_user = ""; // Usuario MQTT
const char* mqtt_password = ""; // Contraseña MQTT

// Tópicos MQTT para el sistema de iluminación
const char* mqtt_topic_luz = "SistemaIluminacion/NivelLuz";   // Nivel de luz ambiente
const char* mqtt_topic_led = "SistemaIluminacion/EstadoLED";    // Estado de LEDs
const char* mqtt_topic_status = "SistemaIluminacion/Estado";    // Estado general del sistema

WiFiClient espClient;   // Cliente WiFi
PubSubClient client(espClient);   // Cliente MQTT

// Configuración de sensores y leds
const int sensor_ldr_pin = 34;    // Pin analógico para sensor LDR
const int led_pin = 2;    // LED principal
const int led_extra_pin = 18;   // LED adicional para poca luz

// Variables para control del sistema
int lectura_luz = 0;
String estado_sistema = "";
String estado_leds = "";
unsigned long ultimo_envio = 0;
const unsigned long intervalo_envio = 5000;  // Enviar datos cada 5 segundos

// Función para conectar a WiFi
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Conectando a ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("Conectado a la red WiFi");
  Serial.print("Dirección IP: ");
  Serial.println(WiFi.localIP());
}

// Función para reconectar al broker MQTT
void reconnect() {
  while (!client.connected()) {
    Serial.print("Intentando conectar al broker MQTT...");
    
    // Generar ID único para client
    String clientId = "ESP32_Iluminacion_" + String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str(), mqtt_user, mqtt_password)) {
      Serial.println("Conectado al broker MQTT");
      Serial.println("Publicando en los tópicos:");
      Serial.println("- " + String(mqtt_topic_luz));
      Serial.println("- " + String(mqtt_topic_led));
      Serial.println("- " + String(mqtt_topic_status));
    } else {
      Serial.print("Fallo, rc=");
      Serial.print(client.state());
      Serial.println(" Intentando de nuevo en 5 segundos");
      delay(5000);
    }
  }
}

// Función para controlar la iluminación
void controlar_iluminacion() {
  lectura_luz = analogRead(sensor_ldr_pin);
  

  if (lectura_luz > 3000) {  // Muy poca luz (24 lux aprox)
    digitalWrite(led_pin, HIGH);
    digitalWrite(led_extra_pin, HIGH);
    estado_sistema = "Muy poca luz - Iluminacion extra activada";
    estado_leds = "LED_PRINCIPAL:ON,LED_EXTRA:ON";
    Serial.println("Hay muy poca luz");
    Serial.println("Iluminación extra activada");
    
  } else if (lectura_luz > 2000) {  // Poca luz (105 lux aprox)
    digitalWrite(led_pin, HIGH);
    digitalWrite(led_extra_pin, LOW);
    estado_sistema = "Poca luz - LED principal encendido";
    estado_leds = "LED_PRINCIPAL:ON,LED_EXTRA:OFF";
    Serial.println("Hay poca luz");
    Serial.println("Led prendido");
    
  } else {  // Buena iluminación
    digitalWrite(led_pin, LOW);
    digitalWrite(led_extra_pin, LOW);
    estado_sistema = "Buena iluminacion - LEDs apagados";
    estado_leds = "LED_PRINCIPAL:OFF,LED_EXTRA:OFF";
    Serial.println("Hay buena iluminación");
    Serial.println("Leds apagados");
  }
}

// Función para enviar datos por MQTT
void enviar_datos_mqtt() {
  if (client.connected()) {
    // Enviar nivel de luz
    String nivel_luz = String(lectura_luz);
    client.publish(mqtt_topic_luz, nivel_luz.c_str());
    
    // Enviar estado de LEDs
    client.publish(mqtt_topic_led, estado_leds.c_str());
    
    // Enviar estado general del sistema
    client.publish(mqtt_topic_status, estado_sistema.c_str());
    
    // Mostrar en monitor serial
    Serial.println("--- Datos enviados por MQTT ---");
    Serial.println("Nivel de luz: " + nivel_luz);
    Serial.println("Estado LEDs: " + estado_leds);
    Serial.println("Estado sistema: " + estado_sistema);
    Serial.println("-------------------------------");
  }
}

// Configuración inicial
void setup() {
  Serial.begin(115200);
  
  // Configurar pines
  pinMode(led_pin, OUTPUT);
  pinMode(led_extra_pin, OUTPUT);
  pinMode(sensor_ldr_pin, INPUT);
  
  // Apagar LEDs inicialmente
  digitalWrite(led_pin, LOW);
  digitalWrite(led_extra_pin, LOW);
  
  // Conectar a WiFi y MQTT
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  
  Serial.println("Sistema de Iluminación IoT iniciado");
  Serial.println("Escalado desde evidencia 1 con conectividad MQTT");
}

// Bucle principal
void loop() {
  // Verificar conexión MQTT
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  // Controlar iluminación
  controlar_iluminacion();
  
  // Enviar datos por MQTT cada 5 segundos
  unsigned long ahora = millis();
  if (ahora - ultimo_envio >= intervalo_envio) {
    enviar_datos_mqtt();
    ultimo_envio = ahora;
  }
  
  // Pausa de 1 segundo
  delay(1000);
}