from sly import Parser
from Lexer import AnalisisLexico
from TablaDeSimbolos import TablaDeSimbolos
from typing import List, Tuple

# Importamos los nodos del AST el enum de tipos
from AnalisisSemantico import (
    Programa, Bloque, DeclVar, Identificador, IdCalificado, Literal,
    Unario, Binario, Asignacion, MultiAsignacion, Si, DoWhile, Print,
    Return, Parametro, Invocacion, Funcion, Trunc, Tipo, ErrorNodo, Lambda
)



class AnalisisSintactico(Parser):
    # Tabla de simbolos 
    def __init__(self):
        self._errores: List[Tuple[str, int]] = [] #para cortar el main si hay errores sintacticos
        self.tabla_simbolos = None
        self.error_flag = False

    # metodo para establecer la tabla de simbolos.
    def set_tabla_simbolos(self, tabla):
        self.tabla_simbolos = tabla

    #Se llama desde las reglas, asi se reportan errores propios
    def registrar_error(self, mensaje: str, tok=None):
        linea = getattr(tok, "lineno", 0) if tok is not None else 0
        self._errores.append((mensaje, linea))

    def tiene_errores(self) -> bool:
        return len(self._errores) > 0

    def errores(self) -> List[Tuple[str, int]]:
        return list(self._errores)
    
    debugfile = 'parser.out'

    #Tokens del lexico.
    tokens = AnalisisLexico.tokens
    
    # Especificar la regla de inicio
    start = 'programa'

    # Ajuste de precedencia para resolver conflictos
    precedence = (
       ('nonassoc', 'EQ', 'NEQ', 'LT', 'LTE', 'GT', 'GTE'),     # Operadores de comparacion
       ('left','+', MINUS),                                     # Operadores aditivos
       ('left', '*', '/'),                                      # Operadores multiplicativos
       ('right', 'UMINUS'),                                     # Operador unario con mayor precedencia
    )

    #REGLAS GRAMATICALES Y ACCIONES SEMANTICAS

    #helper para el semantico, que reciba los lexemas y los convierta a float
    def _to_float(self, lex):
        if isinstance(lex, (int, float)):
            return float(lex)
        if isinstance(lex, str):
            try:
                return float(lex.replace('D', 'e').replace('d', 'e'))
            except:
                return float(lex)  # reintento simple
        return float(0.0)



    #Regla inicio de programa
    @_('ID "{" sentencias "}"')
    def programa(self, p):
        print(f"Línea {p.lineno}: Se reconoció el programa con sentencias.")
        return Programa(nombre=p.ID, cuerpo=Bloque(sentencias=p.sentencias))
    
    #Regla para sentencias (puede ser vacía o multiples sentencias)
    @_('sentencias sentencia')
    def sentencias(self, p):
        return p.sentencias + ([p.sentencia] if p.sentencia is not None else [])

    
    #Regla para una sentencia individual (declaracion de variable)
    @_('UINT lista_ids ";"')
    def sentencia(self, p):
        print(f"Linea {p.lineno}: Se reconocio declaracion de variable(s) de tipo UINT.")
        return DeclVar(tipo_decl=Tipo.UINT, ids=p.lista_ids, linea=p.lineno)
    
    #Reglas para un identificador de variable.
    @_('ID')
    def lista_ids(self,p):
        return [Identificador(nombre=p.ID, linea=p.lineno)]
  
    @_('ID "," lista_ids')
    def lista_ids(self, p):
        return [Identificador(nombre=p.ID, linea=p.lineno)] + p.lista_ids
    @_('id_calificado "," lista_ids')
    def lista_ids(self, p):
        return [p.id_calificado] + p.lista_ids
    
    @_('id_calificado')
    def lista_ids(self,p):
        return [p.id_calificado]
    
    @_('ID "." ID')
    def id_calificado(self, p):
        # Devuelve una tupla, que es ordenada e inmutable
        print(f"Línea {p.lineno}: Se reconoció ID calificado '{p.ID0}.{p.ID1}'.")
        return IdCalificado(base=Identificador(nombre=p.ID0), atributo=Identificador(nombre=p.ID1), linea=p.lineno)

    
    
    @_('')
    def sentencias(self, p):
        return []
    
    
    
    # Reglas para todas las sentencias if
    @_('IF "(" condicion ")" bloque_sentencias ELSE bloque_sentencias ENDIF ";"')
    def sentencia(self, p):
        print(f"Línea {p.lineno}: Se reconoció IF con rama ELSE.")
        return Si(condicion=p.condicion, entonces=p.bloque_sentencias0, sino=p.bloque_sentencias1)

    @_('IF "(" condicion ")" bloque_sentencias ENDIF ";"')
    def sentencia(self, p):
        print(f"Línea {p.lineno}: Se reconoció IF sin ELSE.")
        return Si(condicion=p.condicion, entonces=p.bloque_sentencias, sino=None)
    
    @_(' "{" sentencias "}" ')
    def bloque_sentencias(self, p):
        return p.sentencias
    
    @_('sentencia')
    def bloque_sentencias(self, p):
        return [p.sentencia]
    # Fin de reglas IF

    '''
    # Regla para sentencias IF dentro de una funcion, entonces puede tener RETURN.
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ELSE bloque_sentencias_de_funcion ENDIF ";"')
    def sentencia_de_funcion(self, p):
        print(f"Línea {p.lineno}: Se reconoció IF con rama ELSE dentro de función.")
        return ('if', p.condicion, p.bloque_sentencias_de_funcion0, p.bloque_sentencias_de_funcion1)
    
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ENDIF ";"')
    def sentencia_de_funcion(self, p):
        print(f"Línea {p.lineno}: Se reconoció IF sin ELSE dentro de función.")
        return ('if', p.condicion, p.bloque_sentencias_de_funcion)
    '''
    @_(' "{" sentencias_de_funcion "}" ')
    def bloque_sentencias_de_funcion(self, p):
        return p.sentencias_de_funcion
    
    @_('sentencia_de_funcion')
    def bloque_sentencias_de_funcion(self, p):
        return [p.sentencia_de_funcion]
    # Fin de reglas IF dentro de función.
    

    
    
    #Reglas para condiciones
    @_('expresion EQ expresion')
    def condicion(self, p):
        print(f"Línea {p.lineno}: Se reconoció condición de igualdad '{p.expresion0} == {p.expresion1}'.")
        return Binario(op='==', izq=p.expresion0, der=p.expresion1)
    
    
    @_('expresion NEQ expresion')
    def condicion(self, p):
        print(f"Línea {p.lineno}: Se reconoció condición de desigualdad '{p.expresion0} != {p.expresion1}'.")
        return Binario(op='!=', izq=p.expresion0, der=p.expresion1)
    
    @_('expresion LT expresion')
    def condicion(self, p):
        print(f"Línea {p.lineno}: Se reconoció condición menor que '{p.expresion0} < {p.expresion1}'.")
        return Binario(op='<', izq=p.expresion0, der=p.expresion1)
    
    @_('expresion LTE expresion')
    def condicion(self, p):
        print(f"Línea {p.lineno}: Se reconoció condición menor o igual que '{p.expresion0} <= {p.expresion1}'.")
        return Binario(op='<=', izq=p.expresion0, der=p.expresion1)
    
    @_('expresion GT expresion')
    def condicion(self, p):
        print(f"Línea {p.lineno}: Se reconoció condición mayor que '{p.expresion0} > {p.expresion1}'.")
        return Binario(op='>', izq=p.expresion0, der=p.expresion1)
    
    @_('expresion GTE expresion')
    def condicion(self, p):
        print(f"Línea {p.lineno}: Se reconoció condición mayor o igual que '{p.expresion0} >= {p.expresion1}'.")
        return Binario(op='>=', izq=p.expresion0, der=p.expresion1)
    #Fin de reglas condiciones
    


    #Conjunto de reglas para declaración de funciones
    @_('UINT ID "(" parametros ")" "{" sentencias_de_funcion final_funcion "}" ')
    def sentencia(self, p):
        tail = p.final_funcion if isinstance(p.final_funcion, list) else ([p.final_funcion] if p.final_funcion else [])
        cuerpo = Bloque(sentencias=p.sentencias_de_funcion + tail)
        return Funcion(nombre=p.ID, params=p.parametros, cuerpo=cuerpo, retorno=Tipo.UINT, linea=p.lineno)
        
    #Esto se hace debido a que si se usa 'sentencias' no se podria saber reconocer la palabra reservada RETURN
    @_('sentencias_de_funcion sentencia_de_funcion')
    def sentencias_de_funcion(self, p):
        return p.sentencias_de_funcion + [p.sentencia_de_funcion]

    @_('')
    def sentencias_de_funcion(self, p):
        return []

    # Sentencias permitidas dentro de una función
    @_('UINT lista_ids ";"')
    def sentencia_de_funcion(self, p):
        print(f"Línea {p.lineno}: Se reconoció declaración de variable local '{p.lista_ids}'.")
        return DeclVar(tipo_decl=Tipo.UINT, ids=p.lista_ids, linea=p.lineno)
    
    @_('UINT ID "(" parametros ")" "{" sentencias_de_funcion final_funcion "}" ')
    def sentencia_de_funcion(self, p):
        print(f"Línea {p.lineno}: Se reconoció declaración de funcion dentro de funcion '{p.ID}'.")
        tail = p.final_funcion if isinstance(p.final_funcion, list) else ([p.final_funcion] if p.final_funcion else [])
        cuerpo = Bloque(sentencias=p.sentencias_de_funcion + tail)
        return Funcion(nombre=p.ID, params=p.parametros, cuerpo=cuerpo, retorno=Tipo.UINT)




    #SENTENCIAS IF DENTRO DE FUNCION



    #Reglas para IF comunes dentro de una funcion
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        print(f"Línea {p.lineno}: Se reconoció IF con rama ELSE dentro de función.")
        tail = p.final_funcion if isinstance(p.final_funcion, list) else ([p.final_funcion] if p.final_funcion is not None else [])
        then_blk = Bloque(sentencias=p.bloque_sentencias_de_funcion0)
        else_blk = Bloque(sentencias=p.bloque_sentencias_de_funcion1)
        return [Si(condicion=p.condicion, entonces=then_blk, sino=else_blk)] + p.sentencias_de_funcion + tail
    
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        print(f"❌ Error sintactico en línea {p.lineno}: Se reconocio if comun con else dentro de funcion sin return en ninguna rama ni posteriormente.")
        then_blk = Bloque(sentencias=p.bloque_sentencias_de_funcion0)
        else_blk = Bloque(sentencias=p.bloque_sentencias_de_funcion1)
        return [Si(condicion=p.condicion, entonces=then_blk, sino=else_blk)] + p.sentencias_de_funcion
    
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        print(f"Línea {p.lineno}: Se reconoció IF sin ELSE dentro de función.")
        tail = p.final_funcion if isinstance(p.final_funcion, list) else ([p.final_funcion] if p.final_funcion is not None else [])
        then_blk = Bloque(sentencias=p.bloque_sentencias_de_funcion)
        return [Si(condicion=p.condicion, entonces=then_blk, sino=None)] + p.sentencias_de_funcion + tail
        
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        print(f"❌ Error sintactico en línea {p.lineno}: Se reconocio if comun dentro de funcion sin return en ninguna rama ni posteriormente.")
        then_blk = Bloque(sentencias=p.bloque_sentencias_de_funcion)
        return [Si(condicion=p.condicion, entonces=then_blk, sino=None)] + p.sentencias_de_funcion
    #FIN REGLAS DE IF COMUNES



    #Reglas para sentencias IF final dentro de una funcion.

    # IF () {..., RETURN ...} ELSE {..., RETURN ...} ENDIF;
    @_('IF "(" condicion ")" "{" sentencias_de_funcion final_funcion "}" ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF ";"')
    def final_funcion(self, p):
        print(f"Línea {p.lineno}: Se reconoció final de función con 'if' y 'else' para '{p.condicion}'.")
        then_tail = p.final_funcion0 if isinstance(p.final_funcion0, list) else ([p.final_funcion0] if p.final_funcion0 is not None else [])
        else_tail = p.final_funcion1 if isinstance(p.final_funcion1, list) else ([p.final_funcion1] if p.final_funcion1 is not None else [])
        then_blk = Bloque(sentencias=p.sentencias_de_funcion0 + then_tail)
        else_blk = Bloque(sentencias=p.sentencias_de_funcion1 + else_tail)
        return [Si(condicion=p.condicion, entonces=then_blk, sino=else_blk)]
    
    #IF () RETURN ; ELSE RETURN ; ENDIF;
    @_('IF "(" condicion ")" final_funcion ELSE final_funcion ENDIF ";"')
    def final_funcion(self, p):
        print(f"Línea {p.lineno}: Se reconoció final de función con 'if' y 'else' para '{p.condicion}'.")
        then_tail = p.final_funcion0 if isinstance(p.final_funcion0, list) else ([p.final_funcion0] if p.final_funcion0 is not None else [])
        else_tail = p.final_funcion1 if isinstance(p.final_funcion1, list) else ([p.final_funcion1] if p.final_funcion1 is not None else [])
        then_blk = Bloque(sentencias=then_tail)
        else_blk = Bloque(sentencias=else_tail)
        return [Si(condicion=p.condicion, entonces=then_blk, sino=else_blk)]
    
    #IF () {..., RETURN} ELSE RETURN; ENDIF;
    @_('IF "(" condicion ")" "{" sentencias_de_funcion final_funcion "}" ELSE final_funcion ENDIF ";"')
    def final_funcion(self, p):
        print(f"Línea {p.lineno}: Se reconoció final de función con 'if' y 'else' para '{p.condicion}'.")
        then_tail = p.final_funcion0 if isinstance(p.final_funcion0, list) else ([p.final_funcion0] if p.final_funcion0 is not None else [])
        else_tail = p.final_funcion1 if isinstance(p.final_funcion1, list) else ([p.final_funcion1] if p.final_funcion1 is not None else [])
        then_blk = Bloque(sentencias=p.sentencias_de_funcion + then_tail)
        else_blk = Bloque(sentencias=else_tail)
        return [Si(condicion=p.condicion, entonces=then_blk, sino=else_blk)]
    
    #IF () RETURN; ELSE {..., RETURN}; ENDIF;
    @_('IF "(" condicion ")" final_funcion ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF ";"')
    def final_funcion(self, p):
        print(f"Línea {p.lineno}: Se reconoció final de función con 'if' y 'else' para '{p.condicion}'.")
        then_tail = p.final_funcion0 if isinstance(p.final_funcion0, list) else ([p.final_funcion0] if p.final_funcion0 is not None else [])
        else_tail = p.final_funcion1 if isinstance(p.final_funcion1, list) else ([p.final_funcion1] if p.final_funcion1 is not None else [])
        then_blk = Bloque(sentencias=then_tail)
        else_blk = Bloque(sentencias=p.sentencias_de_funcion + else_tail)
        return [Si(condicion=p.condicion, entonces=then_blk, sino=else_blk)]
    #FIN DE REGLAS PARA SENTENCIAS IF FINALES DENTRO DE FUNCION    



    #ESTE BLOQUE ES PARA LOS FINALES DONDE FALTA ELSE

    #IF () {...RETURN...} ENDIF RETURN;
    @_('IF "(" condicion ")" "{" sentencias_de_funcion final_funcion "}" ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        print(f"Línea {p.lineno}: Se reconoció final de función con 'if' sin else para  '{p.condicion}'.")
        then_tail = p.final_funcion0 if isinstance(p.final_funcion0, list) else ([p.final_funcion0] if p.final_funcion0 is not None else [])
        after_tail = p.final_funcion1 if isinstance(p.final_funcion1, list) else ([p.final_funcion1] if p.final_funcion1 is not None else [])
        then_blk = Bloque(sentencias=p.sentencias_de_funcion0 + then_tail)
        return [Si(condicion=p.condicion, entonces=then_blk, sino=None)] + p.sentencias_de_funcion1 + after_tail
    
    #IF () RETURN; ENDIF RETURN;
    @_('IF "(" condicion ")" final_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        print(f"Línea {p.lineno}: Se reconoció final de función con 'if' sin else para  '{p.condicion}'.")
        then_tail = p.final_funcion0 if isinstance(p.final_funcion0, list) else ([p.final_funcion0] if p.final_funcion0 is not None else [])
        after_tail = p.final_funcion1 if isinstance(p.final_funcion1, list) else ([p.final_funcion1] if p.final_funcion1 is not None else [])
        then_blk = Bloque(sentencias=then_tail)
        return [Si(condicion=p.condicion, entonces=then_blk, sino=None)] + p.sentencias_de_funcion + after_tail
    
    #IF () RETURN; ENDIF sentencias;
    @_('IF "(" condicion ")" final_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        print(f"❌ Error sintactico en línea {p.lineno}: Se reconocio posible falta de return si no se entra a la rama then.")
        then_tail = p.final_funcion if isinstance(p.final_funcion, list) else ([p.final_funcion] if p.final_funcion is not None else [])
        then_blk = Bloque(sentencias=then_tail)
        return [Si(condicion=p.condicion, entonces=then_blk, sino=None)] + p.sentencias_de_funcion
    
    #IF () {...RETURN...}; ENDIF sentencias;
    @_('IF "(" condicion ")" "{" sentencias_de_funcion final_funcion "}" ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        print(f"❌ Error sintactico en línea {p.lineno}: Se reconocio posible falta de return si no se entra a la rama then.")
        then_tail = p.final_funcion if isinstance(p.final_funcion, list) else ([p.final_funcion] if p.final_funcion is not None else [])
        then_blk = Bloque(sentencias=p.sentencias_de_funcion0 + then_tail)
        return [Si(condicion=p.condicion, entonces=then_blk, sino=None)] + p.sentencias_de_funcion1
    
    #FIN DE BLOQUE ES PARA LOS FINALES DONDE FALTA ELSE
    

    #ESTE BLOQUE ES PARA LOS FINALES DONDE ESTA ELSE PERO SIN RETURN
    @_('IF "(" condicion ")" final_funcion ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        print(f"❌ Error sintactico en línea {p.lineno}: Se reconocio return en rama then unicamente.")
        then_tail = p.final_funcion if isinstance(p.final_funcion, list) else ([p.final_funcion] if p.final_funcion is not None else [])
        then_blk = Bloque(sentencias=then_tail)
        else_blk = Bloque(sentencias=p.bloque_sentencias_de_funcion)
        return [Si(condicion=p.condicion, entonces=then_blk, sino=else_blk)] + p.sentencias_de_funcion
    
    @_('IF "(" condicion ")" final_funcion ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        print(f"Línea {p.lineno}: Se reconoció final de función en rama then, no en rama else. Pero si luego de todo el if '{p.condicion}'.")
        then_tail = p.final_funcion0 if isinstance(p.final_funcion0, list) else ([p.final_funcion0] if p.final_funcion0 is not None else [])
        after_tail = p.final_funcion1 if isinstance(p.final_funcion1, list) else ([p.final_funcion1] if p.final_funcion1 is not None else [])
        then_blk = Bloque(sentencias=then_tail)
        else_blk = Bloque(sentencias=p.bloque_sentencias_de_funcion)
        return [Si(condicion=p.condicion, entonces=then_blk, sino=else_blk)] + p.sentencias_de_funcion + after_tail
    
    @_('IF "(" condicion ")" "{" sentencias_de_funcion final_funcion "}" ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        print(f"❌ Error sintactico en línea {p.lineno}: Se reconocio return en rama then unicamente.")
        then_tail = p.final_funcion if isinstance(p.final_funcion, list) else ([p.final_funcion] if p.final_funcion is not None else [])
        then_blk = Bloque(sentencias=p.sentencias_de_funcion0 + then_tail)
        else_blk = Bloque(sentencias=p.bloque_sentencias_de_funcion)
        return [Si(condicion=p.condicion, entonces=then_blk, sino=else_blk)] + p.sentencias_de_funcion1
    
    @_('IF "(" condicion ")" "{" sentencias_de_funcion final_funcion "}" ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        print(f"Línea {p.lineno}: Se reconoció final de función con en rama then, no en rama else. Pero si luego de todo el if '{p.condicion}'.")
        then_tail = p.final_funcion0 if isinstance(p.final_funcion0, list) else ([p.final_funcion0] if p.final_funcion0 is not None else [])
        after_tail = p.final_funcion1 if isinstance(p.final_funcion1, list) else ([p.final_funcion1] if p.final_funcion1 is not None else [])
        then_blk = Bloque(sentencias=p.sentencias_de_funcion0 + then_tail)
        else_blk = Bloque(sentencias=p.bloque_sentencias_de_funcion)
        return [Si(condicion=p.condicion, entonces=then_blk, sino=else_blk)] + p.sentencias_de_funcion1 + after_tail
    #FIN DE BLOQUE ES PARA LOS FINALES DONDE ESTA ELSE PERO SIN RETURN





    #FINALES DONDE RAMA THEN NO TIENE RETURN, Y SI EXISTE RAMA ELSE
    #IF ()  ELSE RETURN; ENDIF;
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ELSE final_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        print(f"❌ Error semántico en línea {p.lineno}: Se reconocio return en rama else unicamente.")
        else_tail = p.final_funcion if isinstance(p.final_funcion, list) else ([p.final_funcion] if p.final_funcion is not None else [])
        then_blk = Bloque(sentencias=p.bloque_sentencias_de_funcion)
        else_blk = Bloque(sentencias=else_tail)
        return [Si(condicion=p.condicion, entonces=then_blk, sino=else_blk)] + p.sentencias_de_funcion
    
    #IF () ELSE {... RETURN ...}; ENDIF;
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        print(f"❌ Error semántico en línea {p.lineno}: Se reconocio return en rama else unicamente.")
        else_tail = p.final_funcion if isinstance(p.final_funcion, list) else ([p.final_funcion] if p.final_funcion is not None else [])
        then_blk = Bloque(sentencias=p.bloque_sentencias_de_funcion)
        else_blk = Bloque(sentencias=p.sentencias_de_funcion0 + else_tail)
        return [Si(condicion=p.condicion, entonces=then_blk, sino=else_blk)] + p.sentencias_de_funcion1
    
     #IF ()  ELSE RETURN; ENDIF; RETURN
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ELSE final_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        print(f"Línea {p.lineno}: Se reconoció final de función en rama else, no en rama then. Pero si luego de todo el if '{p.condicion}'.")
        else_tail = p.final_funcion0 if isinstance(p.final_funcion0, list) else ([p.final_funcion0] if p.final_funcion0 is not None else [])
        after_tail = p.final_funcion1 if isinstance(p.final_funcion1, list) else ([p.final_funcion1] if p.final_funcion1 is not None else [])
        then_blk = Bloque(sentencias=p.bloque_sentencias_de_funcion)
        else_blk = Bloque(sentencias=else_tail)
        return [Si(condicion=p.condicion, entonces=then_blk, sino=else_blk)] + p.sentencias_de_funcion + after_tail
    
    #IF () ELSE {... RETURN ...}; ENDIF; RETURN
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        print(f"Línea {p.lineno}: Se reconoció final de función en rama else, no en rama then. Pero si luego de todo el if '{p.condicion}'.")
        else_tail = p.final_funcion0 if isinstance(p.final_funcion0, list) else ([p.final_funcion0] if p.final_funcion0 is not None else [])
        after_tail = p.final_funcion1 if isinstance(p.final_funcion1, list) else ([p.final_funcion1] if p.final_funcion1 is not None else [])
        then_blk = Bloque(sentencias=p.bloque_sentencias_de_funcion)
        else_blk = Bloque(sentencias=p.sentencias_de_funcion0 + else_tail)
        return [Si(condicion=p.condicion, entonces=then_blk, sino=else_blk)] + p.sentencias_de_funcion1 + after_tail
    #FIN DE REGLAS DE FINALES DONDE RAMA THEN NO TIENE RETURN, Y SI EXISTE RAMA ELSE
    #FINAL SENTENCIAS IF DENTRO DE FUNCION
    
    @_('RETURN "(" expresion ")" ";"')
    def final_funcion(self, p):
        print(f"Línea {p.lineno}: Se reconoció sentencia RETURN con expresión '{p.expresion}'.")
        return Return(expr=p.expresion)





    #FIN DE REGLAS DE final_funcion






    
    @_('ID ASSIGN_PASCAL expresion ";"')
    def sentencia_de_funcion(self, p):
        print(f"Línea {p.lineno}: Se reconoció asignación por pascal '{p.ID} := {p.expresion}'.")
        return Asignacion(destino=Identificador(nombre=p.ID, linea=p.lineno), expr=p.expresion)

    @_('id_calificado ASSIGN_PASCAL expresion ";"')
    def sentencia_de_funcion(self, p):
        print(f"Línea {p.lineno}: Se reconocio asignación por pascal '{p.id_calificado} := {p.expresion}'.")
        return Asignacion(destino=p.id_calificado, expr=p.expresion)

    @_('invocacion ')
    def sentencia_de_funcion(self, p):
        return p.invocacion
    
    @_('print')
    def sentencia_de_funcion(self, p):
        return p.print
    
    @_('DO bloque_sentencias WHILE "(" condicion ")" ";"')
    def sentencia_de_funcion(self, p):
        # Verificamos si la lista de sentencias esta vacia
        if not p.bloque_sentencias:
            print(f"❌ Error Sintactico (Línea {p.lineno}): El cuerpo del DO-WHILE no puede estar vacio (riesgo de bucle infinito).")
            self.registrar_error("Cuerpo de DO-WHILE vacio", p)
            return None 
            
        print(f"Línea {p.lineno}: Se reconoció sentencia DO-WHILE con condición '{p.condicion}'.")
        return DoWhile(cuerpo=Bloque(sentencias=p.bloque_sentencias), condicion=p.condicion)

    @_('lista_ids ASSIGN lista_expr_const ";"')
    def sentencia_de_funcion(self, p):
        if len(p.lista_ids) > len(p.lista_expr_const):
            print(f"❌ Error semantico L{p.lineno}: menos expresiones que variables.")
            return ErrorNodo(mensaje="Mas variables que expresiones en multi asignacion", linea=p.lineno)
        print(f"Línea {p.lineno}: Se reconocio asignación multiple con '='.")
        return MultiAsignacion(destinos=p.lista_ids, expresiones=p.lista_expr_const)
    

    #Fin de sentencias permitidas dentro de una función
    #Fin de reglas declaración de funciones


    
    #----- REGLAS PARA EXPRESIONES ARITMÉTICAS -----#
    # NIVEL 1: Términos (unidades básicas)
    @_('ID')
    def termino(self, p):
        print(f"Línea {p.lineno}: Se reconoció termino '{p.ID}'.")
        return Identificador(nombre=p.ID, linea=p.lineno)
    
    @_('UINT_CONST')
    def termino(self, p):
        print(f"Línea {p.lineno}: Se reconoció termino TERMINO'{p.UINT_CONST}'.")
        return Literal(valor=p.UINT_CONST, tipo=Tipo.UINT, linea=p.lineno)
    
    @_('DFLOAT_CONST')
    def termino(self, p):
        print(f"Línea {p.lineno}: Se reconoció termino TERMINO '{p.DFLOAT_CONST}'.")
        valf = self._to_float(p.DFLOAT_CONST)
        return Literal(valor=valf, tipo=Tipo.DFLOAT, linea=p.lineno)
    
    @_('"(" expresion ")"')
    def termino(self, p):
        print(f"Línea {p.lineno}: Se reconoció expresión entre paréntesis.")
        return p.expresion
    
    @_('id_calificado')
    def termino(self, p):
        return p.id_calificado
    
    @_('invocacion')
    def termino(self, p):
        return p.invocacion
        
    # NIVEL 2: Factor (puede ser un término o un término negativo)
    @_('termino')
    def factor(self, p):
        return p.termino
    @_('MINUS factor %prec UMINUS')
    def factor(self, p):
        valor = p.factor[0]
        if isinstance(valor, int):  # UI
            print(f"Línea {p.lineno}: ❌ Error - Falta operando izquierdo en la operación, no se permite UI negativo.")
            return ('error', 'UI negativo no permitido')
        #elif isinstance(valor, float):  
        #DFLOAT
        print(f"Línea {p.lineno}: Se reconoció expresion negativa '-{p.factor}'.")
        self.tabla_simbolos.agregar_negativo(p.factor, linea=p.lineno)
        return Unario(op='-', expr=p.factor)

    # NIVEL 3: Expresiones de multiplicacion y division
    @_('factor')
    def expr_mult(self, p):
        return p.factor
    
    @_('expr_mult "*" factor')
    def expr_mult(self, p):
        print(f"Línea {p.lineno}: Se reconoció operacion de la multiplicacion '{p.expr_mult} * {p.factor}'.")
        return Binario(op='*', izq=p.expr_mult, der=p.factor)
    
    @_('expr_mult "/" factor')
    def expr_mult(self, p):
        print(f"Línea {p.lineno}: Se reconoció operacion de la division '{p.expr_mult} / {p.factor}'.")
        return Binario(op='/', izq=p.expr_mult, der=p.factor)
    
    # NIVEL 4: Expresiones de suma y resta
    @_('expr_mult')
    def expresion(self, p):
        return p.expr_mult
    
    @_('expresion "+" expr_mult')
    def expresion(self, p):
        print(f"Línea {p.lineno}: Se reconoció operacion de la suma '{p.expresion} + {p.expr_mult}'.")
        return Binario(op='+', izq=p.expresion, der=p.expr_mult)
    
    @_('expresion MINUS expr_mult')
    def expresion(self, p):
        print(f"Línea {p.lineno}: Se reconoció operacion de la resta '{p.expresion} - {p.expr_mult}'.")
        return Binario(op='-', izq=p.expresion, der=p.expr_mult)
    
    # Eliminamos regla vacía para expresion - causa muchos conflictos
    # Solo permitir expresiones vacías en contextos específicos

    @_('')
    def parametros_invocacion(self, p):
        return []
    #Fin de reglas expresiones aritméticas
    


    #Asignaciones e invocaciones de funciones
    @_('ID ASSIGN_PASCAL expresion ";"')
    def sentencia(self, p):
        print(f"Línea {p.lineno}: Se reconoció asignación por pascal '{p.ID} := {p.expresion}'.")
        return Asignacion(destino=Identificador(nombre=p.ID, linea=p.lineno), expr=p.expresion, linea=p.lineno)

    @_('id_calificado ASSIGN_PASCAL expresion ";"')
    def sentencia(self, p):
        print(f"Línea {p.lineno}: Se reconoció asignación por pascal '{p.id_calificado} := {p.expresion}'.")
        return Asignacion(destino=p.id_calificado, expr=p.expresion, linea=p.lineno)

    @_('ID ASSIGN_PASCAL error')
    def sentencia(self, p):
        print(f"❌ Error sintáctico en línea {p.lineno}: Se esperaba una expresión después de ':=' en la asignación por pascal.")
        return Asignacion(destino=Identificador(nombre=p.ID, linea=p.lineno))

    @_('id_calificado ASSIGN_PASCAL error')
    def sentencia(self, p):
        print(f"❌ Error sintáctico en línea {p.lineno}: Se esperaba una expresión después de ':=' en la asignación por pascal.")
        return Asignacion(destino=p.id_calificado)

    @_('invocacion ')
    def sentencia(self, p):
        return p.invocacion

    @_('ID "(" parametros_invocacion ")" ')
    def invocacion(self, p):
        print(f"Línea {p.lineno}: Se reconoció invocación de función '{p.ID}' con parámetros {p.parametros_invocacion}.")
        return Invocacion(nombre=p.ID, argumentos=p.parametros_invocacion, linea=p.lineno)

    @_('parametros_invocacion "," expresion ARROW ID')
    def parametros_invocacion(self, p):
        return p.parametros_invocacion + [(p.expresion, p.ID)]
    
    @_('parametros_invocacion "," TRUNC "(" expresion ")" ARROW ID')
    def parametros_invocacion(self, p):
        print(f"Línea {p.lineno}: Se reconoció truncamiento en argumento múltiple.")
        trunc_node = Trunc(expr=p.expresion, tipo=Tipo.UINT, linea=p.lineno)
        if self.tabla_simbolos:
            #Registro en tabla de símbolos si es necesario
            pass
        return p.parametros_invocacion + [(trunc_node, p.ID)]

    @_('expresion ARROW ID')
    def parametros_invocacion(self, p):
        print(f"Línea {p.lineno}: Se pasa al parametro formal '{p.ID}' la expresion: {p.expresion}.")
        return [(p.expresion, p.ID)]
    
    @_('CV UINT ID "," parametros')
    def parametros(self, p):
        print(f"Línea {p.lineno}: Se pasa por copia valor '{p.ID}'.")
        return [Parametro(nombre=p.ID, tipo=Tipo.UINT, por_ref=False)] + p.parametros
    
    @_('UINT ID "," parametros')
    def parametros(self, p):
        print(f"Línea {p.lineno}: Se pasa por copia-valor-resultado '{p.ID}'.")
        return [Parametro(nombre=p.ID, tipo=Tipo.UINT, por_ref=True)] + p.parametros

    @_('CV UINT ID')
    def parametros(self, p):
        print(f"Línea {p.lineno}: Se pasa por copia valor '{p.ID}'.")
        return [Parametro(nombre=p.ID, tipo=Tipo.UINT, por_ref=False)]

    @_('UINT ID')
    def parametros(self, p):
       print(f"Línea {p.lineno}: Se pasa por copia-valor-resultado '{p.ID}'.")
       return [Parametro(nombre=p.ID, tipo=Tipo.UINT, por_ref=True)]

    
    @_('')
    def parametros(self, p):
        return []
    #Fin de asignaciones e invocaciones de funciones
        
    
    
    #Reglas para la sentencia PRINT
    @_('PRINT "(" CADENA ")" ";"')
    def print(self, p):
        print(f"Línea {p.lineno}: Se reconoció sentencia PRINT con cadena '{p.CADENA}'.")
        return Print(expr=Literal(valor=p.CADENA, tipo=Tipo.STRING))

    @_('PRINT "(" expresion ")" ";"') 
    def print(self, p):
        print(f"Línea {p.lineno}: Se reconoció sentencia PRINT con expresiónes '{p.expresion}'.")
        return Print(expr=p.expresion)

    @_('print')
    def sentencia(self, p):
        return p.print
    #Fin de reglas PRINT
    


    #REGLA PARA DO-WHILE
    @_('DO bloque_sentencias WHILE "(" condicion ")" ";"')
    def sentencia(self, p):
        # Verificamos si la lista de sentencias está vacia
        if not p.bloque_sentencias:
            print(f"❌ Error Sintáctico (Línea {p.lineno}): El cuerpo del DO-WHILE no puede estar vacio (riesgo de bucle infinito).")
            self.registrar_error("Cuerpo de DO-WHILE vacio", p)
            return None
            
        print(f"Línea {p.lineno}: Se reconoció sentencia DO-WHILE con condición '{p.condicion}'.")
        return DoWhile(cuerpo=Bloque(sentencias=p.bloque_sentencias), condicion=p.condicion)

    #Fin de regla DO-WHILE

    

    #Reglas para asignaciones multiples
    @_('lista_ids ASSIGN lista_expr_const ";"')
    def sentencia(self, p):
        if len(p.lista_ids) > len(p.lista_expr_const):
            print(f"❌ Error semántico L{p.lineno}: menos expresiones que variables.")
            return ErrorNodo(mensaje="Mas variables que expresiones multi asignación", linea=p.lineno)
        print(f"Línea {p.lineno}: Se reconoció asignación múltiple con '='.")
        return MultiAsignacion(destinos=p.lista_ids, expresiones=p.lista_expr_const, linea=p.lineno)
        
    @_('expr_const')
    def lista_expr_const(self, p):
        return [p.expr_const]

    @_('lista_expr_const "," expr_const')
    def lista_expr_const(self, p):
        return p.lista_expr_const + [p.expr_const]

    # Aquí usamos una estructura independiente y jerárquica para expresiones constantes
    # para evitar conflictos con las reglas de expresiones regulares
    
    # Nivel 1: términos constantes
    @_('UINT_CONST')
    def termino_const(self, p):
                return Literal(valor=int(p.UINT_CONST), tipo=Tipo.UINT, linea=p.lineno)

    @_('DFLOAT_CONST')
    def termino_const(self, p):
        return Literal(valor=float(p.DFLOAT_CONST), tipo=Tipo.DFLOAT, linea=p.lineno)
        
    @_('"(" expr_const ")" ')
    def termino_const(self, p):
        print(f"Línea {p.lineno}: Se reconoció expresión constante entre paréntesis.")
        return p.expr_const
        
    # Nivel 2: factor constante (puede ser un término o negación)
    @_('termino_const')
    def factor_const(self, p):
        return p.termino_const
    
    """
    @_('MINUS factor_const %prec UMINUS')
    def factor_const(self, p):
        print(f"Línea {p.lineno}: Se reconoció factor constante negativo '-{p.factor_const}'.Si es negativo")
        self.tabla_simbolos.agregar_negativo(p.factor_const, linea=p.lineno)
        return ('negativo', p.factor_const)
    """
    @_('MINUS factor_const %prec UMINUS')
    def factor_const(self, p):
        valor = p.factor_const
        if isinstance(valor, int):  # UI
            print(f"Línea {p.lineno}: ❌ Error - Falta operando izquierdo en la operación, no se permite UI negativo.")
            return ('error', 'UI negativo no permitido')
        #elif isinstance(valor, float): 
        #DFLOAT
        print(f"Línea {p.lineno}: Se reconoció factor constante negativo '-{p.factor_const}'.")
        self.tabla_simbolos.agregar_negativo(p.factor_const, linea=p.lineno)
        return ('negativo', p.factor_const)
    
    # Nivel 3: expresiones multiplicativas constantes
    @_('factor_const')
    def expr_mult_const(self, p):
        return p.factor_const
        
    @_('expr_mult_const "*" factor_const')
    def expr_mult_const(self, p):
        print(f"Línea {p.lineno}: Se reconoció multiplicación de constantes.")
        return (p.expr_mult_const, '*', p.factor_const)
        
    @_('expr_mult_const "/" factor_const')
    def expr_mult_const(self, p):
        print(f"Línea {p.lineno}: Se reconoció división de constantes.")
        return (p.expr_mult_const, '/', p.factor_const)
        
    # Nivel 4: expresiones aditivas constantes
    @_('expr_mult_const')
    def expr_const(self, p):
        return p.expr_mult_const
        
    @_('expr_const "+" expr_mult_const')
    def expr_const(self, p):
        print(f"Línea {p.lineno}: Se reconoció suma de constantes.")
        return (p.expr_const, '+', p.expr_mult_const)
        
    @_('expr_const MINUS expr_mult_const')
    def expr_const(self, p):
        print(f"Línea {p.lineno}: Se reconoció resta de constantes.")
        return (p.expr_const, '-', p.expr_mult_const)
    #Fin de reglas asignaciones multiples

    



    #Inicio reglas de funciones Lambda
    @_('"(" parametro_lambda ")" bloque_sentencias "(" argumento_lambda ")"')
    def sentencia(self, p):
        print(f"Línea {p.lineno}: Se reconoció función Lambda con parámetro '{p.parametro_lambda.nombre}' y argumento '{p.argumento_lambda}'.")
        cuerpo = Bloque(sentencias=p.bloque_sentencias)  # envolver la única sentencia
        return Lambda(parametro=p.parametro_lambda, cuerpo=cuerpo, argumento=p.argumento_lambda)

    @_('"(" parametro_lambda ")" bloque_sentencias "(" argumento_lambda ")"')
    def sentencia_de_funcion(self, p):
        print(f"Línea {p.lineno}: Se reconoció función Lambda con parámetro '{p.parametro_lambda.nombre}' y argumento '{p.argumento_lambda}'.")
        cuerpo = Bloque(sentencias=p.bloque_sentencias)
        return Lambda(parametro=p.parametro_lambda, cuerpo=cuerpo, argumento=p.argumento_lambda)

    @_('UINT ID')
    def parametro_lambda(self, p):
        print(f"Línea {p.lineno}: Parámetro Lambda '{p.ID}' de tipo UINT.")
        return Parametro(nombre=p.ID, tipo=Tipo.UINT, por_ref=False)

    @_('id_calificado')
    def argumento_lambda(self, p):
        print(f"Línea {p.lineno}: Argumento Lambda calificado.")
        return p.id_calificado

    @_('UINT_CONST')
    def argumento_lambda(self, p):
        return Literal(valor=int(p.UINT_CONST), tipo=Tipo.UINT)

    @_('DFLOAT_CONST')
    def argumento_lambda(self, p):
        valf = self._to_float(p.DFLOAT_CONST)
        return Literal(valor=valf, tipo=Tipo.DFLOAT)

    @_('ID')
    def argumento_lambda(self, p):
        return Identificador(nombre=p.ID)
    
    #Regla para argumentos Dfloat negativos en funciones Lambda
    @_('MINUS DFLOAT_CONST %prec UMINUS')
    def argumento_lambda(self, p):
        print(f"Línea {p.lineno}: Se reconoció argumento de función Lambda negativo '{p.DFLOAT_CONST}'.")
        valf = self._to_float(p.DFLOAT_CONST)
        # registrar en la tabla
        if self.tabla_simbolos:
            self.tabla_simbolos.agregar_negativo(valf, linea=p.lineno)
        return Literal(valor=-valf, tipo=Tipo.DFLOAT)

    #Fin de reglas funciones Lambda
    


    #Reglas de conversiones de constantes DFLOAT a UINT en pasaje de parametros de funciones
    @_('TRUNC "(" expresion ")" ARROW ID')
    def parametros_invocacion(self, p):
        print(f"Línea {p.lineno}: Se reconoció truncamiento de DFLOAT a UINT en la expresión '{p.expresion}'.")
        return [(Trunc(expr=p.expresion), p.ID)]
    #Fin de reglas conversiones


    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # --- REGLAS DE ERROR --- #
    
    
    
    #Manejo de errores en la REGLA INICIO de programa    
    #Error si falta la llave de apertura {
    @_('ID error sentencias "}"')
    def programa(self, p):
        self.registrar_error("Falta '{' después del ID del programa", p)
        return ('PROGRAMA', p.ID, p.sentencias)
    
    @_('"{" sentencias "}"')
    def programa(self, p):
        self.registrar_error("Se esperaba un nombre de programa (ID) antes de '{'.", p)
        # Devolvemos una tupla que representa el programa sin nombre.
        return ('PROGRAMA_SIN_NOMBRE', p.sentencias)

    @_('ID "{" sentencias')
    def programa(self, p):
        self.registrar_error("Se esperaba '}' al final del programa.", p)
        return ('PROGRAMA', p.ID, p.sentencias)
    
    @_('ID sentencias')
    def programa(self, p):
        self.registrar_error("Se esperaba '{' después del ID del programa y se esperaba '}' al final del programa.", p)
        return ('PROGRAMA', p.ID, p.sentencias)
    #Fin de manejo de errores en la REGLA INICIO de programa
    



    
    
    
    #ERRORES DE FALTA DE ; EN DECLARACIONES DE SENTENCIAS
    #Utilizaremos el token error para capturar errores de sintaxis y reportar mensajes específicos cuando falte el punto y coma al final de ciertas sentencias.
    @_('UINT lista_ids error')
    def sentencia(self, p):
        self.registrar_error("Se esperaba ';' al final de la declaración de variables.", p)
        return DeclVar(tipo_decl=Tipo.UINT, ids=p.lista_ids)

    
    

    # Reglas para todas las sentencias if con manejo de errores de ;
    @_('IF "(" condicion ")" bloque_sentencias ELSE bloque_sentencias ENDIF error')
    def sentencia(self, p):
        self.registrar_error("Se esperaba ';' al final de la sentencia IF con ELSE.", p)
        return ('if', p.condicion, p.bloque_sentencias0, p.bloque_sentencias1)
    
    @_('IF "(" condicion ")" bloque_sentencias ENDIF error')
    def sentencia(self, p):
        self.registrar_error("Se esperaba ';' al final de la sentencia IF sin ELSE.", p)
        return ('if', p.condicion, p.bloque_sentencias, None)
    
     #IF comunes: con ELSE, con sentencias + final_funcion
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ELSE bloque_sentencias_de_funcion ENDIF error sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Se esperaba ';' después de ENDIF en IF con ELSE (dentro de función).", p)
        return ('if', p.condicion, p.bloque_sentencias_de_funcion0, p.bloque_sentencias_de_funcion1, p.sentencias_de_funcion, p.final_funcion)

    #IF comunes: con ELSE, solo sentencias
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ELSE bloque_sentencias_de_funcion ENDIF error sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Se esperaba ';' después de ENDIF en IF con ELSE (dentro de función).", p)
        return ('if', p.condicion, p.bloque_sentencias_de_funcion0, p.bloque_sentencias_de_funcion1, p.sentencias_de_funcion)

    #IF comunes: sin ELSE, con sentencias + final_funcion
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ENDIF error sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Se esperaba ';' después de ENDIF en IF sin ELSE (dentro de función).", p) 
        return ('if', p.condicion, p.bloque_sentencias_de_funcion, p.sentencia_de_funcion, p.final_funcion)

    #IF comunes: sin ELSE, solo sentencias
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ENDIF error sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Se esperaba ';' después de ENDIF en IF sin ELSE (dentro de función).", p)
        return ('if', p.condicion, p.bloque_sentencias_de_funcion, p.sentencia_de_funcion)

    #Final función: {then RETURN} ELSE {else RETURN} ENDIF error
    @_('IF "(" condicion ")" "{" sentencias_de_funcion final_funcion "}" ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF error')
    def final_funcion(self, p):
        self.registrar_error("Se esperaba ';' tras ENDIF en final de función (con ELSE).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, p.sentencias_de_funcion1, p.final_funcion1)

    #Final función: RETURN; ELSE RETURN; ENDIF error
    @_('IF "(" condicion ")" final_funcion ELSE final_funcion ENDIF error')
    def final_funcion(self, p):
        self.registrar_error("Se esperaba ';' tras ENDIF en final de función (con ELSE).", p)
        return ('final_funcion', p.condicion, p.final_funcion0, p.final_funcion1)

    #Final función: {then RETURN} ELSE RETURN; ENDIF error
    @_('IF "(" condicion ")" "{" sentencias_de_funcion final_funcion "}" ELSE final_funcion ENDIF error')
    def final_funcion(self, p):
        self.registrar_error("Se esperaba ';' tras ENDIF en final de función (con ELSE).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion, p.final_funcion0, p.final_funcion1)

    #Final función: RETURN; ELSE {else RETURN} ENDIF error
    @_('IF "(" condicion ")" final_funcion ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF error')
    def final_funcion(self, p):
        self.registrar_error("Se esperaba ';' tras ENDIF en final de función (con ELSE).", p)   
        return ('final_funcion', p.condicion, p.final_funcion0, p.sentencias_de_funcion, p.final_funcion1)

    #Falta ELSE: {then RETURN} ENDIF error sentencias + final_funcion
    @_('IF "(" condicion ")" "{" sentencias_de_funcion final_funcion "}" ENDIF error sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Se esperaba ';' tras ENDIF en final de función (sin ELSE).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, p.sentencias_de_funcion1, p.final_funcion1)

    #Falta ELSE: RETURN; ENDIF error sentencias + final_funcion
    @_('IF "(" condicion ")" final_funcion ENDIF error sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Se esperaba ';' tras ENDIF en final de función (sin ELSE).", p)   
        return ('final_funcion', p.condicion, p.final_funcion0, p.sentencias_de_funcion, p.final_funcion1)

    #Falta ELSE: RETURN; ENDIF error sentencias
    @_('IF "(" condicion ")" final_funcion ENDIF error sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Se esperaba ';' tras ENDIF en final de función (sin ELSE).", p)
        return ('final_funcion', p.condicion, p.final_funcion, p.sentencias_de_funcion)

    #Falta ELSE: {then RETURN} ENDIF error sentencias
    @_('IF "(" condicion ")" "{" sentencias_de_funcion final_funcion "}" ENDIF error sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Se esperaba ';' tras ENDIF en final de función (sin ELSE).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcion, p.sentencias_de_funcion1)

    #ELSE sin RETURN: then RETURN; else bloque; ENDIF error sentencias
    @_('IF "(" condicion ")" final_funcion ELSE bloque_sentencias_de_funcion ENDIF error sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Se esperaba ';' al final del IF (then con RETURN, else sin RETURN).", p)
        return ('final_funcion', p.condicion, p.final_funcion, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion)

    #ELSE sin RETURN con retorno posterior
    @_('IF "(" condicion ")" final_funcion ELSE bloque_sentencias_de_funcion ENDIF error sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Se esperaba ';' al final del IF (then con RETURN, else sin RETURN, con retorno posterior).", p)
        return ('final_funcion', p.condicion, p.final_funcion0, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion, p.final_funcion1)

    #THEN bloque RETURN; ELSE bloque; ENDIF error sentencias
    @_('IF "(" condicion ")" "{" sentencias_de_funcion final_funcion "}" ELSE bloque_sentencias_de_funcion ENDIF error sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Se esperaba ';' al final del IF (then con RETURN, else sin RETURN).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcion, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion1)

    #THEN bloque RETURN; ELSE bloque; ENDIF error sentencias + final_funcion
    @_('IF "(" condicion ")" "{" sentencias_de_funcion final_funcion "}" ELSE bloque_sentencias_de_funcion ENDIF error sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Se esperaba ';' al final del IF (then con RETURN, else sin RETURN, con retorno posterior).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcio0, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion1, p.final_funcion1)

    #THEN sin RETURN, ELSE con RETURN; ENDIF error sentencias
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ELSE final_funcion ENDIF error sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Se esperaba ';' al final del IF (then sin RETURN, else con RETURN).", p)
        return ('final_funcion_incompleto', p.condicion, p.sentencias_de_funcion0, p.final_funcion, p.sentencias_de_funcion1)

    #THEN sin RETURN, ELSE {RETURN}; ENDIF error sentencias
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF error sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Se esperaba ';' al final del IF (then sin RETURN, else con RETURN).", p)
        return ('final_funcion_incompleto', p.condicion, p.sentencias_de_funcion0, p.final_funcion, p.sentencias_de_funcion1)

    #THEN sin RETURN, ELSE con RETURN; ENDIF error sentencias + final_funcion
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ELSE final_funcion ENDIF error sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Se esperaba ';' al final del IF (then sin RETURN, else con RETURN, con retorno posterior).", p)
        return ('final_funcion_incompleto', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, p.sentencias_de_funcion1, p.final_funcion1)

    #THEN sin RETURN, ELSE {RETURN}; ENDIF error sentencias + final_funcion
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF error sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Se esperaba ';' al final del IF (then sin RETURN, else con RETURN, con retorno posterior).", p)
        return ('final_funcion_incompleto', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, p.sentencias_de_funcion1, p.final_funcion1)

    @_('RETURN "(" expresion ")" error')
    def final_funcion(self, p):
        self.registrar_error("Se esperaba ';' al final de la sentencia RETURN.", p)
        return ('RETURN', p.expresion)
    # Fin de reglas IF con manejo de errores de ;


    

    #Manejo de errores en sentencias dentro de funciones. Los mismos manejos que en las sentencias normales.
    @_('UINT lista_ids error')
    def sentencia_de_funcion(self, p):
        self.registrar_error("Se esperaba ';' al final de la declaración de variables.", p)
        return DeclVar(tipo_decl=Tipo.UINT, ids=p.lista_ids)
    
    
    @_('ID ASSIGN_PASCAL expresion error')
    def sentencia_de_funcion(self, p):
        self.registrar_error("Se esperaba ';' al final de la asignación por pascal.", p)
        return ('asignacion_pascal', p.ID, p.expresion)
    
    @_('ID ASSIGN_PASCAL error')
    def sentencia_de_funcion(self, p):
        self.registrar_error("Se esperaba una expresión después de ':=' en la asignación por pascal.", p)
        return ('asignacion_pascal_incompleta', p.ID)
    
    @_('id_calificado ASSIGN_PASCAL error')
    def sentencia_de_funcion(self, p):
        self.registrar_error("Se esperaba una expresión después de ':=' en la asignación por pascal.", p)
        return ('asignacion_pascal_incompleta', p.id_calificado)
    
    @_('id_calificado ASSIGN_PASCAL expresion error')
    def sentencia_de_funcion(self, p):
        self.registrar_error("Se esperaba ';' al final de la asignación por pascal.", p)
        return ('asignacion_pascal', p.id_calificado, p.expresion)

    @_('DO bloque_sentencias WHILE "(" condicion ")" error')
    def sentencia_de_funcion(self, p):
        self.registrar_error("Se esperaba ';' al final de la sentencia DO-WHILE.", p)
        return DoWhile(cuerpo=Bloque(sentencias=p.bloque_sentencias), condicion=p.condicion)

    @_('lista_ids ASSIGN lista_expr_const error')
    def sentencia_de_funcion(self, p):
        if len(p.lista_ids) > len(p.lista_expr_const):
            self.registrar_error("Se esperaba ';' al final de la declaración de variables.", p)
            return ErrorNodo(mensaje="Aridad en multi-asignación")
        return MultiAsignacion(destinos=p.lista_ids, expresiones=p.lista_expr_const)
     #Fin de manejo de errores en sentencias dentro de funciones

    
    

    #Manejo de error ; en print
    @_('PRINT "(" CADENA ")" error')
    def print(self, p):
        self.registrar_error("Se esperaba ';' al final de la sentencia PRINT con cadena.", p)
        return Print(expr=Literal(valor=p.CADENA, tipo=Tipo.STRING))


    @_('PRINT "(" expresion ")" error')
    def print(self, p):
        self.registrar_error("Se esperaba ';' al final de la sentencia PRINT con expresiones.", p)
        return Print(expr=p.expresion)

    #Fin de manejo de error ; en print



    #Manejo de error ; en DO-WHILE
    @_('DO bloque_sentencias WHILE "(" condicion ")" error')
    def sentencia(self, p):
        self.registrar_error("Se esperaba ';' al final de la sentencia DO-WHILE.", p)
        return DoWhile(cuerpo=Bloque(sentencias=p.bloque_sentencias), condicion=p.condicion)

    #Fin de manejo de error ; en DO-WHILE




    #Manejo de error ; en asignacion multiples y ASSIGN_PASCAL
    @_('lista_ids ASSIGN lista_expr_const error')
    def sentencia(self, p):
        if len(p.lista_ids) > len(p.lista_expr_const):
            self.registrar_error("Se esperaba ';' al final de la declaración de variables.", p)
            return ErrorNodo(mensaje="Aridad en multi-asignación")
        return MultiAsignacion(destinos=p.lista_ids, expresiones=p.lista_expr_const)
    
    @_('ID ASSIGN_PASCAL expresion error')
    def sentencia(self, p):
        self.registrar_error("Se esperaba ';' al final de la asignación por pascal.", p)
        return Asignacion(destino=Identificador(nombre=p.ID, linea=p.lineno), expr=p.expresion)

    
    @_('id_calificado ASSIGN_PASCAL expresion error')
    def sentencia(self, p):
        self.registrar_error("Se esperaba ';' al final de la asignación por pascal.", p)
        return Asignacion(destino=p.id_calificado, expr=p.expresion)
    
    @_('expr_const "+"')
    def expr_const(self, p):
        self.registrar_error("Se encontró un operador '+' sin operando derecho en expresión constante.", p)
        return (p.expr_const)
    
    
    @_('expr_const MINUS')
    def expr_const(self, p):
        self.registrar_error("Se encontró un operador '-' sin operando derecho en expresión constante.", p)
        return (p.expr_const)

    @_('"+" expr_const')
    def expr_const(self, p):
        self.registrar_error("Se encontró un operador '+' sin operando izquierdo en expresión constante.", p)
        return (p.expr_const)
    
    #Fin de manejo de error ; en asignacion multiples y ASSIGN_PASCAL


    #Reglas de manejo de faltante de nombre de funcion
    @_('UINT "(" parametros ")" "{" sentencias_de_funcion final_funcion "}" ')
    def sentencia(self, p):
        self.registrar_error("Se esperaba un nombre de función (ID) después del tipo de retorno 'UINT'.", p)
        return ('FUNCION_SIN_NOMBRE', p.parametros, p.sentencias_de_funcion)
    
    @_('UINT "(" parametros ")" "{" sentencias_de_funcion final_funcion "}" ')
    def sentencia_de_funcion(self, p):
        self.registrar_error("Se esperaba un nombre de función (ID) después del tipo de retorno 'UINT'.", p)
        return ('FUNCION_SIN_NOMBRE', p.parametros, p.sentencias_de_funcion)
    #Fin de reglas de manejo de faltante de nombre de funcion



    #Regla de manejo de error de faltante de coma en la declaracion de variables
    @_('ID lista_ids')
    def lista_ids(self, p):
        self.registrar_error("Se esperaba ',' entre los identificadores en la declaración de variables.", p)
        return [p.ID] + p.lista_ids
    #Fin de regla de manejo de error de faltante de coma en la declaracion de variables


    #Regla de manejo de error de falta de nombre del parametro formal en declaracion de funciones
    @_('CV UINT "," parametros')
    def parametros(self, p):
        self.registrar_error("Se esperaba un nombre de parámetro (ID) después de 'CV UINT'.", p)
        return [p.ID] + p.parametros
    

    @_('UINT "," parametros')
    def parametros(self, p):
        self.registrar_error("Se esperaba un nombre de parámetro (ID) después de 'UINT'.", p)
        return [p.ID] + p.parametros

    @_('CV UINT')
    def parametros(self, p):
       self.registrar_error("Se esperaba un nombre de parámetro (ID) después de 'CV UINT'.", p)
       return None

    @_('UINT')
    def parametros(self, p):
       self.registrar_error("Se esperaba un nombre de parámetro (ID) después de 'UINT'.", p)
       return None
    #Fin de regla de manejo de error de falta de nombre del parametro formal en declaracion de funciones

    #Reglas de manejo de error de falta de tipo de parametro formal en declaracion de funciones
    @_('CV ID "," parametros')
    def parametros(self, p):
        self.registrar_error("Se esperaba un tipo de parámetro (UINT) después de CV y antes del nombre '{p.ID}'.", p)
        return [p.ID] + p.parametros
    
    @_('ID "," parametros')
    def parametros(self, p):
        self.registrar_error("Se esperaba un tipo de parámetro (UINT) antes del nombre '{p.ID}'.", p)
        return [p.ID] + p.parametros
    
    @_('CV ID')
    def parametros(self, p):
        self.registrar_error("Se esperaba un tipo de parámetro (UINT) después de CV y antes del nombre '{p.ID}'.", p)
        return [p.ID]
    
    @_('ID')
    def parametros(self, p):
        self.registrar_error("Se esperaba un tipo de parámetro (UINT) antes del nombre '{p.ID}'.", p)
        return Identificador(nombre=p.ID)
    #Fin de regla de manejo de error de falta de tipo de parametro formal en declaracion de funciones


    #Regla para el manejo de error de falta de , en la lista de parametros de una funcion.
    @_('CV UINT ID error parametros')
    def parametros(self, p):
        self.registrar_error("Se esperaba ',' entre los parámetros en la declaración de la función.", p)
        return [p.ID] + p.parametros    
    @_('UINT ID error parametros')
    def parametros(self, p):
        self.registrar_error("Se esperaba ',' entre los parámetros en la declaración de la función.", p)
        return [p.ID] + p.parametros
    #Fin de regla para el manejo de error de falta de , en la lista de parametros de una funcion.


    #Reglas para el manejo de error de falta de especificacion de correspondencia de parametros
    @_('parametros_invocacion "," expresion ARROW error')
    def parametros_invocacion(self, p):
        self.registrar_error("Se esperaba un parametro formal correspondiente al parametro real.", p)
        return p.parametros_invocacion + [('Se pasa', p.expresion)]
    
    @_('expresion ARROW error')
    def parametros_invocacion(self, p):
        self.registrar_error("Se esperaba un parametro formal correspondiente al parametro real.", p)
        return [('Se pasa', p.expresion)]
    #Fin de manejo de reglas de faltante de correspondencia de parametros formales con los reales




    #Regla de manejo de error de faltante de argumento en sentencia Print
    @_('PRINT "(" error ")" ";"') 
    def print(self, p):
        self.registrar_error("Falta argumento en sentencia PRINT", p)
        return Print(expr=None)
    #FIn de regla de manejo de error de faltante de argumento en sentencia Print




    #Reglas de manejo de error de faltante de parentesis en condicion de while
    @_('DO bloque_sentencias WHILE error condicion ")" ";"')
    def sentencia_de_funcion(self, p):
        self.registrar_error("Falta parentesis izquierdo en DO-WHILE", p)
        return DoWhile(cuerpo=Bloque(sentencias=p.bloque_sentencias), condicion=p.condicion)


    @_('DO bloque_sentencias WHILE error condicion ")" ";"')
    def sentencia(self, p):
        self.registrar_error("Falta parentesis izquierdo en DO-WHILE", p)
        return DoWhile(cuerpo=Bloque(sentencias=p.bloque_sentencias), condicion=p.condicion)

    
    @_('DO bloque_sentencias WHILE "(" condicion error ";"')
    def sentencia_de_funcion(self, p):
        self.registrar_error("Falta parentesis derecho en DO-WHILE", p)
        return DoWhile(cuerpo=Bloque(sentencias=p.bloque_sentencias), condicion=p.condicion)

    
    @_('DO bloque_sentencias WHILE "(" condicion error ";"')
    def sentencia(self, p):
        self.registrar_error("Falta parentesis derecho en DO-WHILE", p)
        return DoWhile(cuerpo=Bloque(sentencias=p.bloque_sentencias), condicion=p.condicion)

    
    @_('DO bloque_sentencias WHILE error condicion error ";"')
    def sentencia(self, p):
        self.registrar_error("Falta ambos parentesis en DO-WHILE", p)
        return DoWhile(cuerpo=Bloque(sentencias=p.bloque_sentencias), condicion=p.condicion)
    
    @_('DO bloque_sentencias WHILE error condicion error ";"')
    def sentencia_de_funcion(self, p):
        self.registrar_error("Falta ambos parentesis en DO-WHILE", p)
        return DoWhile(cuerpo=Bloque(sentencias=p.bloque_sentencias), condicion=p.condicion)
    #Fin de manejo de errores de falta de parentesis en sentencia While





    #Reglas de manejo de errores de falta de parentesis en "if"
    @_('IF error condicion ")" bloque_sentencias ELSE bloque_sentencias ENDIF ";"')
    def sentencia(self, p):
        self.registrar_error("Falta parentesis izquierdo en IF con ELSE", p)
        return ('if', p.condicion, p.bloque_sentencias0, p.bloque_sentencias1)
    
    @_('IF error condicion error bloque_sentencias ELSE bloque_sentencias ENDIF ";"')
    def sentencia(self, p):
        self.registrar_error("Falta ambos parentesis en IF con ELSE", p)
        return ('if', p.condicion, p.bloque_sentencias0, p.bloque_sentencias1)
    
    @_('IF "(" condicion error bloque_sentencias ELSE bloque_sentencias ENDIF ";"')
    def sentencia(self, p):
        self.registrar_error("Falta parentesis derecho en IF con ELSE", p)
        return ('if', p.condicion, p.bloque_sentencias0, p.bloque_sentencias1)
    
    @_('IF error condicion ")" bloque_sentencias ENDIF ";"')
    def sentencia(self, p):
        self.registrar_error("Falta parentesis izquierdo en IF sin ELSE", p)
        return ('if', p.condicion, p.bloque_sentencias, None)
    
    @_('IF error condicion error bloque_sentencias ENDIF ";"')
    def sentencia(self, p):
        self.registrar_error("Falta ambos parentesis en IF sin ELSE", p)
        return ('if', p.condicion, p.bloque_sentencias, None)
    
    @_('IF "(" condicion error bloque_sentencias ENDIF ";"')
    def sentencia(self, p):
        self.registrar_error("Falta parentesis derecho en IF sin ELSE", p)
        return ('if', p.condicion, p.bloque_sentencias, None)
    
   #IF comunes: con ELSE, con sentencias + final_funcion
    @_('IF error condicion ")" bloque_sentencias_de_funcion ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis izquierdo en IF con ELSE dentro de función", p)
        return ('if', p.condicion, p.bloque_sentencias_de_funcion0, p.bloque_sentencias_de_funcion1, p.sentencias_de_funcion, p.final_funcion)

    #IF comunes: con ELSE, con sentencias + final_funcion
    @_('IF error condicion error bloque_sentencias_de_funcion ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Faltan ambos parentesis en IF con ELSE dentro de función", p)
        return ('if', p.condicion, p.bloque_sentencias_de_funcion0, p.bloque_sentencias_de_funcion1, p.sentencias_de_funcion, p.final_funcion)

    #IF comunes: con ELSE, con sentencias + final_funcion
    @_('IF "(" condicion error bloque_sentencias_de_funcion ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis derecho en IF con ELSE dentro de función", p)
        return ('if', p.condicion, p.bloque_sentencias_de_funcion0, p.bloque_sentencias_de_funcion1, p.sentencias_de_funcion, p.final_funcion)

    #IF comunes: con ELSE, solo sentencias
    @_('IF error condicion ")" bloque_sentencias_de_funcion ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis izquierdo en IF con ELSE dentro de función", p)
        return ('if', p.condicion, p.bloque_sentencias_de_funcion0, p.bloque_sentencias_de_funcion1, p.sentencias_de_funcion)

    @_('IF "(" condicion error bloque_sentencias_de_funcion ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis derecho en IF con ELSE dentro de función", p)
        return ('if', p.condicion, p.bloque_sentencias_de_funcion0, p.bloque_sentencias_de_funcion1, p.sentencias_de_funcion)

    @_('IF error condicion error bloque_sentencias_de_funcion ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Faltan ambos parentesis en IF con ELSE dentro de función", p)
        return ('if', p.condicion, p.bloque_sentencias_de_funcion0, p.bloque_sentencias_de_funcion1, p.sentencias_de_funcion)

    #IF comunes: sin ELSE, con sentencias + final_funcion
    @_('IF "(" condicion error bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis derecho en IF sin ELSE dentro de función", p)
        return ('if', p.condicion, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion, p.final_funcion)
    
    @_('IF error condicion error bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Faltan ambos parentesis en IF sin ELSE dentro de función", p)
        return ('if', p.condicion, p.bloque_sentencias_de_funcion, p.sentenciass_de_funcion, p.final_funcion)
    
    @_('IF error condicion ")" bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis izquierdo en IF sin ELSE dentro de función", p)
        return ('if', p.condicion, p.bloque_sentencias_de_funcion, p.sentencia_de_funcion, p.final_funcion)

    #IF comunes: sin ELSE, solo sentencias
    @_('IF error condicion error bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Faltan ambos parentesis en IF sin ELSE dentro de función", p)
        return ('if', p.condicion, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion)
    
    @_('IF "(" condicion error bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis derecho en IF sin ELSE dentro de función", p)
        return ('if', p.condicion, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion)
    
    @_('IF error condicion ")" bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis izquierdo en IF sin ELSE dentro de función", p)
        return ('if', p.condicion, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion)

    #Final función: {then RETURN} ELSE {else RETURN} ENDIF -> falta ENDIF
    @_('IF "(" condicion error "{" sentencias_de_funcion final_funcion "}" ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF ";"')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis derecho en final de función (con ELSE, bloques).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, p.sentencias_de_funcion1, p.final_funcion1)

    @_('IF error condicion error "{" sentencias_de_funcion final_funcion "}" ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF ";"')
    def final_funcion(self, p):
        self.registrar_error("Faltan ambos parentesis en final de función (con ELSE, bloques).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, p.sentencias_de_funcion1, p.final_funcion1)

    @_('IF error condicion ")" "{" sentencias_de_funcion final_funcion "}" ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF ";"')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis izquierdo en final de función (con ELSE, bloques).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, p.sentencias_de_funcion1, p.final_funcion1)

    #Final función: RETURN; ELSE RETURN; ENDIF -> falta ENDIF
    @_('IF error condicion ")" final_funcion ELSE final_funcion ENDIF ";"')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis izquierdo en final de función (con ELSE, returns directos).", p)
        return ('final_funcion', p.condicion, p.final_funcion0, p.final_funcion1)
    
    @_('IF error condicion error final_funcion ELSE final_funcion ENDIF ";"')
    def final_funcion(self, p):
        self.registrar_error("Faltan ambos parentesis en final de función (con ELSE, returns directos).", p)
        return ('final_funcion', p.condicion, p.final_funcion0, p.final_funcion1)
    
    @_('IF "(" condicion error final_funcion ELSE final_funcion ENDIF ";"')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis derecho en final de función (con ELSE, returns directos).", p)
        return ('final_funcion', p.condicion, p.final_funcion0, p.final_funcion1)

    #Final función: {then RETURN} ELSE RETURN; ENDIF -> falta ENDIF
    @_('IF "(" condicion error "{" sentencias_de_funcion final_funcion "}" ELSE final_funcion ENDIF ";"')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis derecho en final de función (con ELSE).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion, p.final_funcion0, p.final_funcion1)

    @_('IF error condicion error "{" sentencias_de_funcion final_funcion "}" ELSE final_funcion ENDIF ";"')
    def final_funcion(self, p):
        self.registrar_error("Faltan ambos parentesis en final de función (con ELSE).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion, p.final_funcion0, p.final_funcion1)

    @_('IF error condicion ")" "{" sentencias_de_funcion final_funcion "}" ELSE final_funcion ENDIF ";"')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis izquierdo en final de función (con ELSE).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion, p.final_funcion0, p.final_funcion1)


    #Final función: RETURN; ELSE {else RETURN} ENDIF -> falta ENDIF
    @_('IF "(" condicion error final_funcion ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF  ";"')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis derecho en final de función (con ELSE).", p)
        return ('final_funcion', p.condicion, p.final_funcion0, p.sentencias_de_funcion, p.final_funcion1)
    
    @_('IF error condicion ")" final_funcion ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF  ";"')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis izquierdo en final de función (con ELSE).", p)
        return ('final_funcion', p.condicion, p.final_funcion0, p.sentencias_de_funcion, p.final_funcion1)
    
    @_('IF error condicion error final_funcion ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF  ";"')
    def final_funcion(self, p):
        self.registrar_error("Faltan ambos parentesis en final de función (con ELSE).", p)
        return ('final_funcion', p.condicion, p.final_funcion0, p.sentencias_de_funcion, p.final_funcion1)

    #Falta ELSE: {then RETURN} ENDIF ; sentencias ... -> falta ENDIF
    @_('IF "(" condicion error "{" sentencias_de_funcion final_funcion "}" ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis derecho en final de función (sin ELSE).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, p.sentencias_de_funcion1, p.final_funcion1)

    @_('IF error condicion error "{" sentencias_de_funcion final_funcion "}" ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Faltan ambos parentesis en final de función (sin ELSE).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, p.sentencias_de_funcion1, p.final_funcion1)

    @_('IF error condicion ")" "{" sentencias_de_funcion final_funcion "}" ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis izquierdo en final de función (sin ELSE).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, p.sentencias_de_funcion1, p.final_funcion1)

    #Falta ELSE: RETURN; ENDIF ; sentencias ... -> falta ENDIF
    @_('IF "(" condicion error final_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis derecho en final de función (sin ELSE).", p)
        return ('final_funcion', p.condicion, p.final_funcion0, p.sentencias_de_funcion, p.final_funcion1)
    
    @_('IF error condicion error final_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Faltan ambos parentesis en final de función (sin ELSE).", p)
        return ('final_funcion', p.condicion, p.final_funcion0, p.sentencias_de_funcion, p.final_funcion1)
                
    @_('IF error condicion ")" final_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis izquierdo en final de función (sin ELSE).", p)
        return ('final_funcion', p.condicion, p.final_funcion0, p.sentencias_de_funcion, p.final_funcion1)

    #Falta ELSE: RETURN; ENDIF ; sentencias -> falta ENDIF
    @_('IF "(" condicion error final_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis derecho (posible falta de return si no entra al then).", p)
        return ('final_funcion', p.condicion, p.final_funcion, p.sentencias_de_funcion)
    
    @_('IF error condicion error final_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Faltan ambos parentesis (posible falta de return si no entra al then).", p)
        return ('final_funcion', p.condicion, p.final_funcion, p.sentencias_de_funcion)
    
    @_('IF error condicion ")" final_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis izquierdo (posible falta de return si no entra al then).", p)
        return ('final_funcion', p.condicion, p.final_funcion, p.sentencias_de_funcion)

    #Falta ELSE: {then RETURN} ENDIF ; sentencias -> falta ENDIF
    @_('IF "(" condicion error "{" sentencias_de_funcion final_funcion "}" ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis derecho (posible falta de return si no entra al then).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcion, p.sentencias_de_funcion1)

    @_('IF error condicion ")" "{" sentencias_de_funcion final_funcion "}" ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis izquierdo (posible falta de return si no entra al then).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcion, p.sentencias_de_funcion1)

    @_('IF error condicion error "{" sentencias_de_funcion final_funcion "}" ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Faltan ambos parentesis (posible falta de return si no entra al then).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcion, p.sentencias_de_funcion1)

    #ELSE sin RETURN: then RETURN; else bloque; ENDIF ; sentencias -> falta ENDIF
    @_('IF "(" condicion error final_funcion ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis derecho (then con RETURN, else sin RETURN).", p)
        return ('final_funcion', p.condicion, p.final_funcion, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion)

    @_('IF error condicion error final_funcion ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Faltan ambos parentesis (then con RETURN, else sin RETURN).", p)
        return ('final_funcion', p.condicion, p.final_funcion, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion)

    @_('IF error condicion ")" final_funcion ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis izquierdo (then con RETURN, else sin RETURN).", p)
        return ('final_funcion', p.condicion, p.final_funcion, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion)

    #ELSE sin RETURN con retorno posterior -> falta ENDIF
    @_('IF "(" condicion error final_funcion ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis derecho (then con RETURN, else sin RETURN, con retorno posterior).", p)
        return ('final_funcion', p.condicion, p.final_funcion0, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion, p.final_funcion1)

    @_('IF error condicion error final_funcion ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Faltan ambos parentesis (then con RETURN, else sin RETURN, con retorno posterior).", p)
        return ('final_funcion', p.condicion, p.final_funcion0, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion, p.final_funcion1)

    @_('IF error condicion ")" final_funcion ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis izquierdo (then con RETURN, else sin RETURN, con retorno posterior).", p)
        return ('final_funcion', p.condicion, p.final_funcion0, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion, p.final_funcion1)

    #THEN bloque RETURN; ELSE bloque; ENDIF ; sentencias -> falta ENDIF
    @_('IF "(" condicion error "{" sentencias_de_funcion final_funcion "}" ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis derecho (then con RETURN, else sin RETURN).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcion, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion1)

    @_('IF error condicion error "{" sentencias_de_funcion final_funcion "}" ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Faltan ambos parentesis (then con RETURN, else sin RETURN).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcion, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion1)

    @_('IF error condicion ")" "{" sentencias_de_funcion final_funcion "}" ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis izquierdo (then con RETURN, else sin RETURN).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcion, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion1)

    #THEN bloque RETURN; ELSE bloque; ENDIF ; sentencias + final_funcion -> falta ENDIF
    @_('IF "(" condicion error "{" sentencias_de_funcion final_funcion "}" ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis derecho (then con RETURN, else sin RETURN, con retorno posterior).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcio0, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion1, p.final_funcion1)

    @_('IF error condicion error "{" sentencias_de_funcion final_funcion "}" ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Faltan ambos parentesis (then con RETURN, else sin RETURN, con retorno posterior).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcio0, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion1, p.final_funcion1)

    @_('IF error condicion ")" "{" sentencias_de_funcion final_funcion "}" ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis izquierdo (then con RETURN, else sin RETURN, con retorno posterior).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcio0, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion1, p.final_funcion1)

    #THEN sin RETURN, ELSE con RETURN; ENDIF ; sentencias -> falta ENDIF
    @_('IF "(" condicion error bloque_sentencias_de_funcion ELSE final_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis derecho (return solo en rama else).", p)
        return ('final_funcion_incompleto', p.condicion, p.sentencias_de_funcion0, p.final_funcion, p.sentencias_de_funcion1)
    
    @_('IF error condicion error bloque_sentencias_de_funcion ELSE final_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Faltan ambos parentesis (return solo en rama else).", p)
        return ('final_funcion_incompleto', p.condicion, p.sentencias_de_funcion0, p.final_funcion, p.sentencias_de_funcion1)
    
    @_('IF error condicion ")" bloque_sentencias_de_funcion ELSE final_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis izquierdo (return solo en rama else).", p)
        return ('final_funcion_incompleto', p.condicion, p.sentencias_de_funcion0, p.final_funcion, p.sentencias_de_funcion1)
    

    #THEN sin RETURN, ELSE {RETURN}; ENDIF ; sentencias -> falta ENDIF
    @_('IF "(" condicion error bloque_sentencias_de_funcion ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis derecho (return solo en rama else).", p)
        return ('final_funcion_incompleto', p.condicion, p.sentencias_de_funcion0, p.final_funcion, p.sentencias_de_funcion1)
    
    @_('IF error condicion error bloque_sentencias_de_funcion ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Faltan ambos parentesis (return solo en rama else).", p)
        return ('final_funcion_incompleto', p.condicion, p.sentencias_de_funcion0, p.final_funcion, p.sentencias_de_funcion1)
    
    @_('IF error condicion ")" bloque_sentencias_de_funcion ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis izquierdo (return solo en rama else).", p)
        return ('final_funcion_incompleto', p.condicion, p.sentencias_de_funcion0, p.final_funcion, p.sentencias_de_funcion1)

    #THEN sin RETURN, ELSE con RETURN; ENDIF ; sentencias + final_funcion -> falta ENDIF
    @_('IF "(" condicion error bloque_sentencias_de_funcion ELSE final_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis derecho (return solo en rama else, con retorno posterior).", p)
        return ('final_funcion_incompleto', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, p.sentencias_de_funcion1, p.final_funcion1)
    
    @_('IF error condicion error bloque_sentencias_de_funcion ELSE final_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Faltan ambos parentesis (return solo en rama else, con retorno posterior).", p)
        return ('final_funcion_incompleto', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, p.sentencias_de_funcion1, p.final_funcion1)
    
    @_('IF error condicion ")" bloque_sentencias_de_funcion ELSE final_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis izquierdo (return solo en rama else, con retorno posterior).", p)
        return ('final_funcion_incompleto', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, p.sentencias_de_funcion1, p.final_funcion1)

    #THEN sin RETURN, ELSE {RETURN}; ENDIF ; sentencias + final_funcion -> falta ENDIF
    @_('IF "(" condicion error bloque_sentencias_de_funcion ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis derecho (return solo en rama else, con retorno posterior).", p)
        return ('final_funcion_incompleto', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, p.sentencias_de_funcion1, p.final_funcion1)
    
    @_('IF error condicion error bloque_sentencias_de_funcion ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Faltan ambos parentesis (return solo en rama else, con retorno posterior).", p)
        return ('final_funcion_incompleto', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, p.sentencias_de_funcion1, p.final_funcion1)
    
    @_('IF error condicion ")" bloque_sentencias_de_funcion ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta parentesis izquierdo (return solo en rama else, con retorno posterior).", p)
        return ('final_funcion_incompleto', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, p.sentencias_de_funcion1, p.final_funcion1)

    #Fin de manejo de falta de parentesis en sentencias if





    #Reglas de faltante de cuerpo en iteraciones
    @_('DO error WHILE "(" condicion ")" ";"')
    def sentencia_de_funcion(self, p):
        self.registrar_error("Se esperaba un cuerpo en la sentencia DO-WHILE dentro de función.", p)
        return ('DO_WHILE', p.condicion)
    
    @_('DO error WHILE "(" condicion ")" ";"')
    def sentencia(self, p):
        self.registrar_error("Se esperaba un cuerpo en la sentencia DO-WHILE.", p)
        return ('DO_WHILE', p.condicion)
    #Fin de reglas de manejo de faltante en cuerpo de iteraciones





    #Reglas de manejo de falta de endif
    @_('IF "(" condicion ")" bloque_sentencias ELSE bloque_sentencias error ";"')
    def sentencia(self, p):
        self.registrar_error("Se reconoció IF con ELSE sin token endif.", p)
        return ('if', p.condicion, p.bloque_sentencias0, p.bloque_sentencias1)
    
    @_('IF "(" condicion ")" bloque_sentencias error ";"')
    def sentencia(self, p):
        self.registrar_error("Se reconoció IF sin ELSE sin token endif.", p)
        return ('if', p.condicion, p.bloque_sentencias, None)    
    
    #IF comunes: con ELSE, con sentencias + final_funcion
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ELSE bloque_sentencias_de_funcion error ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta token ENDIF en IF con ELSE dentro de función.", p)
        return ('if', p.condicion, p.bloque_sentencias_de_funcion0, p.bloque_sentencias_de_funcion1, p.sentencias_de_funcion, p.final_funcion)

    #IF comunes: con ELSE, solo sentencias
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ELSE bloque_sentencias_de_funcion error ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta token ENDIF en IF con ELSE dentro de función.", p)
        return ('if', p.condicion, p.bloque_sentencias_de_funcion0, p.bloque_sentencias_de_funcion1, p.sentencias_de_funcion)

    #IF comunes: sin ELSE, con sentencias + final_funcion
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion error ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta token ENDIF en IF sin ELSE dentro de función.", p)
        return ('if', p.condicion, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion, p.final_funcion)

    #IF comunes: sin ELSE, solo sentencias
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion error ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta token ENDIF en IF sin ELSE dentro de función.", p)
        return ('if', p.condicion, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion)

    #Final función: {then RETURN} ELSE {else RETURN} ENDIF -> falta ENDIF
    @_('IF "(" condicion ")" "{" sentencias_de_funcion final_funcion "}" ELSE "{" sentencias_de_funcion final_funcion "}" error ";"')
    def final_funcion(self, p):
        self.registrar_error("Falta token ENDIF en final de función (con ELSE, bloques).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, p.sentencias_de_funcion1, p.final_funcion1)

    #Final función: RETURN; ELSE RETURN; ENDIF -> falta ENDIF
    @_('IF "(" condicion ")" final_funcion ELSE final_funcion error ";"')
    def final_funcion(self, p):
        self.registrar_error("Falta token ENDIF en final de función (con ELSE, returns directos).", p)
        return ('final_funcion', p.condicion, p.final_funcion0, p.final_funcion1)

    #Final función: {then RETURN} ELSE RETURN; ENDIF -> falta ENDIF
    @_('IF "(" condicion ")" "{" sentencias_de_funcion final_funcion "}" ELSE final_funcion error ";"')
    def final_funcion(self, p):
        self.registrar_error("Falta token ENDIF en final de función (con ELSE).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion, p.final_funcion0, p.final_funcion1)

    #Final función: RETURN; ELSE {else RETURN} ENDIF -> falta ENDIF
    @_('IF "(" condicion ")" final_funcion ELSE "{" sentencias_de_funcion final_funcion "}" error ";"')
    def final_funcion(self, p):
        self.registrar_error("Falta token ENDIF en final de función (con ELSE).", p)
        return ('final_funcion', p.condicion, p.final_funcion0, p.sentencias_de_funcion, p.final_funcion1)

    #Falta ELSE: {then RETURN} ENDIF ; sentencias ... -> falta ENDIF
    @_('IF "(" condicion ")" "{" sentencias_de_funcion final_funcion "}" error ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta token ENDIF en final de función (sin ELSE).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, p.sentencias_de_funcion1, p.final_funcion1)

    #Falta ELSE: RETURN; ENDIF ; sentencias ... -> falta ENDIF
    @_('IF "(" condicion ")" final_funcion error ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta token ENDIF en final de función (sin ELSE).", p)
        return ('final_funcion', p.condicion, p.final_funcion0, p.sentencias_de_funcion, p.final_funcion1)

    #Falta ELSE: RETURN; ENDIF ; sentencias -> falta ENDIF
    @_('IF "(" condicion ")" final_funcion error ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta token ENDIF (posible falta de return si no entra al then).", p)
        return ('final_funcion', p.condicion, p.final_funcion, p.sentencias_de_funcion)

    #Falta ELSE: {then RETURN} ENDIF ; sentencias -> falta ENDIF
    @_('IF "(" condicion ")" "{" sentencias_de_funcion final_funcion "}" error ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta token ENDIF (posible falta de return si no entra al then).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcion, p.sentencias_de_funcion1)

    #ELSE sin RETURN: then RETURN; else bloque; ENDIF ; sentencias -> falta ENDIF
    @_('IF "(" condicion ")" final_funcion ELSE bloque_sentencias_de_funcion error ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta token ENDIF (then con RETURN, else sin RETURN).", p)
        return ('final_funcion', p.condicion, p.final_funcion, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion)

    #ELSE sin RETURN con retorno posterior -> falta ENDIF
    @_('IF "(" condicion ")" final_funcion ELSE bloque_sentencias_de_funcion error ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta token ENDIF (then con RETURN, else sin RETURN, con retorno posterior).", p)
        return ('final_funcion', p.condicion, p.final_funcion0, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion, p.final_funcion1)

    #THEN bloque RETURN; ELSE bloque; ENDIF ; sentencias -> falta ENDIF
    @_('IF "(" condicion ")" "{" sentencias_de_funcion final_funcion "}" ELSE bloque_sentencias_de_funcion error ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta token ENDIF (then con RETURN, else sin RETURN).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcion, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion1)

    #THEN bloque RETURN; ELSE bloque; ENDIF ; sentencias + final_funcion -> falta ENDIF
    @_('IF "(" condicion ")" "{" sentencias_de_funcion final_funcion "}" ELSE bloque_sentencias_de_funcion error ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta token ENDIF (then con RETURN, else sin RETURN, con retorno posterior).", p)
        return ('final_funcion', p.condicion, p.sentencias_de_funcion0, p.final_funcio0, p.bloque_sentencias_de_funcion, p.sentencias_de_funcion1, p.final_funcion1)

    #THEN sin RETURN, ELSE con RETURN; ENDIF ; sentencias -> falta ENDIF
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ELSE final_funcion error ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta token ENDIF (return solo en rama else).", p)
        return ('final_funcion_incompleto', p.condicion, p.sentencias_de_funcion0, p.final_funcion, p.sentencias_de_funcion1)

    #THEN sin RETURN, ELSE {RETURN}; ENDIF ; sentencias -> falta ENDIF
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ELSE "{" sentencias_de_funcion final_funcion "}" error ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta token ENDIF (return solo en rama else).", p)
        return ('final_funcion_incompleto', p.condicion, p.sentencias_de_funcion0, p.final_funcion, p.sentencias_de_funcion1)

    #THEN sin RETURN, ELSE con RETURN; ENDIF ; sentencias + final_funcion -> falta ENDIF
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ELSE final_funcion error ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta token ENDIF (return solo en rama else, con retorno posterior).", p)
        return ('final_funcion_incompleto', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, p.sentencias_de_funcion1, p.final_funcion1)

    #THEN sin RETURN, ELSE {RETURN}; ENDIF ; sentencias + final_funcion -> falta ENDIF
    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ELSE "{" sentencias_de_funcion final_funcion "}" error ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta token ENDIF (return solo en rama else, con retorno posterior).", p)
        return ('final_funcion_incompleto', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, p.sentencias_de_funcion1, p.final_funcion1)

    #Fin de manejo de errores de faltante de endif
    




    #Reglas de manejo Falta de cuerpo en bloque then/else.
    @_('IF "(" condicion ")" error ELSE bloque_sentencias ENDIF ";"')
    def sentencia(self, p):
        self.registrar_error("Se reconoció IF con rama ELSE sin cuerpo en then.", p)
        return ('if', p.condicion, p.bloque_sentencias)
    
    @_('IF "(" condicion ")" bloque_sentencias ELSE error ENDIF ";"')
    def sentencia(self, p):
        self.registrar_error("Se reconoció IF con rama ELSE sin cuerpo en else.", p)
        return ('if', p.condicion, p.bloque_sentencias)
    
    @_('IF "(" condicion ")" error ELSE error ENDIF ";"')
    def sentencia(self, p):
        self.registrar_error("Se reconoció IF con rama ELSE sin cuerpos.", p)
        return ('if', p.condicion)
    
    @_('IF "(" condicion ")" error ENDIF ";"')
    def sentencia(self, p):
        self.registrar_error("Se reconoció IF sin ELSE sin cuerpo.", p)
        return ('if', p.condicion, None)
    
    #IF "comunes" (con ELSE)
    @_('IF "(" condicion ")" ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta cuerpo en rama THEN del IF dentro de función.", p)
        return ('if_falta_cuerpo_then', p.condicion, [], p.bloque_sentencias_de_funcion, p.sentencias_de_funcion, p.final_funcion)

    @_('IF "(" condicion ")" ELSE bloque_sentencias_de_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta cuerpo en rama THEN del IF dentro de función.", p)
        return ('if_falta_cuerpo_then', p.condicion, [], p.bloque_sentencias_de_funcion, p.sentencias_de_funcion)

    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ELSE ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta cuerpo en rama ELSE del IF dentro de función.", p)
        return ('if_falta_cuerpo_else', p.condicion, p.bloque_sentencias_de_funcion, [], p.sentencias_de_funcion, p.final_funcion)

    @_('IF "(" condicion ")" bloque_sentencias_de_funcion ELSE ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta cuerpo en rama ELSE del IF dentro de función.", p)
        return ('if_falta_cuerpo_else', p.condicion, p.bloque_sentencias_de_funcion, [], p.sentencias_de_funcion)

    @_('IF "(" condicion ")" ELSE ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Faltan cuerpos en THEN y ELSE del IF dentro de función.", p)
        return ('if_falta_cuerpo_ambos', p.condicion, [], [], p.sentencias_de_funcion, p.final_funcion)

    @_('IF "(" condicion ")" ELSE ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Faltan cuerpos en THEN y ELSE del IF dentro de función.", p)
        return ('if_falta_cuerpo_ambos', p.condicion, [], [], p.sentencias_de_funcion)

    #IF "comunes" sin ELSE
    @_('IF "(" condicion ")" ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta cuerpo en rama THEN del IF (sin ELSE) dentro de función.", p)
        return ('if_sin_else_falta_then', p.condicion, [], p.sentencias_de_funcion, p.final_funcion)

    @_('IF "(" condicion ")" ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta cuerpo en rama THEN del IF (sin ELSE) dentro de función.", p)
        return ('if_sin_else_falta_then', p.condicion, [], p.sentencias_de_funcion)




    # Falta cuerpo en THEN (solo aparece ELSE con su cuerpo)
    @_('IF "(" condicion ")" ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF ";"')
    def final_funcion(self, p):
        self.registrar_error("Falta cuerpo en rama THEN (final de función con bloques).", p)
        return ('final_funcion_falta_cuerpo_then', p.condicion, [], None, p.sentencias_de_funcion, p.final_funcion)

    # Falta cuerpo en ELSE (solo aparece THEN con su cuerpo)
    @_('IF "(" condicion ")" "{" sentencias_de_funcion final_funcion "}" ELSE ENDIF ";"')
    def final_funcion(self, p):
        self.registrar_error("Falta cuerpo en rama ELSE (final de función con bloques).", p)
        return ('final_funcion_falta_cuerpo_else', p.condicion, p.sentencias_de_funcion, p.final_funcion, [], None)

    # Faltan cuerpos en AMBAS ramas (aparece ELSE/ENDIF pegados)
    @_('IF "(" condicion ")" error ELSE error ENDIF ";"')
    def final_funcion(self, p):
        self.registrar_error("Faltan cuerpos en THEN y ELSE (final de función).", p)
        return ('final_funcion_falta_cuerpo_ambos', p.condicion, [], None, [], None)
    
    # Falta cuerpo en THEN (solo ELSE con retorno)
    @_('IF "(" condicion ")" ELSE final_funcion ENDIF ";"')
    def final_funcion(self, p):
        # Se esperaba un final_funcion para THEN antes de ELSE.
        self.registrar_error("Falta cuerpo en rama THEN (final de función con returns directos).", p)
        return ('final_funcion_falta_cuerpo_then', p.condicion, None, None, None, p.final_funcion)

    # Falta cuerpo en ELSE (solo THEN con retorno)
    @_('IF "(" condicion ")" final_funcion ELSE ENDIF ";"')
    def final_funcion(self, p):
        # Se esperaba un final_funcion para ELSE tras ELSE.
        self.registrar_error("Falta cuerpo en rama ELSE (final de función con returns directos).", p)
        return ('final_funcion_falta_cuerpo_else', p.condicion, None, p.final_funcion, None, None)

    # FALTA CUERPO EN ELSE (grupo: ELSE pero sin RETURN) con cola de sentencias
    @_('IF "(" condicion ")" final_funcion ELSE error ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta cuerpo en rama ELSE (después de ENDIF hay sentencias).", p)
        return ('final_funcion_falta_cuerpo_else', p.condicion, p.final_funcion, [], p.sentencias_de_funcion)

    @_('IF "(" condicion ")" final_funcion ELSE ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta cuerpo en rama ELSE (con retorno posterior tras sentencias).", p)
        return ('final_funcion_falta_cuerpo_else', p.condicion, p.final_funcion0, [], p.sentencias_de_funcion, p.final_funcion1)
       
    @_('IF "(" condicion ")" "{" sentencias_de_funcion final_funcion "}" ELSE error ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta cuerpo en rama ELSE (then tiene bloque+return, luego sentencias).", p)
        return ('final_funcion_falta_cuerpo_else', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, [], p.sentencias_de_funcion1)

    @_('IF "(" condicion ")" "{" sentencias_de_funcion final_funcion "}" ELSE ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta cuerpo en rama ELSE (then bloque+return, con retorno posterior).", p)
        return ('final_funcion_falta_cuerpo_else', p.condicion, p.sentencias_de_funcion0, p.final_funcion0, [], p.sentencias_de_funcion1, p.final_funcion1)

    # FALTA CUERPO EN THEN (grupo: THEN sin RETURN, ELSE con RETURN) con cola de sentencias
    @_('IF "(" condicion ")" error ELSE final_funcion ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta cuerpo en rama THEN (else tiene return, luego sentencias).", p)
        return ('final_funcion_falta_cuerpo_then', p.condicion, [], p.final_funcion, p.sentencias_de_funcion)

    @_('IF "(" condicion ")" ELSE final_funcion ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta cuerpo en rama THEN (else con return, con retorno posterior).", p)
        return ('final_funcion_falta_cuerpo_then', p.condicion, [], p.final_funcion0, p.sentencias_de_funcion, p.final_funcion1)

    @_('IF "(" condicion ")" error ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF ";" sentencias_de_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta cuerpo en rama THEN (else bloque+return, luego sentencias).", p)
        return ('final_funcion_falta_cuerpo_then', p.condicion, [], (p.sentencias_de_funcion0, p.final_funcion0), p.sentencias_de_funcion1)

    @_('IF "(" condicion ")" error ELSE "{" sentencias_de_funcion final_funcion "}" ENDIF ";" sentencias_de_funcion final_funcion')
    def final_funcion(self, p):
        self.registrar_error("Falta cuerpo en rama THEN (else bloque+return, con retorno posterior).", p)
        return ('final_funcion_falta_cuerpo_then', p.condicion, [], (p.sentencias_de_funcion0, p.final_funcion0), p.sentencias_de_funcion1, p.final_funcion1)


    #Fin de manejo de errores de faltante de cuerpo en sentencias then/else





    #Reglas de manejo de errores de falta de operadores en expresiones
    # Captura específicamente todas las combinaciones posibles de factores sin operadores entre ellos
    @_('UINT_CONST UINT_CONST')
    def termino(self, p):
        self.registrar_error("Se encontraron dos constantes enteras consecutivas sin operador entre ellas.", p)
        return [p.UINT_CONST0]
    
    @_('UINT_CONST DFLOAT_CONST')
    def termino(self, p):
        self.registrar_error("Se encontraron una constante entera y una constante flotante consecutivas sin operador entre ellas.", p)
        return [p.UINT_CONST]
    
    @_('DFLOAT_CONST UINT_CONST')
    def termino(self, p):
        self.registrar_error("Se encontraron una constante entera y una constante flotante consecutivas sin operador entre ellas.", p)
        return [p.DFLOAT_CONST]

    @_('DFLOAT_CONST DFLOAT_CONST')
    def termino(self, p):
        self.registrar_error("Se encontraron dos constantes flotantes consecutivas sin operador entre ellas.", p)
        return [p.DFLOAT_CONST0]

    @_('ID ID')
    def termino(self, p):
        self.registrar_error("Se encontraron dos identificadores consecutivos sin operador entre ellos.", p)
        return [p.ID0]
    
    @_('ID UINT_CONST')
    def termino(self, p):
        self.registrar_error("Se encontraron un identificador y una constante entera consecutivos sin operador entre ellos.", p)
        return [p.ID]
    
    @_('UINT_CONST ID')
    def termino(self, p):
        self.registrar_error("Se encontraron un identificador y una constante entera consecutivos sin operador entre ellos.", p)
        return [p.UINT_CONST]
    
    @_('ID DFLOAT_CONST')
    def termino(self, p):
        self.registrar_error("Se encontraron un identificador y una constante flotante consecutivos sin operador entre ellos.", p)
        return [p.ID]
    
    @_('DFLOAT_CONST ID')
    def termino(self, p):
        self.registrar_error("Se encontraron un identificador y una constante flotante consecutivos sin operador entre ellos.", p)
        return [p.DFLOAT_CONST]
    
    @_('ID invocacion')
    def termino(self, p):
        self.registrar_error("Se encontraron un identificador y una invocación de función consecutivos sin operador entre ellos.", p)
        return [p.ID]
    
    @_('invocacion ID')
    def termino(self, p):
        self.registrar_error("Se encontraron una invocación de función y un identificador consecutivos sin operador entre ellos.", p)
        return [p.invocacion]
    
    @_('UINT_CONST invocacion')
    def termino(self, p):
        self.registrar_error("Se encontraron una constante entera y una invocación de función consecutivos sin operador entre ellas.", p)
        return [p.UINT_CONST]
    
    @_('invocacion UINT_CONST')
    def termino(self, p):
        self.registrar_error("Se encontraron una invocación de función y una constante entera consecutivos sin operador entre ellas.", p)
        return [p.invocacion]
    
    @_('DFLOAT_CONST invocacion')
    def termino(self, p):
        self.registrar_error("Se encontraron una constante flotante y una invocación de función consecutivos sin operador entre ellas.", p)
        return [p.DFLOAT_CONST]
    
    @_('invocacion DFLOAT_CONST')
    def termino(self, p):
        self.registrar_error("Se encontraron una invocación de función y una constante flotante consecutivos sin operador entre ellas.", p)
        return [p.invocacion]
    #Fin de manejo de errores de falta de operador en expresiones
    



    #Regla de manejo de falta de operandos en expresiones
    @_('expresion MINUS error')
    def expresion(self, p):
        self.registrar_error("Se encontró un operador '-' sin operando derecho.", p)
        return (p.expresion)
    
    @_('expresion "+" error')
    def expresion(self, p):
        self.registrar_error("Se encontró un operador '+' sin operando derecho.", p)
        #No se forma arbol
        return (p.expresion)
    
    @_('error "+" expr_mult')
    def expresion(self, p):
        self.registrar_error("Se encontró un operador '+' sin operando izquierdo.", p)
        return (p.expr_mult)
    
    @_('error MINUS expr_mult')
    def expresion(self, p):
        self.registrar_error("Se encontró un operador '-' sin operando izquierdo.", p)
        return (p.expr_mult)
    
    @_('expr_mult "*"')
    def expr_mult(self, p):
        self.registrar_error("Se encontró un operador '*' sin operando derecho.", p)
        return (p.expr_mult)
    
    @_('expr_mult "/"')
    def expr_mult(self, p):
        self.registrar_error("Se encontró un operador '/' sin operando derecho.", p)
        return (p.expr_mult)
    
    @_('expr_mult_const "*"')
    def expr_mult_const(self, p):
        self.registrar_error("Se encontró un operador '*' sin operando derecho.", p)
        return (p.expr_mult_const)

    @_('expr_mult_const "/"')
    def expr_mult_const(self, p):
        self.registrar_error("Se encontró un operador '/' sin operando derecho.", p)
        return (p.expr_mult_const)
    
    @_('error "*" expr_mult')
    def expr_mult(self, p):
        self.registrar_error("Se encontró un operador '*' sin operando izquierdo.", p)
        return (p.expr_mult)
    
    @_('error "/" expr_mult')
    def expr_mult(self, p):
        self.registrar_error("Se encontró un operador '/' sin operando izquierdo.", p)
        return (p.expr_mult)
    
    @_('error "*" expr_mult_const')
    def expr_mult_const(self, p):
        self.registrar_error("Se encontró un operador '*' sin operando izquierdo.", p)
        return (p.expr_mult_const)

    @_('error "/" expr_mult_const')
    def expr_mult_const(self, p):
        self.registrar_error("Se encontró un operador '/' sin operando izquierdo.", p)
        return (p.expr_mult_const)
    #Fin de manejo de errores de falta de operandos en expresiones




    #Regla de manejo de errores para asignaciones multiples ante el faltante de , del lado derecho.
    #Fin de manejo de errores para asignaciones multiples con faltante de "," del ladro derecho.



    #Reglas de manejo de errore de faltante de comparador en comparacion
    @_('expresion error')
    def condicion(self, p):
        self.registrar_error("Se esperaba un comparador luego de la expresión.", p)
        return (None)
    #Fin de manejo de errores de faltante de comparador en comparacion

    #Regla de falta de While en sentencia Do-While(Tema 14)
    @_('DO bloque_sentencias error "(" condicion ")" ";"')
    def sentencia(self, p):
        self.registrar_error("Se reconoció sentencia DO-WHILE sin la palabra reservada 'WHILE'.", p)
        return DoWhile(cuerpo=Bloque(sentencias=p.bloque_sentencias), condicion=p.condicion)
    
    @_('DO bloque_sentencias error condicion ")" ";"')
    def sentencia(self, p):
        self.registrar_error("Se reconoció sentencia DO-WHILE sin la palabra reservada 'WHILE' y sin parentesis izquierdo.", p)
        return ('DO_WHILE', p.bloque_sentencias, p.condicion)
    
    @_('DO bloque_sentencias error condicion error')
    def sentencia(self, p):
        self.registrar_error("Se reconoció sentencia DO-WHILE sin la palabra reservada 'WHILE' y sin parentesis izquierdo ni derecho.", p)
        return ('DO_WHILE', p.bloque_sentencias, p.condicion)
    
    @_('DO bloque_sentencias error "(" condicion ")" ";"')
    def sentencia_de_funcion(self, p):
        self.registrar_error("Se reconoció sentencia DO-WHILE sin la palabra reservada 'WHILE'.", p)
        return DoWhile(cuerpo=Bloque(sentencias=p.bloque_sentencias), condicion=p.condicion)

    
    @_('DO bloque_sentencias error condicion ")" ";"')
    def sentencia_de_funcion(self, p):
        self.registrar_error("Se reconoció sentencia DO-WHILE sin la palabra reservada 'WHILE' y sin parentesis izquierdo.", p)
        return ('DO_WHILE', p.bloque_sentencias, p.condicion)
    
    @_('DO bloque_sentencias error condicion error')
    def sentencia_de_funcion(self, p):
        self.registrar_error("Se reconoció sentencia DO-WHILE sin la palabra reservada 'WHILE' y sin parentesis izquierdo ni derecho.", p)
        return ('DO_WHILE', p.bloque_sentencias, p.condicion)
    #Fin de regla de falta de While en sentencia Do-While(Tema 14)



    #Regla de falta de "," en lista de elementos de lado izquierdo o de lado derecho(tema 17)
    #Del lazo izquierdo ya se maneja con la falta de coma en "lista_ids" (linea 767)
    #Realizamos unicamente el manejo de errores en el lado derecho
    @_('lista_ids ASSIGN error expr_const ";"')
    def sentencia_de_funcion(self, p):
        if len(p.lista_ids) > len(p.lista_expr_const):
            self.registrar_error("Error semantico: menos expresiones que variables en multi-asignacion.", p)
            return ErrorNodo(mensaje="Aridad en multi-asignación")
        return MultiAsignacion(destinos=p.lista_ids, expresiones=p.lista_expr_const)
    
    @_('lista_ids ASSIGN error expr_const ";"')
    def sentencia(self, p):
        if len(p.lista_ids) > len(p.lista_expr_const):
            self.registrar_error("Error semantico: menos expresiones que variables en multi-asignacion.", p)
            return ErrorNodo(mensaje="Aridad en multi-asignación")
        return MultiAsignacion(destinos=p.lista_ids, expresiones=p.lista_expr_const)
    #Fin de manejo de errores de falta de "," en lista de elementos de lado izquierdo o de lado derecho(tema 17)
    
    
    
    
    #Regla de manejo de error de falta de delimitadores { y/o } de la función Lambda.
    @_('"(" parametro_lambda ")" error sentencias "}" "(" argumento_lambda ")"')
    def sentencia(self, p):
        self.registrar_error("Se esperaba delimitador izquierdo después de la declaración de la función Lambda.", p)
        return ('funcion_lambda', p.parametro_lambda, p.sentencias, p.argumento_lambda)

    @_('"(" parametro_lambda ")" error sentencias "}" "(" argumento_lambda ")"')
    def sentencia_de_funcion(self, p):
        self.registrar_error("Se esperaba delimitador izquierdo después de la declaración de la función Lambda.", p)
        return ('funcion_lambda', p.parametro_lambda, p.sentencias, p.argumento_lambda)
    
    @_('"(" parametro_lambda ")" "{" sentencias error "(" argumento_lambda ")"')
    def sentencia(self, p):
        self.registrar_error("Se esperaba delimitador derecho después de la declaración de la función Lambda.", p)
        return ('funcion_lambda', p.parametro_lambda, p.sentencias, p.argumento_lambda)

    @_('"(" parametro_lambda ")" "{" sentencias error "(" argumento_lambda ")"')
    def sentencia_de_funcion(self, p):
        self.registrar_error("Se esperaba delimitador derecho después de la declaración de la función Lambda.", p)
        return ('funcion_lambda', p.parametro_lambda, p.sentencias, p.argumento_lambda)


    @_('"(" parametro_lambda ")" error sentencias error "(" argumento_lambda ")"')
    def sentencia(self, p):
        self.registrar_error("Se esperaban ambos delimitadores después de la declaración de la función Lambda.", p)
        return ('funcion_lambda', p.parametro_lambda, p.sentencias, p.argumento_lambda)

    @_('"(" parametro_lambda ")" error sentencias "}" error argumento_lambda ")"')
    def sentencia_de_funcion(self, p):
        self.registrar_error("Se esperaban ambos delimitadores después de la declaración de la función Lambda.", p)
        return ('funcion_lambda', p.parametro_lambda, p.sentencias, p.argumento_lambda)
    #Fin de manejo de error de falta de delimitadores { y/o } de la función Lambda.

    



    #Reglas de falta de delimitador en sentencias TRUNC(Tema 31)
    @_('TRUNC error expresion ")" ARROW ID')
    def parametros_invocacion(self, p):
        self.registrar_error("Se esperaba delimitador izquierdo en la función TRUNC.", p)
        return [(Trunc(expr=p.expresion), p.ID)]
    
    @_('TRUNC "(" expresion error ARROW ID')
    def parametros_invocacion(self, p):
        self.registrar_error("Se esperaba delimitador derecho en la función TRUNC.", p)
        return [(Trunc(expr=p.expresion), p.ID)]
    
    @_('TRUNC error expresion error ARROW ID')
    def parametros_invocacion(self, p):
        self.registrar_error("Se esperaban ambos delimitadores en la función TRUNC.", p)
        return [(Trunc(expr=p.expresion), p.ID)]
    #Fin de reglas de falta de delimitador en sentencias TRUNC(Tema 31)

    #FIN DE MANEJO DE ERRORES ;

    # Manejo de errores sintácticos
    def error(self, tok):
        if self.error_flag:
            return
        self.error_flag = True
        if tok:
            self.registrar_error(f"Token inesperado '{tok.value}' de tipo {tok.type}", tok)
            # Estrategia mínima de sincronización: descartar token y continuar
            self.errok()
        else:
            self.registrar_error("Fin de entrada inesperado (EOF).", None)
            return