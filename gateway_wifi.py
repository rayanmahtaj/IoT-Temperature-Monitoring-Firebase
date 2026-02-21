SSID = 'VOTRE_NOM_WIFI'
PASSWORD = 'VOTRE_MOT_DE_PASSE'
import machine
import network
import urequests
import time

# Variables globales pour la gestion des alertes SMS
LAST_SMS_TIME = 0
SMS_INTERVAL = 15 # Intervalle minimum entre deux SMS d'alerte (en secondes)
ALERT_ACTIVE = False # Indique si l'alerte (température > 25°C) est actuellement active

def send_sms(message):
    try:
        phone = "+000000000000"  # ton numéro complet avec indicatif
        apikey = "VOTRE_CLE_API"       # clé API reçue depuis CallMeBot
        
        # encoder les espaces et caractères spéciaux
        message_encoded = message.replace(" ", "%20")
        
        url = "https://api.callmebot.com/whatsapp.php?phone={}&text={}&apikey={}".format(
            phone,
            message_encoded,
            apikey
        )
        
        response = urequests.get(url)
        print("SMS envoyé :", response.text)
        response.close()
        
        # Mettre à jour le temps du dernier SMS envoyé (NÉCESSAIRE ici)
        global LAST_SMS_TIME
        LAST_SMS_TIME = time.time()

    except Exception as e:
        print("Erreur envoi SMS:", e)


# --- Connexion WiFi ---
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
print("Connexion au WiFi...")
wlan.connect(SSID, PASSWORD)

# Attendre la connexion (max 10 secondes)
for i in range(10):
    if wlan.isconnected():
        break
    time.sleep(1)

if wlan.isconnected():
    print("Connecté au WiFi:", wlan.ifconfig())
else:
    print("Impossible de se connecter au WiFi")
    raise SystemExit

# ---------- UART pour lire Arduino ----------
uart = machine.UART(1, tx=17, rx=16, baudrate=9600)  # TX/RX selon ton câblage

# ---------- Firebase ----------
FIREBASE_URL = 'https://led-statue-a48fc-default-rtdb.firebaseio.com/'

def send_to_firebase(path, value):
    if wlan.isconnected():
        try:
            urequests.put(FIREBASE_URL + path + '.json', json=value).close()
            print(f"Donnée envoyée: {path} -> {value}")
        except Exception as e:
            print("Erreur Firebase:", e)
    else:
        print("Pas de connexion WiFi, données non envoyées")

# ---------- Boucle principale ----------
while True:
    if uart.any():
        line = uart.readline()
        if line:
            line = line.decode().strip()
            print("Reçu de Arduino:", line)  # Affichage pour debug

            # Essayer de convertir en float / int si possible
            try:
                parts = line.split(',')
                if len(parts) == 3:  # Format attendu : "temp,hum,fan"
                    temp = float(parts[0])
                    hum = float(parts[1])
                    fan = int(parts[2])
                    
                    # Envoyer à Firebase
                    send_to_firebase('/Temperature', temp)
                    send_to_firebase('/Humidity', hum)
                    send_to_firebase('/Fan', fan)

                    # LOGIQUE D'ALERTE WHATSAPP
                    current_time = time.time()
                    # Suppression des déclarations 'global' ici pour éviter la SyntaxError

                    if temp > 25:
                        # Si la température dépasse 25°C
                        if not ALERT_ACTIVE:
                            # Premier message d'alerte (déclenchement)
                            send_sms("⚠️ Alerte CRITIQUE ! La température atteint {}°C. Action immédiate requise.".format(temp))
                            ALERT_ACTIVE = True
                        elif current_time - LAST_SMS_TIME >= SMS_INTERVAL:
                            # Message de rappel (avec temporisation de 15s)
                            send_sms("⚠️ Alerte RAPPEL ! La température est toujours à {}°C.".format(temp))
                            
                    elif temp <= 25 and ALERT_ACTIVE:
                        # Si la température redescend en dessous ou égale à 25°C ET que l'alerte était active
                        send_sms("✅ Température sous seuil critique.")
                        ALERT_ACTIVE = False
                        
            except Exception as e:
                print("Erreur conversion UART:", e)

    time.sleep(0.1)