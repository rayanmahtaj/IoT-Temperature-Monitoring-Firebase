#include "DHT.h"
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

const int DHT_PIN = A1;
const int DHT_TYPE = DHT11;
const int RELAY_PIN = 8;
const int BUZZER_PIN = 7;       // Buzzer sur broche 7
const float TEMP_SEUIL = 21.0;

// Valeur critique pour URGENT
const float TEMP_CRITIQUE = 25.0;

// LCD 16x2 I2C (adresse 0x27)
LiquidCrystal_I2C lcd(0x27, 16, 2);

DHT dht(DHT_PIN, DHT_TYPE);

void setup() {
  Serial.begin(9600);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);      // Initialisation buzzer
  digitalWrite(RELAY_PIN, HIGH);
  digitalWrite(BUZZER_PIN, LOW);    // Buzzer éteint par défaut
  dht.begin();

  // LCD initialisation
  lcd.init();
  lcd.backlight();
}

void loop() {
  delay(3000);

  float temp = dht.readTemperature();
  float hum = dht.readHumidity();

  if (isnan(temp) || isnan(hum)) return;

  int fan = (temp >= TEMP_SEUIL) ? 1 : 0;
  digitalWrite(RELAY_PIN, (fan == 1) ? LOW : HIGH);

  // ----------- Gestion buzzer -----------  
  if (temp > TEMP_CRITIQUE) {
    digitalWrite(BUZZER_PIN, HIGH);   // buzzer activé
  } else {
    digitalWrite(BUZZER_PIN, LOW);    // buzzer désactivé
  }

  // ----------- Affichage LCD -----------  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Temp: ");
  lcd.print(temp, 1);
  lcd.print("C");

  lcd.setCursor(0, 1);
  if (temp > TEMP_CRITIQUE) {
    lcd.print("URGENT !");
  } else {
    lcd.print("            "); // vide la ligne
  }

  // ----------- Envoi Serial -----------  
  Serial.print(temp, 2);
  Serial.print(",");
  Serial.print(hum, 2);
  Serial.print(",");
  Serial.println(fan);
 delay(3000);
}