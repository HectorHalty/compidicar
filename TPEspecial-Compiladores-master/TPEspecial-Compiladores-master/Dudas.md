## PARSER:
       agregue:
        en parser_pruebas:
            nada.txt
            lambda_idcalificado.txt
            completo.txt. En completo.txt si en la linea 42 el trunc esta en el ultimo parametro, da error ya que no puede reconocer al token trunc en el ultimo parametro. ver eso
            mas_prefijos.txt
            sentencias_vacias.txt
            sentencias_vacias1.5.txt
        en semantico_pruebas:
            algo.txt
            sintaxisSinSemantica.txt
            
        en el paser.py agregue:
            @_('error MINUS expr_mult') en la definicion:
                def expresion(self, p):
                    print(f"❌ Error sintáctico en línea {p.lineno}: Se encontró un operador '-' sin operando izquierdo.")
                    return (p.expr_mult)
                Faltaba MINUS en el decorador, y daba errores en montones de lados

            def expresion(self, p):
                print(f"❌ Error sintáctico en línea {p.lineno}: Se encontró un operador '-' sin operando izquierdo.")
                return (p.expr_mult)"

                agregue un "-" en el decorador, xq sino aparecia en todos lados ese error.

            para que las ASSIGN_PASCAL reconozcan bien el error:
                    @_('ID ASSIGN_PASCAL error')
                        def sentencia(self, p):
                            print(f"❌ Error sintáctico en línea {p.lineno}: Se esperaba una expresión después de ':=' en la asignación por pascal.")
                            return ('asignacion_pascal_incompleta', p.ID)
                        
                    @_('id_calificado ASSIGN_PASCAL error')
                        def sentencia(self, p):
                            print(f"❌ Error sintáctico en línea {p.lineno}: Se esperaba una expresión después de ':=' en la asignación por pascal.")
                            return ('asignacion_pascal_incompleta', p.id_calificado)
                    
                    y tambien en sentencia_de_funcion

            agregue linea 415 para que se pueda tener parametros vacios en una funcion

 ## Analisis Semantico:   
        Mis dudas del enunciado
            Uso:
                - Incorporar un atributo Uso en la Tabla de Símbolos, indicando el uso de cada identificador en el programa (nombre de variable, nombre de función, nombre de programa, nombre de parámetro, etc.).
            Otros Atributos:
                -Se podrán Incorporar atributos adicionales a las entradas de la Tabla de Símbolos, de acuerdo a los temas particulares asignados


        Hay que validar bien lo de IDCalificado

        Fijarnos la linea 182 y 161 de Parser.py, creo que falta devolver final_funcion, ahi lp agregue y no se rompio.
        Hablar lo de if en la funcion, creo q se arreglar lo q no andaba el dia q entrega






## Ver lo que me dijo en clase: 
    -Recorrer una sola vez el codigo en el main. (FALTA ANEXAR EL RECORRIDO DEL ANALISIS SEMANTICO. HACERLO DPS DE LO DEL AST EN EL PARSER)
    -Formar el ast ya desde la salida del parser.
    -Realizar mas txt con mas tipos diferentes de pruebas. Estos debieran ser lo mas completos posibles y diferentes entre ellos.
    -Tratar de hacer el analisis semantico  si hay errores sintacticos previos en el codigo. Depende puntualmente de que tanto se pueda salvar un error. Por ejemplo, la falta de ; no deberia ser problema para hacer el analisis semantico.
    -tratar de ver todos los casos q veamos y arreglarlos antes de la entrega.
    -Ver que tan eficiente quedo el analisis semantico en el main.
    -Saberse bien el codigo, las intenciones, y las decisiones de diseño.

## ARREGLE LO DEL IF EN LA FUNCION. (saque lo de la 102 que ahora esta comentado, y los final_funcion contienen TODOS los posibles if en una funcion, contando los que dan posibles errores por POSIBLE falta de retorno)
# HAY QUE PROBAR TODOS LOS CASOS DE UN IF DENTRO DE UNA FUNCION, LO HARIA ANTES DE LA ENTREGA. FIJEMOSNOS EN OTRAS COSAS X AHORA.
        Pruebas a rehacer:
            -Los if dentro de funcion. todos los casos
            -La falta de cuerpo en esos if.
            -La falta de endif en esos if nuevos.
            - La FALTA DE PARENTESIS (matame y brabalo para la posteridad)
            -Preguntar que onda los errores q no nos marcaron.
            -Como deben aparecer las cadenas en la tabla



Que la funcion ya tenga como retorno TIPO.UINT


Ver en la tabla repeticion de nombre de lexemas.
Nos salteamos lo del mangling.