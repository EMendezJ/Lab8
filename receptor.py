import paho.mqtt.client as mqtt
import json
import csv
from datetime import datetime
import matplotlib.pyplot as plt

# --- Configuración ---
CSV_FILENAME = "motor_data.csv"
CSV_HEADER = ["timestamp", "rpm", "velocidad_lineal"]
TOPIC = "motor/data" # IMPORTANTE: Debe coincidir con el topic de tu ESP8266

# Listas para almacenar los datos temporalmente y graficarlos al final
tiempos_plot = []
rpm_plot = []
vl_plot = []

# --- Función para escribir los datos al CSV ---
def write_to_csv(timestamp, rpm, vl):
    with open(CSV_FILENAME, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Escribir encabezado solo si el archivo está vacío
        if csvfile.tell() == 0:  
            writer.writerow(CSV_HEADER)
        writer.writerow([timestamp, f"{rpm:.2f}", f"{vl:.2f}"])

# --- Funciones Callbacks de MQTT ---
def on_connect(client, userdata, flags, rc):
    print("Conectado al Broker con código de resultado " + str(rc))
    client.subscribe(TOPIC) 

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        
        rpm = data.get("rpm")
        vl = data.get("vl") 
        
        if rpm is not None and vl is not None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            write_to_csv(timestamp, rpm, vl)
            
            # Imprimir en la terminal de la Pi
            print(f"[{timestamp}] Recibido -> RPM: {rpm:.2f}, Vel Lineal: {vl:.2f} m/s")
            
            # Guardamos en las listas para la gráfica (solo la hora para que se vea bien)
            tiempos_plot.append(datetime.now().strftime("%H:%M:%S"))
            rpm_plot.append(rpm)
            vl_plot.append(vl)
            
        else:
            print("Error: Datos RPM o velocidad lineal no encontrados en el JSON")
            
    except json.JSONDecodeError:
        print("Error: No se pudo decodificar el mensaje JSON")

# --- Configuración del Cliente MQTT ---
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Nos conectamos a "127.0.0.1" (localhost) porque el script y el Broker están en la misma Pi
client.connect("127.0.0.1", 1883, 60) 

print("Escuchando datos del tractor... (Presiona Ctrl+C para detener y generar tu gráfica)")

try:
    # Mantener el script corriendo para recibir mensajes
    client.loop_forever()
    
except KeyboardInterrupt:
    # --- Generación de Gráficas al presionar Ctrl+C ---
    print("\n\nSimulación terminada por el usuario. Generando gráficas...")
    
    if len(tiempos_plot) > 0:
        fig, ax1 = plt.subplots(figsize=(10, 5))

        # Eje Y izquierdo: RPM
        color1 = 'tab:red'
        ax1.set_xlabel('Tiempo (Hora)')
        ax1.set_ylabel('RPM', color=color1)
        ax1.plot(tiempos_plot, rpm_plot, color=color1, marker='o', label='RPM')
        ax1.tick_params(axis='y', labelcolor=color1)
        plt.xticks(rotation=45)

        # Eje Y derecho: Velocidad Lineal
        ax2 = ax1.twinx()  
        color2 = 'tab:blue'
        ax2.set_ylabel('Velocidad Lineal (m/s)', color=color2)  
        ax2.plot(tiempos_plot, vl_plot, color=color2, marker='x', label='Velocidad')
        ax2.tick_params(axis='y', labelcolor=color2)

        fig.tight_layout()  
        plt.title('Telemetría de Motor de Tractor (ESP8266 a Raspberry Pi)')
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Guardar la imagen
        plt.savefig('grafica_tractor.png')
        print("Gráfica guardada exitosamente como 'grafica_tractor.png'")
        print(f"Datos guardados exitosamente en '{CSV_FILENAME}'")
    else:
        print("No se recibieron datos, no se pudo graficar.")
