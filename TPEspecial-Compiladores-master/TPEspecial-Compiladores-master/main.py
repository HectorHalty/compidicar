from Lexer import AnalisisLexico
from Parser import AnalisisSintactico
from AnalisisSemantico import Nodo
import sys
import io, os

def analizar_archivo(nombre_archivo):
    errores_compilacion = []
    tokens = []
    resultado = None # AST
    arbol_semantico = None
    
    # Lectura del archivo
    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as f:
            codigo_fuente = f.read()
    except FileNotFoundError:
        print(f"Error: El archivo '{nombre_archivo}' no fue encontrado.")
        sys.exit(1)


    #PARTE 1. ANALISIS LEXICO 

    lexer = AnalisisLexico()
    try:
        #Intentamos obtener tokens incluso si hay errores lexicos
        tokens = list(lexer.tokenize(codigo_fuente))
    except Exception as e:
        errores_compilacion.append(f"Error Lexico Fatal: {e}")

    #Recolectamos errores reportados por el lexer
    if hasattr(lexer, 'errores') and lexer.errores:
        for err in lexer.errores:
            errores_compilacion.append(f"Error Lexico: {err}")


    #PARTE 2. ANALISIS SINTACTICO 
    # Solo intentamos parsear si obtuvimos tokens (aunque haya habido errores lexicos)
    if tokens:
        parser = AnalisisSintactico()
        parser.set_tabla_simbolos(lexer.tabla_simbolos)

        # Capturamos stdout para silenciar mensajes internos del parser
        captured_output = io.StringIO()
        sys_stdout_original = sys.stdout
        sys.stdout = captured_output

        try:
            resultado = parser.parse(iter(tokens))
        except Exception as e:
            errores_compilacion.append(f"Error Sintactico Fatal: {e}")

        sys.stdout = sys_stdout_original # Restauramos stdout

        # Recolectar errores sintacticos
        if hasattr(parser, "errores") and parser.errores():
            for mensaje, linea in parser.errores():
                errores_compilacion.append(f"Error Sintactico (Linea {linea}): {mensaje}")
        
        if not isinstance(resultado, Nodo) and not errores_compilacion:
             # Si no hay arbol y no detectamos errores explicitos, marcamos error generico
             errores_compilacion.append("Error Sintactico: No se pudo generar el Arbol Sintactico (AST).")


    #PARTE 3. ANALISIS SEMANTICO 
    # Intentamos el analisis semantico SOLO si existe un arbol sintactico (resultado).
    if resultado is not None:
        try:
            from AnalisisSemantico import AnalisisSemantico
            sem = AnalisisSemantico(lexer.tabla_simbolos)
            arbol_semantico = sem.analizar_entrada(resultado)

            #Recolectamos errores semanticos y mostramos warnings
            if arbol_semantico and arbol_semantico.diag:
                print("\n=== DIAGNOSTICOS SEMANTICOS ===")
                for d in arbol_semantico.diag:
                    severidad = getattr(d, 'severidad', 'ERROR')
                    linea = getattr(d, 'linea', '?')
                    mensaje = str(d) # Usamos str(d) para obtener el mensaje completo

                    if severidad == 'WARNING':
                        # Solo imprimimos, NO agregamos a la lista de errores fatales
                        print(f" Warning (Linea {linea}): {mensaje}")
                    else:
                        # Es ERROR (o desconocido), lo agregamos para detener compilacion
                        errores_compilacion.append(f"Error Semantico (Linea {linea}): {mensaje}")

        except ImportError as e:
            print(f"Error de configuracion: No se pudo importar AnalisisSemantico: {e}")
            return
        except Exception as e:
            errores_compilacion.append(f"Error Semantico Fatal: {e}")


    # Si se acumulo CUALQUIER error, los mostramos y paramos AQUI.
    # Asi evitamos generar codigo basura.
    if errores_compilacion:
        mostrar_errores(errores_compilacion)


    # MOSTRAMOS RESULTADOS INTERMEDIOS (AST Y TABLA)
    # Lo hacemos ANTES de verificar si hay errores para poder ver el arbol recuperado
    
    print(f"\n=== 2) REPRESENTACION INTERMEDIA (AST) ===")
    if arbol_semantico:
        print(arbol_semantico.imprimir_arbol())
    elif resultado:
        # Si fallo el semantico pero hay arbol sintactico crudo
        print("(Arbol Sintactico sin procesar por Semantico)")
        print(resultado)
    else:
        print("(No se pudo generar el AST)")

    print("\n=== 3) TABLA DE SIMBOLOS ===")
    print(lexer.tabla_simbolos)

    


    #GENERACION DE CODIGO (Solo si no hay errores)


    print(f"✅ Compilacion exitosa del archivo: {nombre_archivo}\n")

    if errores_compilacion:
        print("❌ No se genero codigo debido a errores de compilacion.")
        return

    # 4) Archivo conteniendo el codigo Assembler
    print("\n=== 4) CODIGO ASSEMBLER (WASM) ===")
    try:
        from generador_wasm import GeneradorWasm
        
        # Limpieza previa
        if os.path.exists("output.wat"): os.remove("output.wat")
        if os.path.exists("output.wasm"): os.remove("output.wasm")
        
        generador = GeneradorWasm()
        codigo_wat = generador.generar(arbol_semantico)
        
        output_filename = "output.wat"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(codigo_wat)
            
        print(f"✅ Archivo generado: '{output_filename}'")
        print("Contenido del archivo generado (primeras 20 lineas):")
        print("-" * 40)
        print("\n".join(codigo_wat.split('\n')[:20]))
        if len(codigo_wat.split('\n')) > 20:
            print("... (resto del archivo omitido) ...")
        print("-" * 40)
        
        print("\nInstrucciones para ejecutar:")
        print(f"  1. wat2wasm {output_filename} -o output.wasm")
        print(f"  2. node run_wasm.js output.wasm")

    except Exception as e:
        print(f"❌ Error durante la generación de codigo: {e}")


def mostrar_errores(lista_errores):
    print("\n=== 1) ERRORES DE COMPILACION ===")
    for err in lista_errores:
        print(f"❌ {err}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python main.py <archivo_fuente.txt>")
        sys.exit(1)

    analizar_archivo(sys.argv[1])


if __name__ == "__main__":
    main()