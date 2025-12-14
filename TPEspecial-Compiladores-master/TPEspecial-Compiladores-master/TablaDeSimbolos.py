#Definición de la tabla de símbolos
class TablaDeSimbolos:
    def __init__(self):
        self.simbolos = {}  # Diccionario para almacenar los símbolos

    def _to_tipo_str(self, tipo):
        #Acepta enums (p.ej. Tipo.UINT) o strings y devuelve un string de tipo.
        try:
            return tipo.name  # Enum
        except Exception:
            return str(tipo)
        
    def agregar(self, lexema, tipo, valor=None, linea=None):    #Por si se desconoce el valor o linea
        if lexema not in self.simbolos:
            # Si el símbolo es nuevo, lo creamos
            entrada = {
                'lexema': lexema,
                'tipo': tipo,
                'valor': valor,
                'linea': linea,
                'uso': 'N/A'
            }
            self.simbolos[lexema] = entrada
        else:
            print(f"Warning: El símbolo '{lexema}' ya existe en la tabla de símbolos.")
        # Devolvemos la entrada
        return self.simbolos[lexema]
    

    def asignar_tipo(self, lexema, tipo):
        #Método para asignar o actualizar el tipo de un símbolo existente en la tabla.
        tipo_str = self._to_tipo_str(tipo)
        if lexema not in self.simbolos:
            # Si no existe, lo crea (útil si el lexer no lo vio)
            self.agregar(lexema, tipo_str)
            return
        # Si existe, actualiza el tipo
        self.simbolos[lexema]['tipo'] = tipo_str


    def renombrar(self, clave_vieja, clave_nueva):
        #Cambia la clave de una entrada y actualiza 'lexema' sin perder la info.Retorna True si se renombró, False si no existía o la nueva ya existe.
        if clave_vieja in self.simbolos and clave_nueva not in self.simbolos:
            entrada = self.simbolos.pop(clave_vieja)
            entrada['lexema'] = clave_nueva
            self.simbolos[clave_nueva] = entrada
            return True
        return False
    
    
    def asignar_uso(self, lexema, uso_str):
        #Asigna o añade un uso a un símbolo existente.
        if lexema in self.simbolos:
            entrada = self.simbolos[lexema]
            # CORRECCIÓN: Usar .get() para leer de forma segura
            current_uso = entrada.get('uso', 'N/A')
            if current_uso == 'N/A' or not current_uso:
                entrada['uso'] = uso_str
            else:
                # Evita añadir el mismo uso dos veces seguidas
                if uso_str not in current_uso.split('-'):
                    entrada['uso'] += f"-{uso_str}"


    def agregar_negativo(self, lexema_original, linea=None):
        """
        Método para agregar un número negativo a la tabla de símbolos.
        Crea una nueva entrada independiente sin modificar la entrada original.
        """
        # Extraer el valor real del lexema
        if isinstance(lexema_original, list) and len(lexema_original) == 1:
            valor_original = lexema_original[0]
        else:
            valor_original = str(lexema_original)
        
        # Crear el lexema para el número negativo
        lexema_negativo = f"-{valor_original}"
        
        # Crear una nueva entrada para el número negativo
        if lexema_negativo not in self.simbolos:
            entrada = {
                'lexema': lexema_negativo,
                'tipo': 'DFLOAT_CONST',
                'valor': f"-{valor_original}",
                'linea': linea,
                'uso': 'constante'
            }
            self.simbolos[lexema_negativo] = entrada
        else:
            print(f"Warning: El símbolo '{lexema_negativo}' ya existe en la tabla de símbolos.")
        
        return self.simbolos[lexema_negativo]

    def __str__(self):
        s = "   TABLA DE SÍMBOLOS   \n"
        s += "{:<25} {:<15} {:<25} {:<35} {:<10}\n".format("Lexema", "Tipo", "Valor", "Uso", "Línea")
        s += "-" * 115 + "\n"
        for lexema, entrada in self.simbolos.items():
            valor_str = str(entrada['valor']) if entrada['valor'] is not None else "N/A"
            linea_str = str(entrada['linea']) if entrada['linea'] is not None else "N/A"
            uso_str = str(entrada.get('uso', 'N/A')) # Usar .get() para seguridad
            s += "{:<25} {:<15} {:<25} {:<35} {:<10}\n".format(
                entrada['lexema'],
                entrada['tipo'],
                valor_str,
                uso_str,
                linea_str
            )
        s += "\n"
        return s
