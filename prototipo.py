import threading
import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import tkinter as tk
from tkinter import ttk
import pandas as pd
import sys
import serial.tools.list_ports

# ====== CONFIGURACIÓN SERIAL ======
#PUERTO = 'COM6'
#VELOCIDAD = 115200

# ====== BUFFER Y ESCALAS ======
BUFFER_SIZE_MAX = 1000
valores_ch0 = deque([0]*BUFFER_SIZE_MAX, maxlen=BUFFER_SIZE_MAX)
valores_ch1 = deque([0]*BUFFER_SIZE_MAX, maxlen=BUFFER_SIZE_MAX)
buffer_lock = threading.Lock()

escala_vertical = [0, 4095]
ventana_muestras = 200
pausado = False
AE_CH0 = True
AE_CH1 = True

############REDIRECCION DE MENSAJES A ELEMENTO TEXT############
class RedirectText:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)

    def flush(self):
        pass


# ====== LECTURA SERIAL ======
def leer_serial(puerto):
    global ser
    ser = serial.Serial(puerto, 115200, timeout=1)
    ser.reset_input_buffer()

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

def iniciar_lectura():
    puerto = combobox_puertos.get()
    threading.Thread(target=leer_serial, args=(puerto,), daemon=True).start()

plt.style.use('dark_background')

# ====== INTERFAZ DE GRÁFICO ======
fig, ax = plt.subplots()
fig.patch.set_facecolor('mediumblue')
linea_ch0, = ax.plot([], [], color='blue', label='CH0')
linea_ch1, = ax.plot([], [], color='red', label='CH1')
ax.set_title("Osciloscopio Digital", loc='left', pad=20, fontsize=14, color='yellow')
ax.set_ylabel("Valor ADC", color='yellow', labelpad=20)
ax.set_xlabel("Tiempo (muestras)", color='yellow')
ax.set_ylim(*escala_vertical)
ax.set_xlim(0, ventana_muestras)
    
#texto_adicional = "MCP3204 (12Bits)"
#ax.text(0.8, 1.05, texto_adicional, fontsize=10, ha='center', va='bottom', color='white', fontname='sans-serif', 
#        bbox=dict(facecolor='black', alpha=1, edgecolor='none', boxstyle='round,pad=0.5'))

# ====== ACTUALIZACIÓN DINÁMICA ======
def actualizar(frame):
    if pausado:
        return linea_ch0, linea_ch1
    with buffer_lock:
        datos_ch0 = list(valores_ch0)[-ventana_muestras:]
        datos_ch1 = list(valores_ch1)[-ventana_muestras:]
    
    ####Control Logica de Canales####
    if AE_CH0:
        linea_ch0.set_data(range(len(datos_ch0)), datos_ch0)
    else:
        linea_ch0.set_data([], [])

    if AE_CH1:
        linea_ch1.set_data(range(len(datos_ch1)), datos_ch1)
    else:
        linea_ch1.set_data([], [])

    #linea_ch0.set_data(range(len(datos_ch0)), datos_ch0)
    #linea_ch1.set_data(range(len(datos_ch1)), datos_ch1)
    ax.set_xlim(0, ventana_muestras)
    return linea_ch0, linea_ch1

# ====== CONTROL DE TECLADO ======
def on_key(event):
    global ventana_muestras
    if event.key == 'r':
        ventana_muestras = 200

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

def actualizar_escala_vertical(value):
    global escala_vertical
    escala_vertical[1] = int(value)
    ax.set_ylim(*escala_vertical)

def actualizar_ventana_muestras(value):
    global ventana_muestras
    ventana_muestras = int(value)

def cerrar_exit():
    plt.close(fig)
    ventana.quit()
    sys.exit()

####CH0 ON####
def on_ch0():
    global AE_CH0
    AE_CH0 = True
    print("CH0 Encendido")

####CH0 OFF####
def off_ch0():
    global AE_CH0
    AE_CH0 = False
    print("CH0 Apagado")

####CH1 ON####
def on_ch1():
    global AE_CH1
    AE_CH1 = True
    print("CH1 Encendido")

####CH1 OFF####
def off_ch1():
    global AE_CH1
    AE_CH1 = False
    print("CH1 Apagado")

def crear_ventana_csv():
    global ventana, combobox_puertos
    ventana = tk.Tk()
    ventana.title("Opciones del Osciloscopio")
    ventana.geometry("590x510")

    ####Obtener puertos COM disponibles####
    puertos = [port.device for port in serial.tools.list_ports.comports()]

    ####Crear Combobox para seleccionar puertos####
    combobox_puertos = ttk.Combobox(ventana, values=puertos)
    combobox_puertos.grid(row=4, column=0, padx=5, pady=5)
    combobox_puertos.set("Selecciona un puerto")

    ####Botón para iniciar lectura####
    boton_iniciar = tk.Button(ventana, text="Iniciar Lectura", command=iniciar_lectura, bd=2, relief='groove', bg='lightgray')
    boton_iniciar.grid(row=5, column=0, padx=5, pady=5)

    ####Botón para exportar CSV####
    boton_csv = tk.Button(ventana, text="Exportar CSV", command=exportar_csv, bd=2, relief='groove', bg='lightgray')
    boton_csv.grid(row=0, column=0, padx=5, pady=5)

    # Botón para pausar/reanudar
    boton_pausa = tk.Button(ventana, text="Pausar/Reanudar", command=pausar_reanudar, bd=2, relief='groove', bg='lightgray')
    boton_pausa.grid(row=0, column=1, padx=5, pady=10)

    #####Botón para guardar imagen####
    boton_imagen = tk.Button(ventana, text="Guardar Imagen", command=guardar_imagen, bd=2, relief='groove', bg='lightgray')
    boton_imagen.grid(row=0, column=2, padx=5, pady=10)

    ####Botón para cerrar el programa####
    boton_cerrar = tk.Button(ventana, text="Cerrar", command=cerrar_exit, bd=2, relief='groove', bg='lightgray')
    boton_cerrar.grid(row=6, column=0, padx=5, pady=10)

    ####Indicadores de color para CH0 y CH1####
    etiqueta_ch0 = tk.Label(ventana, text="CH0", bg='royalblue', fg='white', width=10)
    etiqueta_ch0.grid(row=3, column=1, padx=5, pady=5)

    etiqueta_ch1 = tk.Label(ventana, text="CH1", bg='salmon', fg='white', width=10)
    etiqueta_ch1.grid(row=3, column=2, padx=5, pady=5)

    ####Botones para encender/apagar CH0####
    boton_encender_ch0 = tk.Button(ventana, text="Encender CH0", command=on_ch0, bd=2, relief='groove', bg='lightgray')
    boton_encender_ch0.grid(row=4, column=1, padx=5, pady=5)

    boton_apagar_ch0 = tk.Button(ventana, text="Apagar CH0", command=off_ch0, bd=2, relief='groove', bg='lightgray')
    boton_apagar_ch0.grid(row=5, column=1, padx=5, pady=5)

    ####Botones para encender/apagar CH1####
    boton_encender_ch1 = tk.Button(ventana, text="Encender CH1", command=on_ch1, bd=2, relief='groove', bg='lightgray')
    boton_encender_ch1.grid(row=4, column=2, padx=5, pady=5)

    boton_apagar_ch1 = tk.Button(ventana, text="Apagar CH1", command=off_ch1, bd=2, relief='groove', bg='lightgray')
    boton_apagar_ch1.grid(row=5, column=2, padx=5, pady=5)

    ####Escala vertical####
    scale_vertical = tk.Scale(ventana, from_=4095, to=0, orient='vertical', command=actualizar_escala_vertical, tickinterval=820, length=200, bd=2, relief='groove')
    scale_vertical.set(escala_vertical[1])
    scale_vertical.grid(row=2, column=2, padx=5, pady=10)

    etiqueta_escala_vertical = tk.Label(ventana, text="Vertical", bg='lightgray')
    etiqueta_escala_vertical.grid(row=1, column=2, padx=10, pady=10)

    ####Escala Horizontal####
    scale_muestras = tk.Scale(ventana, from_=BUFFER_SIZE_MAX, to=50, orient='vertical', command=actualizar_ventana_muestras, tickinterval=200, length=200, bd=2, relief='groove')
    scale_muestras.set(ventana_muestras)
    scale_muestras.grid(row=2, column=1, padx=5, pady=10)

    etiqueta_ventana_muestras = tk.Label(ventana, text="Horizontal", bg='lightgray')
    etiqueta_ventana_muestras.grid(row=1, column=1, padx=10, pady=10)

    ####Cuadro de texto Consola####
    texto_console = tk.Text(ventana, height=12, width=30, bd=2, relief='groove', bg='white')
    texto_console.grid(row=2, column=0, padx=5, pady=5)

    etiqueta_texto = tk.Label(ventana, text='Consola:')
    etiqueta_texto.grid(row=1, column=0, padx=10, pady=10)

    ####Cuadro de texto Puertos####
    texto_console = tk.Text(ventana, height=12, width=30, bd=2, relief='groove', bg='white')
    texto_console.grid(row=2, column=0, padx=5, pady=5)

    etiqueta_texto = tk.Label(ventana, text='Puertos COM:')
    etiqueta_texto.grid(row=3, column=0, padx=10, pady=10)

    sys.stdout = RedirectText(texto_console)

    ventana.mainloop()



# Lanzar interfaz de botones
threading.Thread(target=crear_ventana_csv, daemon=True).start()

# Animación y ejecución
ani = animation.FuncAnimation(fig, actualizar, interval=10, blit=False)
plt.grid(True, linestyle='--', alpha=0.25)
plt.show()
