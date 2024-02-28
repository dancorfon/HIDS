import os

def generar_archivos_txt(carpeta_guardado, cantidad_archivos=50):
    # Verificar si la carpeta de guardado existe, si no, crearla
    if not os.path.exists(carpeta_guardado):
        os.makedirs(carpeta_guardado)

    # Contenido base para cada archivo
    contenido_base = """\
Este es un ejemplo de archivo de texto.
Puedes escribir aquí lo que desees.
"""

    # Generar los archivos
    for i in range(1, cantidad_archivos+1):
        nombre_archivo = f"archivo_{i}.txt"
        ruta_completa = os.path.join(carpeta_guardado, nombre_archivo)
        contenido = f"{contenido_base}\nEste es el archivo número {i}."

        with open(ruta_completa, 'w') as archivo:
            archivo.write(contenido)

        print(f'Se ha generado el archivo "{nombre_archivo}" en la carpeta "{carpeta_guardado}".')

# Carpeta donde se guardarán los archivos
carpeta_guardado = 'archivos_generados'

# Llamada a la función para generar los archivos
generar_archivos_txt("Users\danie\OneDrive\Desktop\SSI\PAI 1\Archivos", cantidad_archivos=50)
