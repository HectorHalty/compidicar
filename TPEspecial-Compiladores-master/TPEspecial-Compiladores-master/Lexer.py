from sly import Lexer
from TablaDeSimbolos import TablaDeSimbolos

class AnalisisLexico(Lexer):
    #Definición de tokens
    tokens = {ID, MINUS, ASSIGN, ASSIGN_PASCAL, EQ, NEQ, ARROW, LTE, GTE, GT, LT, UINT, DO, WHILE, IF, ELSE, ENDIF, PRINT, RETURN, CADENA, UINT_CONST, DFLOAT_CONST, CV, TRUNC}
    ignore = ' \t'
    literals = {'+', '*', '/', '(', ')', '{' , '}', '_', ',', ';', '.'}

    def __init__(self):
        self.errores = []
        self.tabla_simbolos = TablaDeSimbolos()

    #expresiones regulares para tokens
    ignore_comentario = r'##(.|\n)*?##'     #La parte `(.|\n)*?` busca cualquier caracter
    ignore_newline = r'\n+'
    UINT_CONST = r'\d+UI'
    #error_dfloat = r'(\d+\.\d*|\.\d+)D(\d+|[+\-]\b)|\d+D[+\-]\d+'
    DFLOAT_CONST = r'(\d+\.\d*|\.\d+)(D[+\-]\d+)?'  #negativos se ve en el parser
    CADENA = r'"[^"\n]*"'
    error_numero = r'\d+(\.\d*)?(D[+\-]\d+)?'
    error_cadena = r'"([^"\n]|\\")*'
    error_comentario = r'##(.|\n)*'

    #Identificadores y palabras reservadas
    ID = r'[A-Z][A-Z0-9%]*'
    #DFLOAT = r'dfloat'
    UINT = r'uint'
    DO = r'do'
    WHILE = r'while'
    IF = r'if'
    ELSE = r'else'
    ENDIF = r'endif'
    PRINT = r'print'
    RETURN = r'return'
    CV = r'cv'
    ASSIGN_PASCAL= r':='
    TRUNC = r'trunc'
    EQ = '=='
    NEQ = '=!'
    ASSIGN = r'='
    ARROW = r'->'
    LTE = r'<='
    GTE = r'>='
    GT = r'>'
    LT = r'<'
    MINUS = r'-'
    
    #Manejo de errores en constantes de punto flotante
    def error_dfloat(self, t):
        print(f"Línea {self.lineno}: Error: Formato inválido para número de punto flotante '{t.value}'")
        self.index += len(t.value)
    

    #Inciso 33: Ignoramos comentarios entre ## ... ##
    def ignore_comentario(self, t):
        self.lineno += t.value.count('\n')

    #Contamos saltos de línea para reportar errores correctamente
    def ignore_newline(self, t):
        self.lineno += len(t.value)
    
    #Inciso 2: Constantes enteras sin signo de 16 bits (uint)
    def UINT_CONST(self, t):
        # Quitamos el sufijo 'UI' para convertir a número
        val = int(t.value[:-2])
        # Verificamos rango
        if not (0 <= val <= 65535):
            print(f"Línea {self.lineno}: Warning: Constante '{t.value}' fuera de rango (0-65535).")
            # Truncamos el valor al rango permitido
            val = max(0, min(val, 65535))
            print(f"Línea {self.lineno}: Warning: Constante '{t.value}' truncada a '{val}UI'.")
        t.value = val
        self.tabla_simbolos.agregar(str(t.value), 'UINT_CONST', valor=val, linea=self.lineno)
        return t
    
    #Inciso 6: Puntos Flotantes con notación científica
    POS_MIN = 2.2250738585072014e-308
    POS_MAX = 1.7976931348623157e+308

    def DFLOAT_CONST(self, t):
        lexema_original = t.value
        #Verificamos que el valor este dentro del rango permitido, y reemplazamos la 'e' de la notacion cientifica con 'D'.
        valor_numerico = float(t.value.replace('D', 'e'))
        #Verificamos el intervalo y el 0
        es_cero = (valor_numerico == 0.0)
        en_rango_positivo = (self.POS_MIN < valor_numerico < self.POS_MAX)
        if not (es_cero or en_rango_positivo ):
            print(f"Línea {self.lineno}: Error: Constante de punto flotante '{t.value}' fuera de rango.")
            return 

        self.tabla_simbolos.agregar(lexema_original, 'DFLOAT_CONST', valor=t.value, linea=self.lineno)

        return t

    
    def ID(self, t):
        if len(t.value) > 20:
            print(f"Línea {self.lineno}: Warning: Identificador '{t.value}' truncado a 20 caracteres.")
            t.value = t.value[:20]
        #Agregamos a la tabla de símbolos si este no ha sido agregado antes.
        if t.type == 'ID':
            if t.value not in self.tabla_simbolos.simbolos:
                self.tabla_simbolos.agregar(t.value, 'Identificador', linea=self.lineno)
        #El token se retorna, sin importar qué tipo sea.
        return t

    #Inciso 7: Cadena de una linea entre comillas dobles
    def CADENA(self, t):
        lexema_original = t.value
        t.value = t.value[1:-1] # Quitamos las comillas
        # Agregamos la cadena a la tabla
        ##self.tabla_simbolos.agregar(lexema_original, 'CADENA', valor=t.value, linea=self.lineno)
        return t
 
    #Manejo de errores en numeros
    def error_numero(self, t):
        self.errores.append(f"(Línea {t.lineno}): Formato inválido para número '{t.value}'")
             
    #Manejo de errores en cadenas entre comillas
    def error_cadena(self, t):
        self.errores.append(f"(Línea {t.lineno}): Cadena no terminada '{t.value}'")

    #Manejo de errores en comentarios
    def error_comentario(self, t):
        self.errores.append(f"(Línea {t.lineno}): Comentario no terminado '{t.value}'")
        self.lineno += t.value.count('\n')
        self.index += len(t.value)
    
    #Manejo de errores
    def error(self, t):
        # Requisito: Reportar línea y descripción del error [cite: 44]
        self.errores.append(f"(Línea {t.lineno}): Carácter ilegal '{t.value[0]}'")
        self.index += 1