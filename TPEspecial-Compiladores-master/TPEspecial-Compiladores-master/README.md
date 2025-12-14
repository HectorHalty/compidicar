## COMPILADOR - TPE (Lenguaje a WebAssembly)

Este proyecto implementa un compilador que traduce un lenguaje fuente propio a **WebAssembly (WASM)**. El compilador realiza el análisis léxico, sintáctico y semántico, genera código intermedio (`.wat`), lo ensambla a binario (`.wasm`) y lo ejecuta automáticamente utilizando un entorno de Node.js.

## 📋 PRERREQUISITOS DEL SISTEMA

Para ejecutar este proyecto correctamente en **Windows 11** (o cualquier otro sistema operativo), asegúrate de tener instaladas las siguientes herramientas:

1.  **Python 3.8 o superior**: [Descargar Python](https://www.python.org/downloads/)
    * *Importante:* Durante la instalación, marca la casilla **"Add Python to PATH"**.
2.  **Node.js (Versión LTS)**: [Descargar Node.js](https://nodejs.org/)
    * Necesario para ejecutar el código compilado a través del script `run_wasm.js`.
3.  **WABT (The WebAssembly Binary Toolkit)**:
    * Necesario para la herramienta `wat2wasm` que convierte el código de texto a binario.
    * **Ver sección de Configuración de WABT abajo.**

---

## ⚙️ INSTALACIÓN Y CONFIGURACIÓN

### Paso 1: Configuración de WABT (Crítico para Windows)
El sistema necesita reconocer el comando `wat2wasm` en la terminal.

1.  Descarga el archivo `.zip` para Windows de **WABT** desde [GitHub Releases](https://github.com/WebAssembly/wabt/releases) (busca el archivo que termina en `windows.zip`).
2.  Descomprime la carpeta en una ubicación segura (ejemplo: `C:\wabt`).
3.  **Agregar al PATH de Windows:**
    * Presiona la tecla `Windows` y busca **"Editar las variables de entorno del sistema"**.
    * Haz clic en el botón **"Variables de entorno"**.
    * En la sección "Variables del sistema" (abajo), busca la variable **"Path"** y haz clic en **"Editar"**.
    * Haz clic en **"Nuevo"** y pega la ruta a la carpeta `bin` que descomprimiste (ejemplo: `C:\wabt\bin`).
    * Acepta todas las ventanas para guardar cambios.
4.  Reinicia tu terminal y verifica la instalación escribiendo: `wat2wasm --version`.

### Paso 2: Instalación de Dependencias de Python

El proyecto requiere la librería `sly` para el análisis léxico y sintáctico. Elige una de las siguientes opciones:

#### 🟢 Opción A: Con `requirements.txt`
Si dispones del archivo de requerimientos, ejecuta:
cmd
pip install -r requirements.txt

#### Opcion B:
### 🚀 EJECUCIÓN

El archivo main.py automatiza todo el proceso de compilación y ejecución.

## Navegar al directorio del proyecto:

    cd C:\ruta\al\proyecto\TPEspecial-Compiladores

## Ejecutar el compilador: Debes indicar la ruta del archivo de prueba que deseas compilar.
DOS

    python main.py pruebas/parser_pruebas/nombre_del_test.txt

## ¿Qué sucede al ejecutar?

Si la configuración es correcta, el script realizará lo siguiente automáticamente:

    Genera el código intermedio en output.wat.

    Llama a wat2wasm para crear el binario output.wasm.

    Llama a Node.js para ejecutar el programa y mostrar el resultado en la consola.

### 📂 ARCHIVOS DE SALIDA

Durante la ejecución se generarán los siguientes archivos en la raíz del proyecto para facilitar la depuración:

    output.wat: Código fuente generado en formato de texto WebAssembly (legible por humanos).

    output.wasm: Archivo binario ejecutable final.

    salida_numerada.txt: Copia del código fuente original con números de línea, útil para rastrear errores.

    resultado_analisis_sintactico.txt: Log detallado de la salida del análisis sintáctico.

### ⚠️ SOLUCIÓN DE PROBLEMAS FRECUENTES

    Error: FileNotFoundError o "'wat2wasm' no se reconoce...":

        Esto indica que Windows no encuentra la herramienta WABT. Revisa el Paso 1 y asegúrate de que la ruta a la carpeta bin está en el PATH. Asegúrate de reiniciar la terminal después de cambiar el PATH.

    Caracteres extraños en la consola:

        El compilador usa emojis y codificación UTF-8. Si en el cmd de Windows ves símbolos raros, prueba ejecutar el proyecto desde PowerShell o Windows Terminal.