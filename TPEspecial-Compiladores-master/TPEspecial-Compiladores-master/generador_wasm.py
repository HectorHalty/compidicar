import copy
from AnalisisSemantico import (
    Nodo, Binario, Unario, Literal, Identificador, AuxiliarWasm, Tipo,
    ArbolSemantico, Programa, Bloque, DeclVar, Asignacion, MultiAsignacion,
    Si, DoWhile, Print, Return, Invocacion, Funcion, Parametro, IdCalificado, Lambda, Trunc
)

class GeneradorWasm:
    def __init__(self):
        self._reset()

    def _reset(self):
        self._funciones_generadas = {}
        self._globales = {}
        self._meta_funciones = {} #para semantica de cvr
        self._contextos = [{
            "codigo": [],
            "locales": set(),
            "parametros": set(), # Nuevo: rastrear parametros para no redeclararlos como locales
            "variables_usuario": {},
            "funcion_actual": None,
            "contador_aux": 0,
            "contador_bloques": 0
        }]

    def _ctx(self):
        return self._contextos[-1]

    def _push_context(self):
        self._contextos.append({
            "codigo": [],
            "locales": set(),
            "parametros": set(), # Nuevo contexto empieza sin parametros
            "variables_usuario": self._ctx()["variables_usuario"].copy(),
            "funcion_actual": None,
            "contador_aux": self._ctx()["contador_aux"],
            "contador_bloques": self._ctx()["contador_bloques"]
        })

    def _pop_context(self):
        if len(self._contextos) > 1:
            ctx = self._contextos.pop()
            self._ctx()["contador_aux"] = ctx["contador_aux"]
            self._ctx()["contador_bloques"] = ctx["contador_bloques"]
            return ctx
        return None

    def _nueva_var_aux(self, tipo_wasm: str):
        ctx = self._ctx()
        nombre = f"$t{ctx['contador_aux']}"
        ctx['contador_aux'] += 1
        ctx['locales'].add(f"(local {nombre} {tipo_wasm})")
        return nombre
    
    def _asegurar_local(self, nombre_wasm: str, tipo_nodo: Tipo):
        """
        Asegura que una variable este declarada en el ambito local actual.
        Si es global o parametro, no hace nada.
        Si no esta declarada, la agrega a la lista de locales para evitar errores de Wasm.
        """
        ctx = self._ctx()
        if nombre_wasm in self._globales:
            return
        if nombre_wasm in ctx['parametros']:
            return
        
        tipo_wasm = self._get_tipo_wasm(tipo_nodo)
        decl = f"(local {nombre_wasm} {tipo_wasm})"
        ctx['locales'].add(decl)

    def _get_tipo_wasm(self, tipo_nodo: Tipo) -> str:
        if tipo_nodo == Tipo.UINT: return "i32"
        if tipo_nodo == Tipo.DFLOAT: return "f64"
        return "i32"

    def _get_op_instruccion(self, op: str, tipo_operando: Tipo):
        tipo_wasm = self._get_tipo_wasm(tipo_operando)
        ops = {
            '+': f'{tipo_wasm}.add', '-': f'{tipo_wasm}.sub', '*': f'{tipo_wasm}.mul',
            '/': f'{tipo_wasm}.div_s' if tipo_wasm == 'i32' else f'{tipo_wasm}.div',
            '==': f'{tipo_wasm}.eq', '!=': f'{tipo_wasm}.ne',
            '<': f'{tipo_wasm}.lt_s' if tipo_wasm == 'i32' else f'{tipo_wasm}.lt',
            '<=': f'{tipo_wasm}.le_s' if tipo_wasm == 'i32' else f'{tipo_wasm}.le',
            '>': f'{tipo_wasm}.gt_s' if tipo_wasm == 'i32' else f'{tipo_wasm}.gt',
            '>=': f'{tipo_wasm}.ge_s' if tipo_wasm == 'i32' else f'{tipo_wasm}.ge',
        }
        return ops.get(op)

    '''
        Genera el ciclo principal junto con _procesar_bloque.
        Hace una copia profunda del arbol porque la generacion de codigo ira modificando el arbol y no queremos perder el orginal
    '''
    def generar(self, arbol_semantico: ArbolSemantico):
        self._reset()
        arbol_copiado = copy.deepcopy(arbol_semantico.raiz)

        # Aseguramos que sea la raiz del arbol. 
        if isinstance(arbol_copiado, Programa) and isinstance(arbol_copiado.cuerpo, Bloque):
            self._procesar_bloque(arbol_copiado.cuerpo)

        # Obtiene el contexto actual del arbol
        main_ctx = self._ctx()
        # Tomamos las declaraciones 
        declaraciones_locales = "\n    ".join(sorted(list(main_ctx['locales'])))
        # Tomamos el cuerpo del bloque main 
        cuerpo_main = "\n    ".join(main_ctx['codigo'])
        
        imports = [
            '(import "env" "abort" (func $abort (param i32)))',
            '(import "env" "console_log_i32" (func $console_log_i32 (param i32)))',
            '(import "env" "console_log_f64" (func $console_log_f64 (param f64)))'
        ]
        import_section = "\n  ".join(imports)
        
        # Toma los valores (codigo fuente generado) de las funciones generadas que contienen el codigo Wasm de cada funcion definida por el usuario
        # Se pone en el modulo Wasm Final, antes de la funcion main, para que todas las funciones definidas por el usuario esten en el codigo wat generado.
        funciones_generadas_str = "\n\n".join(self._funciones_generadas.values())
        # Toma las globales generadas (si las hay)
        globales_generados_str = "\n".join(self._globales.values())
        # Retornamos un archivo en codigo Web Assembly 
        return f"""(module
  {import_section}

{globales_generados_str}

{funciones_generadas_str}

  (func $main (result i32)
    {declaraciones_locales}
    {cuerpo_main}
    i32.const 0
  )
  (export "main" (func $main))
)"""
    '''
        Es quien comienza el procesamiento del arbol,
        puede recibir un bloque o una lista de sentencias. 
        Cualquiera debe ser analizada por procesar_sentencia, 1 por 1 para generar el codigo correspondiente
        a dicha sentencia.
    '''
    def _procesar_bloque(self, bloque_o_lista):
        sentencias_a_procesar = []
        if isinstance(bloque_o_lista, Bloque):
            sentencias_a_procesar = bloque_o_lista.sentencias
        elif isinstance(bloque_o_lista, list):
            sentencias_a_procesar = bloque_o_lista

        for sentencia in sentencias_a_procesar:
            self._procesar_sentencia(sentencia)

    def _procesar_sentencia(self, sentencia: Nodo):
        # Obtenemos el contexto actual de la funcion/bloque/sentencia.
        ctx = self._ctx()
        # Lista de instrucciones ( codigo Wasm ) que se esta generando, guardaremos lo que vamos generando. 
        codigo = ctx['codigo']

        '''
            Es un gran if/elif que decide que nodo es el actual del AST 
            y genera el codigo wasm correspondiente
        '''

        '''
            Por cada identificador declarado, lo agrega a contexto como variable local con su tipo
            La idea es poder usar local.set $nombre y local.get $nombre en el codigo generado.
        '''
        if isinstance(sentencia, DeclVar):
            for ident in sentencia.ids:
                nombre_var = f"${ident.nombre}"
                ctx['variables_usuario'][ident.nombre] = nombre_var
                tipo_wasm = self._get_tipo_wasm(sentencia.tipo_decl)

                # Si estamos en el contexto global (no hay padre), es una variable global
                if self._ctx().get("funcion_actual") is None and len(self._contextos) == 1:
                    self._globales[nombre_var] = f"(global {nombre_var} (mut {tipo_wasm}) ({tipo_wasm}.const 0))"
                else: # Si no, es una variable local a la funcion
                    ctx['locales'].add(f"(local {nombre_var} {tipo_wasm})")
        
        
        elif isinstance(sentencia, (Asignacion, MultiAsignacion)):
            '''
                Maneja asignaciones y asingaciones multiples.
                Obtiene la/s expresiones y el/los destinos. 
                sigue....
            '''
            destinos = [sentencia.destino] if isinstance(sentencia, Asignacion) else sentencia.destinos
            expresiones = [sentencia.expr] if isinstance(sentencia, Asignacion) else sentencia.expresiones

            nodos_auxiliares = [self._reducir_expresion_a_valor(expr) for expr in expresiones]
            for i, destino_ident in enumerate(destinos):
                if i < len(nodos_auxiliares) and isinstance(destino_ident, (Identificador, IdCalificado)):
                    nodo_aux = nodos_auxiliares[i]
                    
                    # Si el nodo auxiliar no es una variable temporal de wasm, significa que la expresion
                    # no pudo ser resuelta a un valor (ej. AA.A). En este caso, no generamos codigo
                    # para la asignacion para evitar errores de pila vacia.
                    if not isinstance(nodo_aux, AuxiliarWasm):
                        continue

                    nombre_simple = ""
                    if isinstance(destino_ident, Identificador):
                        nombre_simple = destino_ident.nombre
                    elif isinstance(destino_ident, IdCalificado):
                        # Para la asignacion, el nombre relevante es el del atributo.
                        nombre_simple = destino_ident.atributo.nombre

                    nombre_var_wasm = self._get_nombre_variable_wasm(nombre_simple)

                    if nombre_var_wasm:
                        self._generar_codigo_hoja(nodo_aux)
                        if nombre_var_wasm in self._globales:
                            codigo.append(f"global.set {nombre_var_wasm}")
                        else:
                            # Aseguramos que la variable exista localmente si estamos asignando a una variable de un padre
                            self._asegurar_local(nombre_var_wasm, destino_ident.tipo)
                            codigo.append(f"local.set {nombre_var_wasm}")

        elif isinstance(sentencia, Si):
            nodo_cond_aux = self._reducir_expresion_a_valor(sentencia.condicion)
            self._generar_codigo_hoja(nodo_cond_aux)
            
            codigo.append("if")
            self._procesar_bloque(sentencia.entonces)
            if sentencia.sino:
                codigo.append("else")
                self._procesar_bloque(sentencia.sino)
            codigo.append("end")

        elif isinstance(sentencia, DoWhile):
            loop_id = ctx['contador_bloques']
            ctx['contador_bloques'] += 1
            codigo.append(f"(block $exit_loop_{loop_id}")
            codigo.append(f"  (loop $loop_body_{loop_id}")
            self._procesar_bloque(sentencia.cuerpo)
            
            nodo_cond_aux = self._reducir_expresion_a_valor(sentencia.condicion)
            self._generar_codigo_hoja(nodo_cond_aux)

            codigo.append(f"    br_if $loop_body_{loop_id}")
            codigo.append("  )")
            codigo.append(")")

        elif isinstance(sentencia, Print):
            nodo_aux = self._reducir_expresion_a_valor(sentencia.expr)
            # Si el tipo es string, no genera nada ya que WASM no permite almacenar Strings
            if getattr(nodo_aux, "tipo", None) == Tipo.STRING:
                return  # No hacer nada para prints de cadenas
            self._generar_codigo_hoja(nodo_aux)
            tipo_expr = self._get_tipo_wasm(nodo_aux.tipo)
            codigo.append(f"call $console_log_{tipo_expr}")

        elif isinstance(sentencia, Funcion):
            self._push_context()
            ctx_func = self._ctx()
            ctx_func['funcion_actual'] = sentencia
            nombre_func_wasm = f"${sentencia.nombre}"
            #Por_ref=True significa CVR (sin 'cv')
            info_params = []

            #CONTROL DE RECURSION: INICIO
            #1. Se crea variable global de guardia para esta funcion. Es una suerte de bandera, de semaforo.
            nombre_guardia = f"$bandera_de_recursion_{sentencia.nombre}"
            self._globales[nombre_guardia] = f"(global {nombre_guardia} (mut i32) (i32.const 0))"
            
            # Guardamos el nombre del guardia en el contexto para usarlo en los Returns
            ctx_func['bandera_de_recursion'] = nombre_guardia

            # 2. Se genera codigo de verificacion al inicio de la funcion
            # Si el guardia es 1, abortar (Error 3)
            ctx_func['codigo'].append(f"global.get {nombre_guardia}")
            ctx_func['codigo'].append("if")
            ctx_func['codigo'].append("    i32.const 3")
            ctx_func['codigo'].append("    call $abort")
            ctx_func['codigo'].append("end")
            
            # Marcar que estamos dentro de la funcion (Setear guardia a 1)
            ctx_func['codigo'].append("i32.const 1")
            ctx_func['codigo'].append(f"global.set {nombre_guardia}")
            #FIN CONTROL DE RECURSION

            params_str_list = []
            for p in sentencia.params:
                nombre_param_wasm = f"${p.nombre}"
                params_str_list.append(f"(param {nombre_param_wasm} {self._get_tipo_wasm(p.tipo)})")
                ctx_func['variables_usuario'][p.nombre] = nombre_param_wasm
                ctx_func['parametros'].add(nombre_param_wasm) # Registrar parametro
                
                # Si es por referencia (CVR), creamos una global para el valor de retorno
                if p.por_ref:
                    nombre_global_cvr = f"$cvr_{sentencia.nombre}_{p.nombre}"
                    tipo_wasm = self._get_tipo_wasm(p.tipo)
                    self._globales[nombre_global_cvr] = f"(global {nombre_global_cvr} (mut {tipo_wasm}) ({tipo_wasm}.const 0))"
                    info_params.append((p.nombre, True, nombre_global_cvr))
                else:
                    info_params.append((p.nombre, False, None))

            self._meta_funciones[sentencia.nombre] = info_params

            params_str = " ".join(params_str_list)
            result_str = f"(result {self._get_tipo_wasm(sentencia.retorno)})" if sentencia.retorno != Tipo.VOID else ""
            
            self._procesar_bloque(sentencia.cuerpo)
            
            # CONTROL DE RECURSION: HABILITAMOS RESET DEL GUARDIA
            # Asegurar que el guardia se resetee al salir naturalmente de la funcion (sin return explicito)
            ctx_func['codigo'].append("i32.const 0")
            ctx_func['codigo'].append(f"global.set {nombre_guardia}")

            if sentencia.retorno != Tipo.VOID:
                tipo_wasm = self._get_tipo_wasm(sentencia.retorno)
                ctx_func['codigo'].append(f"{tipo_wasm}.const 0")

            locales_func_str = "\n    ".join(sorted(list(ctx_func['locales'])))
            cuerpo_func_str = "\n    ".join(ctx_func['codigo'])
            
            self._funciones_generadas[nombre_func_wasm] = f"  (func {nombre_func_wasm} {params_str} {result_str}\n    {locales_func_str}\n    {cuerpo_func_str}\n  )"
            
            self._pop_context()

        elif isinstance(sentencia, Invocacion):
            nodo_aux = self._reducir_expresion_a_valor(sentencia)
            if nodo_aux.tipo != Tipo.VOID:
                self._generar_codigo_hoja(nodo_aux)
                codigo.append("drop")

        elif isinstance(sentencia, Return):
            if sentencia.expr:
                nodo_aux = self._reducir_expresion_a_valor(sentencia.expr)
                self._generar_codigo_hoja(nodo_aux)
            
            func_actual = ctx.get('funcion_actual')
            if func_actual and func_actual.nombre in self._meta_funciones:
                for p_nombre, es_cvr, g_nombre in self._meta_funciones[func_actual.nombre]:
                    if es_cvr:
                        codigo.append(f"local.get ${p_nombre}")
                        codigo.append(f"global.set {g_nombre}")

            codigo.append("return")
        

        elif isinstance(sentencia, Lambda):
            #Creamos un nuevo Ambito para la lambda.
            self._push_context()
            ctx_lambda = self._ctx()
            #Se declara al parametro como si fuese una variable local del ambito.
            param_nombre_py = sentencia.parametro.nombre
            nombre_param_wasm = f"${param_nombre_py}"
            ctx_lambda['variables_usuario'][param_nombre_py] = nombre_param_wasm
            # Usamos el tipo del nodo Parametro
            tipo_wasm = self._get_tipo_wasm(sentencia.parametro.tipo)
            ctx_lambda['locales'].add(f"(local {nombre_param_wasm} {tipo_wasm})")
            #El argumento se asigna al parametro
            #Se genera en el contexto padre de la lambda.
            nodo_arg_aux = self._reducir_expresion_a_valor(sentencia.argumento)
            self._generar_codigo_hoja(nodo_arg_aux)
            #La instruccion de asignacion va al codigo del contexto de la lambda.
            ctx_lambda['codigo'].append(f"local.set {nombre_param_wasm}")
            #Procesamos el cuerpo de la lambda dentro de su propio ambito.
            self._procesar_bloque(sentencia.cuerpo)
            #Finalizamos el ambito de la lambda, integrando su codigo y locales en el padre.
            ctx_finalizado = self._pop_context()
            ctx_padre = self._ctx()
            #Agregamos las declaraciones de locales de la lambda al padre.
            ctx_padre['locales'].update(ctx_finalizado['locales'])
            # Agregamos el codigo generado por la lambda al padre
            ctx_padre['codigo'].extend(ctx_finalizado['codigo'])

    def _reemplazar_invocaciones(self, nodo: Nodo) -> Nodo:
        if isinstance(nodo, Invocacion):
            # Procesar esta invocacion y convertirla en auxiliar
            return self._reducir_expresion_a_valor(nodo)

        elif isinstance(nodo, Binario):
            # Reemplazar invocaciones en ambos lados
            nodo.izq = self._reemplazar_invocaciones(nodo.izq)
            nodo.der = self._reemplazar_invocaciones(nodo.der)
            return nodo

        elif isinstance(nodo, Unario):
            nodo.expr = self._reemplazar_invocaciones(nodo.expr)
            return nodo

        elif isinstance(nodo, Trunc):
            nodo.expr = self._reemplazar_invocaciones(nodo.expr)
            return nodo

        else:
            # Hojas (Literal, Identificador, AuxiliarWasm) se devuelven sin cambios
            return nodo

    def _reducir_expresion_a_valor(self, expresion: Nodo) -> Nodo:
        # Si la expresion es un literal string, no se puede generar código para el.
        if isinstance(expresion, Literal) and getattr(expresion, "tipo", None) == Tipo.STRING:
            return expresion

        # Caso especial: Invocacion debe procesarse primero
        if isinstance(expresion, Invocacion):
            for arg in expresion.argumentos:
                nodo_arg_aux = self._reducir_expresion_a_valor(arg[0])
                self._generar_codigo_hoja(nodo_arg_aux)
            self._ctx()['codigo'].append(f"call ${expresion.nombre}")

            # Verificamos si la funcion invocada tiene parametros CVR
            if expresion.nombre in self._meta_funciones:
                info_params = self._meta_funciones[expresion.nombre]
                # Iteramos sobre los argumentos pasados
                for i, (arg_nodo, _) in enumerate(expresion.argumentos):
                    if i < len(info_params):
                        p_nombre, es_cvr, g_nombre = info_params[i]        
                        # Si el parametro es CVR y el argumento es una variable (Identificador)
                        if es_cvr and isinstance(arg_nodo, Identificador):
                            # Obtenemos el nombre de la variable en el contexto actual
                            nombre_var_wasm = self._get_nombre_variable_wasm(arg_nodo.nombre)
                            if nombre_var_wasm:
                                # Leemos de la global temporal CVR
                                self._ctx()['codigo'].append(f"global.get {g_nombre}")       
                                #Se verifica si es global o local antes de escribir
                                if nombre_var_wasm in self._globales:
                                    self._ctx()['codigo'].append(f"global.set {nombre_var_wasm}")
                                else:
                                    # Asegurar local para CVR tambien
                                    self._asegurar_local(nombre_var_wasm, arg_nodo.tipo)
                                    self._ctx()['codigo'].append(f"local.set {nombre_var_wasm}")

            if expresion.tipo != Tipo.VOID:
                tipo_wasm = self._get_tipo_wasm(expresion.tipo)
                nombre_aux = self._nueva_var_aux(tipo_wasm)
                self._ctx()['codigo'].append(f"local.set {nombre_aux}")
                return AuxiliarWasm(nombre=nombre_aux, tipo=expresion.tipo)
            else:
                return expresion

        # las invocaciones se convierten en auxiliares primero
        expresion_preparada = self._reemplazar_invocaciones(expresion)

        #se procesan las invocaciones ya convertidas a auxiliares
        nodo_reducido = self._procesar_expresion_completa(expresion_preparada)

        if not self._es_hoja(nodo_reducido): return nodo_reducido

        if not isinstance(nodo_reducido, AuxiliarWasm):
            self._generar_codigo_hoja(nodo_reducido)
            tipo_wasm = self._get_tipo_wasm(nodo_reducido.tipo)
            nombre_aux = self._nueva_var_aux(tipo_wasm)
            self._ctx()['codigo'].append(f"local.set {nombre_aux}")
            nodo_reducido = AuxiliarWasm(nombre=nombre_aux, tipo=nodo_reducido.tipo)

        return nodo_reducido
    
    def _procesar_expresion_completa(self, nodo: Nodo) -> Nodo:
        codigo = self._ctx()['codigo']
        
        #Primero manejamos casos especiales como Trunc antes del bucle principal
        if isinstance(nodo, Trunc):
            #Procesamos la expresion interna (debe ser DFLOAT)
            nodo_expr = self._procesar_expresion_completa(nodo.expr)
            
            #Generamos el codigo para evaluar la expresion interna
            self._generar_codigo_hoja(nodo_expr)
            
            #Generamos la instruccion de truncado de WASM
            #    i32.trunc_f64_u convierte f64 a i32 sin signo
            codigo.append("i32.trunc_f64_u")
            
            #Creamos una variable auxiliar para almacenar el resultado del trunc
            tipo_wasm = self._get_tipo_wasm(nodo.tipo)  # Debe ser 'i32' para UINT
            nombre_aux = self._nueva_var_aux(tipo_wasm)
            codigo.append(f"local.set {nombre_aux}")
            
            #Devolvemos el nodo auxiliar que representa el resultado
            return AuxiliarWasm(tipo=nodo.tipo, linea=nodo.linea, nombre=nombre_aux)
        
        # Bucle principal para reducir expresiones binarias
        while not self._es_hoja(nodo):
            pila = [(nodo, None)]
            sub_arbol_a_reducir, padre_del_sub_arbol = None, None

            while pila:
                actual, padre = pila.pop()
                if isinstance(actual, Binario) and self._es_hoja(actual.izq) and self._es_hoja(actual.der):
                    sub_arbol_a_reducir, padre_del_sub_arbol = actual, padre
                    break
                elif isinstance(actual, Binario):
                    if isinstance(actual.der, Nodo): pila.append((actual.der, actual))
                    if isinstance(actual.izq, Nodo): pila.append((actual.izq, actual))

            if not sub_arbol_a_reducir: break

            if isinstance(sub_arbol_a_reducir, Binario) and sub_arbol_a_reducir.op == '/':
                divisor_node = sub_arbol_a_reducir.der
                self._generar_codigo_hoja(divisor_node)
                tipo_divisor = self._get_tipo_wasm(divisor_node.tipo)
                codigo.append(f"{tipo_divisor}.const 0")
                codigo.append(f"{tipo_divisor}.eq")
                codigo.append("if")
                codigo.append("    i32.const 1")
                codigo.append("    call $abort")
                codigo.append("end")
                self._generar_codigo_hoja(sub_arbol_a_reducir.izq)
                self._generar_codigo_hoja(divisor_node)
                instruccion = self._get_op_instruccion('/', sub_arbol_a_reducir.tipo)
            
            elif isinstance(sub_arbol_a_reducir, Binario) and sub_arbol_a_reducir.op == '+' and sub_arbol_a_reducir.tipo == Tipo.UINT:
                # Generamos codigo para los operandos
                self._generar_codigo_hoja(sub_arbol_a_reducir.izq)
                self._generar_codigo_hoja(sub_arbol_a_reducir.der)
                
                # Realizamos la suma (i32.add)
                codigo.append("i32.add")
                
                # Verificacion de Overflow (> 65535)
                # Necesitamos verificar el resultado sin perderlo de la pila, ya que se debe asignar despues.
                # Usamos una variable temporal auxiliar para la verificacion.
                temp_check = self._nueva_var_aux("i32")
                
                # local.tee guarda el valor en la variable Y lo mantiene en el tope de la pila
                codigo.append(f"local.tee {temp_check}")
                
                # Obtenemos el valor guardado para compararlo
                codigo.append(f"local.get {temp_check}")
                codigo.append("i32.const 65535")
                codigo.append("i32.gt_u") # Comparamos si es mayor sin signo
                
                codigo.append("if")
                codigo.append("    i32.const 2") # Usamos codigo 2 para indicar Overflow
                codigo.append("    call $abort")
                codigo.append("end")
                
                # No asignamos instruccion aqui porque ya hicimos el 'i32.add' manualmente
                instruccion = None

            else:
                self._generar_codigo_hoja(sub_arbol_a_reducir.izq)
                self._generar_codigo_hoja(sub_arbol_a_reducir.der)
                instruccion = self._get_op_instruccion(sub_arbol_a_reducir.op, sub_arbol_a_reducir.tipo)
            
            if instruccion: codigo.append(instruccion)
            
            tipo_wasm = self._get_tipo_wasm(sub_arbol_a_reducir.tipo)
            nombre_aux = self._nueva_var_aux(tipo_wasm)
            codigo.append(f"local.set {nombre_aux}")
            nodo_aux = AuxiliarWasm(nombre=nombre_aux, tipo=sub_arbol_a_reducir.tipo)

            if padre_del_sub_arbol is None: nodo = nodo_aux
            elif padre_del_sub_arbol.izq is sub_arbol_a_reducir: padre_del_sub_arbol.izq = nodo_aux
            elif padre_del_sub_arbol.der is sub_arbol_a_reducir: padre_del_sub_arbol.der = nodo_aux
        
        return nodo

    def _es_hoja(self, nodo: Nodo) -> bool:
        return isinstance(nodo, (Literal, Identificador, AuxiliarWasm, IdCalificado))

    def _get_nombre_variable_wasm(self, nombre_py: str) -> str:
        return self._ctx()['variables_usuario'].get(nombre_py)

    def _generar_codigo_hoja(self, nodo_hoja: Nodo):
        codigo = self._ctx()['codigo']
        if isinstance(nodo_hoja, Literal):
            # Ignorar literales string: no generar codigo Wasm
            if getattr(nodo_hoja, "tipo", None) == Tipo.STRING:
                return
            tipo_wasm = self._get_tipo_wasm(nodo_hoja.tipo)
            codigo.append(f"{tipo_wasm}.const {nodo_hoja.valor}")
        elif isinstance(nodo_hoja, AuxiliarWasm):
            codigo.append(f"local.get {nodo_hoja.nombre}")
        elif isinstance(nodo_hoja, Identificador):
            nombre_var = self._get_nombre_variable_wasm(nodo_hoja.nombre)
            if nombre_var:
                if nombre_var in self._globales:
                    codigo.append(f"global.get {nombre_var}")
                else:
                    self._asegurar_local(nombre_var, nodo_hoja.tipo)
                    codigo.append(f"local.get {nombre_var}")
        elif isinstance(nodo_hoja, IdCalificado):
            #Se Permite acceso a locales (aunque sean de ámbitos padres) para evitar dejar la pila vacia.
            nombre_var = self._get_nombre_variable_wasm(nodo_hoja.atributo.nombre)
            if nombre_var:
                if nombre_var in self._globales:
                    codigo.append(f"global.get {nombre_var}")
                else:
                    # Intentamos acceder como local. 
                    # Si la variable pertenece a una funcion padre, Wasm puro
                    # fallara en validacion ("unknown local") a menos que se implementen closures,
                    # pero al menos generamos la instrucción para evitar el error de pila vacia.
                    self._asegurar_local(nombre_var, nodo_hoja.tipo)
                    codigo.append(f"local.get {nombre_var}")
            else:
                # Fallback de seguridad por si no se encuentra la variable
                print(f"Warning: Variable {nodo_hoja.atributo.nombre} no encontrada para generación.")
                tipo_wasm = self._get_tipo_wasm(nodo_hoja.tipo)
                codigo.append(f"{tipo_wasm}.const 0")
            # Si no es una global, no se genera codigo, lo que puede llevar a errores de pila vacia.
            # Esto es una limitacion de diseño: no se puede acceder a locales de otras funciones.