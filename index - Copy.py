import threading
import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import tkinter as tk
import pandas as pd

# ====== CONFIGURACIÓN SERIAL ======
PUERTO = 'COM6'
VELOCIDAD = 115200

# ====== BUFFER Y ESCALAS ======
BUFFER_SIZE_MAX = 1000
valores_ch0 = deque([0]*BUFFER_SIZE_MAX, maxlen=BUFFER_SIZE_MAX)
valores_ch1 = deque([0]*BUFFER_SIZE_MAX, maxlen=BUFFER_SIZE_MAX)
buffer_lock = threading.Lock()

escala_vertical = [0, 4095]
ventana_muestras = 200
pausado = False

# ====== LECTURA SERIAL ======
def leer_serial():
    while True:
        try:
            linea = ser.readline().decode('utf-8', errors='ignore').strip()
            partes = linea.split(',')
            if len(partes) == 2 and partes[0].isdigit() and partes[1].isdigit():
                ch0 = int(partes[0])
                ch1 = int(partes[1])
                with buffer_lock:
                    valores_ch0.append(ch0)
                    valores_ch1.append(ch1)
        except Exception as e:
            print("Error:", e)

ser = serial.Serial(PUERTO, VELOCIDAD, timeout=1)
ser.reset_input_buffer()
threading.Thread(target=leer_serial, daemon=True).start()

plt.style.use('dark_background') #REVISAR OJO

# ====== INTERFAZ DE GRÁFICO ======
fig, ax = plt.subplots()
linea_ch0, = ax.plot([], [], color='blue', label='CH0')
linea_ch1, = ax.plot([], [], color='red', label='CH1')
ax.set_title("Osciloscopio Digital")
ax.set_ylabel("Valor ADC")
ax.set_xlabel("Tiempo (muestras)")
ax.set_ylim(*escala_vertical)
ax.set_xlim(0, ventana_muestras)

# ====== ACTUALIZACIÓN DINÁMICA ======
def actualizar(frame):
    if pausado:
        return linea_ch0, linea_ch1
    with buffer_lock:
        datos_ch0 = list(valores_ch0)[-ventana_muestras:]
        datos_ch1 = list(valores_ch1)[-ventana_muestras:]
    linea_ch0.set_data(range(len(datos_ch0)), datos_ch0)
    linea_ch1.set_data(range(len(datos_ch1)), datos_ch1)
    ax.set_xlim(0, ventana_muestras)
    return linea_ch0, linea_ch1

# ====== CONTROL DE TECLADO ======
def on_key(event):
    global escala_vertical, ventana_muestras
    if event.key == 'up':
        escala_vertical[1] = max(escala_vertical[1] - 500, 100)
    elif event.key == 'down':
        escala_vertical[1] = min(escala_vertical[1] + 500, 4095)
    elif event.key == 'r':
        escala_vertical = [0, 4095]
        ventana_muestras = 200
    elif event.key == 'left':
        ventana_muestras = max(50, ventana_muestras - 50)
    elif event.key == 'right':
        ventana_muestras = min(BUFFER_SIZE_MAX, ventana_muestras + 50)

    ax.set_ylim(*escala_vertical)
    print(f"Vertical: {escala_vertical}, Horizontal: {ventana_muestras}")

fig.canvas.mpl_connect('key_press_event', on_key)

# ====== FUNCIONES ADICIONALES ======
def exportar_csv():
    with buffer_lock:
        datos_ch0 = list(valores_ch0)
        datos_ch1 = list(valores_ch1)
    df = pd.DataFrame({'CH0': datos_ch0, 'CH1': datos_ch1})
    df.to_csv('datos_capturados.csv', index=False)
    print("Datos exportados a 'datos_capturados.csv'")

def pausar_reanudar():
    global pausado
    pausado = not pausado
    estado = "Pausado" if pausado else "Reanudado"
    print(f"Estado: {estado}")

def guardar_imagen():
    fig.savefig("captura_osciloscopio.png")
    print("Gráfico guardado como 'captura_osciloscopio.png'")

def crear_ventana_csv():
    ventana = tk.Tk()
    ventana.title("Opciones del Osciloscopio")
    ventana.geometry("300x180")

    boton_csv = tk.Button(ventana, text="Exportar CSV", command=exportar_csv)
    boton_csv.pack(pady=5)

    boton_pausa = tk.Button(ventana, text="Pausar/Reanudar", command=pausar_reanudar)
    boton_pausa.pack(pady=5)

    boton_imagen = tk.Button(ventana, text="Guardar Imagen", command=guardar_imagen)
    boton_imagen.pack(pady=5)
    
    ventana.mainloop()

# Lanzar interfaz de botones
threading.Thread(target=crear_ventana_csv, daemon=True).start()

# Animación y ejecución
ani = animation.FuncAnimation(fig, actualizar, interval=10, blit=False)
plt.grid()
plt.show()