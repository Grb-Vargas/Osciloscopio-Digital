#include <SPI.h> // Incluir librería SPI para comunicar con MCP3204

const int CS_PIN = 10; // Pin de selección de chip (CS)

void setup() {
  Serial.begin(115200);       // Iniciar monitor serial
  SPI.begin();              // Iniciar bus SPI
  pinMode(CS_PIN, OUTPUT);  // CS como salida
  digitalWrite(CS_PIN, HIGH); // Mantener CS en alto por defecto
}

// Función para leer un canal del MCP3204
int leerMCP3204(int canal) {
  if (canal < 0 || canal > 3) return -1; // Validar canal (0 a 3)

  byte startBit = 0b00000110;  // Byte 1: Start bit (1), modo single-ended (1), bit 2 canal (D1)
  byte canalBits = (canal & 0x03) << 6; // Byte 2: Bits D1 y D0 de canal en los bits 7 y 6

  digitalWrite(CS_PIN, LOW); // Activar el chip
  SPI.transfer(startBit);    // Enviar primer byte (start + single + D2 canal)
  int resultado = SPI.transfer(canalBits); // Enviar segundo byte (D1 y D0 del canal)
  resultado = (resultado & 0x0F) << 8; // Solo los 4 bits inferiores son útiles → bits 11–8
  resultado |= SPI.transfer(0x00);     // Leer bits 7–0 del resultado
  digitalWrite(CS_PIN, HIGH); // Desactivar el chip

  return resultado; // Valor de 12 bits (0–4095)
}

void loop() {
  //int valorADC = leerMCP3204(0); // Leer canal CH0
  //float voltaje = valorADC * (5.0 / 4095.0); // Convertir a voltios

  //Serial.print("Valor ADC: ");
  //Serial.print(valorADC);
  //Serial.print(" | Voltaje: ");
  //Serial.println(voltaje, 3); // Mostrar con 3 decimales

  //delay(200); // Esperar 200 ms antes de la siguiente lectura

  int valorCH0 = leerMCP3204(0); // Leer canal CH0
  int valorCH1 = leerMCP3204(1);
  Serial.print(valorCH0);
  Serial.print(",");  
  Serial.println(valorCH1);      // Solo imprime el número
  //delay(5);                      // Frecuencia de muestreo ~200Hz
}