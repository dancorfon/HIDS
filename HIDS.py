import os
import hashlib
import sqlite3
import shutil
import time
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import datetime
import logging

# Configuración del archivo de registro
log_file = 'file_integrity.log'
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Carpeta de backup
backup_folder = 'backup'
if not os.path.exists(backup_folder):
    os.makedirs(backup_folder)

# Variable global para controlar la verificación de integridad
stop_verification = False

# Función para calcular el hash de un archivo
def calculate_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        buffer = f.read(65536)
        while len(buffer) > 0:
            hasher.update(buffer)
            buffer = f.read(65536)
    return hasher.hexdigest()

# Función para verificar la integridad de los archivos
def check_integrity():
    global stop_verification
    conn = sqlite3.connect('file_integrity.db')
    c = conn.cursor()
    report_counter = 0

    while True:
        if stop_verification:
            generate_report()  # Generar informe al detener la verificación
            stop_verification = False  # Restablecer la variable de detención
            break

        # Obtener la lista de archivos de la base de datos
        c.execute("SELECT * FROM files")
        files = c.fetchall()

        for file_data in files:
            file_id, file_name, file_path, stored_hash, failed = file_data
            #current_hash = calculate_hash(file_path)
            
            try:
                with open(file_path, 'rb') as f:
                    current_hash = calculate_hash(file_path)
            except FileNotFoundError:
                logging.warning(f'El archivo {file_name} no se ha encontrado en el directorio. Se restaurará desde el backup.')
                c.execute("UPDATE files SET failed = 1 WHERE id = ?", (file_id,))
                conn.commit()
                messagebox.showinfo('Alerta', f'El archivo {file_name} no se ha encontrado en el directorio. Se restaurará desde el backup.')
                shutil.copy(os.path.join(backup_folder, file_name), file_path)


            if current_hash != stored_hash:
                logging.warning(f'El archivo {file_name} ha sido modificado. Se restaurará desde el backup.')
                c.execute("UPDATE files SET failed = 1 WHERE id = ?", (file_id,))
                conn.commit()
                messagebox.showinfo('Alerta', f'El archivo {file_name} ha sido modificado. Se restaurará desde el backup.')
                shutil.copy(os.path.join(backup_folder, file_name), file_path)
                

        time.sleep(15)
        report_counter += 1
        print(report_counter)

        if report_counter % 10 == 0:
            generate_report()
            report_counter = 0

    conn.close()

# Función para generar un informe
def generate_report():
    conn = sqlite3.connect('file_integrity.db')
    c = conn.cursor()

    # Obtener la fecha y hora actual
    now = datetime.datetime.now()
    # Formatear la fecha y hora como parte del nombre del informe
    report_name = f"informe_{now.strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    # Construir la ruta completa del informe
    report_path = os.path.join('informes', report_name)

    # Calcular el porcentaje de aciertos
    c.execute("SELECT COUNT(*) FROM files")
    total_files_checked = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM files WHERE failed = 1")
    alerts = c.fetchone()[0]
    accuracy_percentage = ((total_files_checked - alerts) / total_files_checked) * 100 if total_files_checked > 0 else 0

    # Escribir el contenido del informe
    with open(report_path, 'w') as file:
        file.write("Informe de verificación de integridad:\n")
        file.write(f"Fecha y hora: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"Número de alertas: {alerts}\n")
        file.write(f"Número de archivos verificados: {total_files_checked}\n")
        file.write(f"Porcentaje de aciertos: {accuracy_percentage:.2f}%\n\n")

        # Si hay alertas, escribir la información de alerta
        if alerts > 0:
            file.write("Alertas detectadas:\n")
            c.execute("SELECT name, path FROM files WHERE failed = 1")
            alert_info = c.fetchall()
            for name, path in alert_info:
                file.write(f"Nombre del archivo: {name}\n")
                file.write(f"Ruta del archivo: {path}\n\n")

    print(f"Informe generado: {report_path}")
    logging.info(f"Informe generado: {report_path}")
    # Limpiar la columna 'failed' para la próxima verificación
    c.execute("UPDATE files SET failed = 0")
    conn.commit()
    conn.close()

# Función para seleccionar archivos y guardar en la base de datos
def select_files():
    def add_file():
        file_path = file_entry.get()
        if file_path:
            file_name = os.path.basename(file_path)
            file_hash = calculate_hash(file_path)

            conn = sqlite3.connect('file_integrity.db')
            c = conn.cursor()

            c.execute("INSERT INTO files (name, path, hash, failed) VALUES (?, ?, ?, 0)", (file_name, file_path, file_hash))
            conn.commit()
            shutil.copy(file_path, os.path.join(backup_folder, file_name))

            file_listbox.insert(tk.END, file_name)
            file_entry.delete(0, tk.END)
            conn.close()

    def remove_file():
        selected_index = file_listbox.curselection()
        if selected_index:
            file_name = file_listbox.get(selected_index)
            file_path = os.path.join(backup_folder, file_name)
            os.remove(file_path)

            conn = sqlite3.connect('file_integrity.db')
            c = conn.cursor()

            c.execute("DELETE FROM files WHERE name=?", (file_name,))
            conn.commit()

            file_listbox.delete(selected_index)
            conn.close()

    def verify_integrity():
        global stop_verification
        stop_verification = False
        messagebox.showinfo('Verificación de integridad', 'Se procederá a verificar la integridad de los archivos cada 15 segundos. Si se detecta alguna modificación, se restaurará el archivo original desde el backup.')
        threading.Thread(target=check_integrity, daemon=True).start()

    def stop_verification():
        global stop_verification
        messagebox.showinfo('Parar proceso de verificación de integridad', 'Se procederá a parar el proceso de verificación de la integridad de los archivos seleccionados.')
        stop_verification = True

    root = tk.Tk()
    root.title('HIDS - Sistema de Detección de Intrusiones en Archivos')

    file_label = tk.Label(root, text='Seleccione los archivos que desea verificar:')
    file_label.pack()

    file_entry = tk.Entry(root, width=40)
    file_entry.pack(side=tk.LEFT)

    browse_button = tk.Button(root, text='Buscar', command=lambda: file_entry.insert(tk.END, filedialog.askopenfilename()))
    browse_button.pack(side=tk.LEFT, padx=5)

    add_button = tk.Button(root, text='Agregar archivo', command=add_file)
    add_button.pack(side=tk.LEFT)

    remove_button = tk.Button(root, text='Retirar archivo', command=remove_file)
    remove_button.pack(side=tk.LEFT)

    verify_button = tk.Button(root, text='Verificar integridad', command=verify_integrity)
    verify_button.pack()

    stop_verification_button = tk.Button(root, text='Parar verificación', command=stop_verification)
    stop_verification_button.pack()  # Agregar el botón para detener la verificación

    file_listbox_label = tk.Label(root, text='Archivos seleccionados:')
    file_listbox_label.pack()

    file_listbox = tk.Listbox(root, width=50, height=5)
    file_listbox.pack()

    root.mainloop()

if __name__ == "__main__":

    # Configuración del archivo de registro
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Eliminar la base de datos si existe
    if os.path.exists('file_integrity.db'):
        os.remove('file_integrity.db')

    # Crear una nueva base de datos y la tabla correspondiente
    conn = sqlite3.connect('file_integrity.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS files
                 (id INTEGER PRIMARY KEY, name TEXT, path TEXT, hash TEXT, failed INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

    select_files()
