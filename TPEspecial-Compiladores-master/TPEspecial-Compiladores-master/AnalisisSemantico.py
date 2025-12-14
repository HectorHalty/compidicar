from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Union
from TablaDeSimbolos import TablaDeSimbolos  

class Tipo(Enum):
    UINT = auto()
    DFLOAT = auto()
    STRING = auto()
    VOID = auto()
    BOOL = auto()
    UNKNOWN = auto()

'''
    dataclass que contiene mensaje, linea y severidad; tiene __str__ que formatea E/W/I. 
    Lo que permite esa dataclass es contener la informacion de los errores y warnings que se van
    generando durante el analisis semantico.
'''
@dataclass
class Diagnostico:  
    mensaje: str
    linea: int = 0
    severidad: str = "ERROR"
    def __str__(self) -> str:
        pref = "E" if self.severidad.upper().startswith("E") else "W" if self.severidad.upper().startswith("W") else "I"
        if self.linea:
            return f"[{pref}] L{self.linea}: {self.mensaje}"
        return f"[{pref}] {self.mensaje}"

'''
    Estas clases de datos contendran informacion para luego agregar en la tabla de simbolos.
    Simbolo: estructura minima con nombre, tipo y linea.
    SimboloVariable: simbolo para variables. (de ser necesario se puede agregar mas info)
    SimboloParametro: simbolo para parametros de funciones (agrega por_ref).
    SimboloFuncion: simbolo para funciones (agrega params, retorno y mangle). Es muy necesario guardar esta info para 
        validar llamadas a funciones.
'''
@dataclass
class Simbolo:
    nombre: str
    tipo: Tipo = Tipo.UNKNOWN
    linea: int = 0

@dataclass
class SimboloVariable(Simbolo):
    pass

@dataclass
class SimboloParametro(Simbolo):
    por_ref: bool = False           # Quedo por_ref porque fue nuesra primera decision ahora es CVR en su funcionalidad.

@dataclass
class SimboloFuncion(Simbolo):
    params: List[SimboloParametro] = field(default_factory=list) # Se usa para definir los parametros de la funcion.
    retorno: Tipo = Tipo.VOID                                    # Field asegura que cada instancia tenga su propia lista.
    mangle: str = ""

'''
    La idea de la clase ambito es implmentar el name mangling y darle un nombre unico a cada variable segun su ambito. 
'''
class Ambito:
    #Constructor con especificacion en los parametros.
    # padre: ambito padre o None si es global
    # str = "global" significa que es texto, y si no se pasa nada, vale "global".
    def __init__(self, padre: Optional['Ambito']=None, nombre: str="global"):
        self.padre = padre 
        self.simbolos: Dict[str, Simbolo] = {}  # Mapa de nombres se guarda clave nombre de la variable y valor Simbolo
        self.nombre = nombre    # Nombre del ambito sea funcion do while etc.

    '''
        Genera un path unico para el ambito, la idea es que quede como "global:funcion1:funcion2:..."
    '''
    def get_mangled_path(self) -> str:
        partes = []
        a = self
        # Mientras haya un padre. 
        while a is not None:
            partes.append(a.nombre)
            a = a.padre
        return ":" + ":".join(reversed(partes)) # Reverse lo que hace es invertir la lista.
    

    def declarar(self, sim: Simbolo, diag: List[Diagnostico]) -> bool:
        # Verificar si el nombre del simbolo existe en el diccionario/ambito actual
        # Para poder determinar si es redeclaracion o no.
        if sim.nombre in self.simbolos:
            diag.append(Diagnostico(f"Identificador redeclarado: {sim.nombre}", sim.linea))
            return False
        # Si no hay simbolo con ese nombre, lo agregamos.
        self.simbolos[sim.nombre] = sim
        return True
    
    # Metodo que resuelve el alcance lexico devuelve un simbolo si lo encuentra o none si no existe. 
    def resolver(self, nombre: str) -> Optional[Simbolo]:
        amb: Optional[Ambito] = self            #Se comienza buscando en el ambito actual y puede ser Optional porque puede no existir el simbolo.
        while amb:                              #Mientras haya un ambito (no sea None)
            if nombre in amb.simbolos:          # Si el nombre esta en los simbolos del ambito actual
                return amb.simbolos[nombre]     # Devolvemos el simbolo encontrado
            amb = amb.padre                     # Si no esta, subimos al ambito padre
        return None

# AST anotado. Cada nodo define hijos() para que el visitante recorra el arbol de forma uniforme.
@dataclass
class Nodo:
    '''
        tipo: se definira durante el analisis semantico.
        linea: linea del codigo fuente donde se encuentra el nodo.
        metodo hijos: devuelve la lista de nodos hijos para recorrer el arbol.
    '''
    tipo: Tipo = Tipo.UNKNOWN
    linea: int = 0
    def hijos(self) -> List[Nodo]:
        return []
    

@dataclass
class ErrorNodo(Nodo):
    mensaje: str = ""
    def hijos(self):
        return []

@dataclass
class Programa(Nodo):
    nombre: str = "PROGRAM"
    cuerpo: "Bloque" = None  
    def hijos(self) -> List[Nodo]:
        return [self.cuerpo] if self.cuerpo else []

@dataclass
class Bloque(Nodo): # Lista de sentencias dentro de {}.  Hay casos del parser que no devuelve un unico nodo sino un Nodo con nodos dentro como un if o funcion por ejemplo.
    sentencias: List[Nodo] = field(default_factory=list)
    def hijos(self) -> List[Nodo]:              
        # Aplanar posibles listas anidadas provenientes del parser
        planos: List[Nodo] = []                 #Lista para los nodos
        for s in self.sentencias:               # Recorremos cada sentencia 
            if isinstance(s, list):             # La sentencia puede ser una lista porque puede tener varias sentencias anidadas. 
                for inner in s:                 # Recorremos cada elemento de la lista
                    if isinstance(inner, Nodo): # Si el elemento es un nodo, lo agregamos a la lista de nodos planos
                        planos.append(inner)    
            elif isinstance(s, Nodo):           # Si la sentencia no es una lista, pero es un nodo, lo agregamos directamente
                planos.append(s)
        return planos

@dataclass
class DeclVar(Nodo):
    # Hay un unico tipo UINT 
    tipo_decl: Tipo = Tipo.UINT
    # Lista de identificadores que se declaran uint A, B, C
    # Se guarda una lista porque en una línea puedes declarar varias
    ids: List["Identificador"] = field(default_factory=list)
    def hijos(self) -> List[Nodo]:
        return list(self.ids)

@dataclass
class Identificador(Nodo):
    # El nombre del identificador 
    nombre: str = ""
    def __repr__(self) -> str:
        return f"ID({self.nombre})"

@dataclass
class IdCalificado(Nodo):
    base: Identificador = None  
    atributo: Identificador = None          # Para los prefijados AA.BB
    def hijos(self) -> List[Nodo]:
        return [self.base, self.atributo]   

@dataclass
class Literal(Nodo):
    '''
        Representa las hojas del arbol, guarda el valor del literal.
    '''
    valor: Any = None
# HABLAR CON RAMON CASO TRUNC.TXT y lambda.txt analizar el signo negativo en literales.
@dataclass
class Unario(Nodo):
    op: str = "-"                                   # Un solo operando por ejemplo -5
    expr: Nodo = None                               
    def hijos(self) -> List[Nodo]:                  # Devuelve la lista de hijos del nodo unario.
        return [self.expr] if self.expr else []     # Retorna una lista con el nodo de la expresion por ejemplo Literal 5. Sino expr devuelve lista vacia.
@dataclass
class Binario(Nodo):
    op: str = ""
    izq: Nodo = None  
    der: Nodo = None
    def hijos(self) -> List[Nodo]:
        return [self.izq, self.der]

@dataclass
class Asignacion(Nodo):
    destino: Union[Identificador, IdCalificado, None] = None # 
    expr: Nodo = None  
    def hijos(self) -> List[Nodo]:
        lista: List[Nodo] = []
        if isinstance(self.destino, Nodo):  # Asegurarse de que destino es un Nodo
            lista.append(self.destino)      # Agregar destino a la lista de hijos
        if self.expr:                       # Verificar que expr no sea None
            lista.append(self.expr)         # Agregar expr a la lista de hijos
        return lista

@dataclass
class MultiAsignacion(Nodo):
    destinos: List[Identificador] = field(default_factory=list)
    expresiones: List[Nodo] = field(default_factory=list)
    def hijos(self) -> List[Nodo]:
        return [*self.destinos, *self.expresiones]
    '''
        Aca tuvimos que usar * para poder devolver una lista unica con destinos y expresiones.
        Esto es necesario porque en Python, al usar listas, no podemos simplemente concatenar dos listas
        de forma directa en el retorno, ya que eso devolveria una lista de listas. Al usar * descomponemos
        las listas en sus elementos individuales.
    '''

@dataclass
class Si(Nodo):
    condicion: Nodo = None          
    entonces: Bloque = None  
    sino: Optional[Bloque] = None   
    def hijos(self) -> List[Nodo]:
        lista = [self.condicion, self.entonces]
        if self.sino:
            lista.append(self.sino)
        return lista

@dataclass
class DoWhile(Nodo):
    cuerpo: Bloque = None  
    condicion: Nodo = None  
    def hijos(self) -> List[Nodo]:
        return [self.cuerpo, self.condicion]

@dataclass
class Print(Nodo):
    expr: Nodo = None 
    def hijos(self) -> List[Nodo]:
        return [self.expr] if self.expr else [] #Si hay una expresion la devolvemos en lista

@dataclass
class Return(Nodo):
    expr: Optional[Nodo] = None
    def hijos(self) -> List[Nodo]:
        return [self.expr] if self.expr else [] #Si hay una expresion la devolvemos en lista

@dataclass
class Parametro(Nodo):
    nombre: str = ""            # Nombre del parametro
    por_ref: bool = False       # Indica si es por CVR o CV
    tipo: Tipo = Tipo.UNKNOWN   # Tipo del parametro

@dataclass
class Invocacion(Nodo):
    nombre: str = ""
    argumentos: List[Tuple[Nodo, Optional[str]]] = field(default_factory=list)  # Lista de tuplas (expresion, nombre_formal)
    def hijos(self) -> List[Nodo]:
        return [e for (e, _) in self.argumentos]    # Devolvemos solo las expresiones, con el _ ignoramos el nombre formal. Mas tarde se validaran los nombres formales.
                                                    # por ahora devolvemos una lista con expresiones.

@dataclass
class Funcion(Nodo):
    nombre: str = ""
    params: List[Parametro] = field(default_factory=list)
    cuerpo: Bloque = None  
    retorno: Tipo = Tipo.UINT
    def hijos(self) -> List[Nodo]:
        '''
            Hay que devolver parametros y luego el cuerpo. Pero los parametros estan en una lista que
            tenemos que desempaquetar para devolverlos uno por uno y luego agregar el cuerpo.
            El if dice que si el cuerpo existe lo agregamos al final, sino devolvemos solo los parametros.
        '''
        return [*self.params, self.cuerpo] if self.cuerpo else list(self.params)

@dataclass
class Lambda(Nodo):
    parametro: Parametro = field(default_factory=Parametro)
    cuerpo: Nodo = None 
    argumento: Nodo = None  
    def hijos(self):
        return [self.parametro, self.cuerpo, self.argumento]

@dataclass
class Trunc(Nodo):
    expr: Nodo = None  
    def hijos(self) -> List[Nodo]:
        return [self.expr] if self.expr else []

@dataclass
class AuxiliarWasm(Nodo):
    """
    Nodo para representar una variable auxiliar de Wasm que contiene un resultado intermedio.
    Este nodo reemplaza a un subárbol ya procesado por el generador de código.
    """
    nombre: str = "" # El nombre de la variable en Wasm, ej:$t0
    def __repr__(self) -> str:
        return f"AuxWasm({self.nombre})"
    def hijos(self) -> List[Nodo]:
        return []

@dataclass
class ArbolSemantico: #contiene imprimir_arbol() para impresión legible y to_dot() para exportar a Graphviz/DOT
    '''
       Utilizamos Optional para permitir que el arbol semantico pueda estar vacio
       y no devuelva error. 
       diag es la lista de diagnosticos que luego mostraremos por pantallas todos juntos dependiendo el tipo de severidad. 
    '''
    raiz: Optional[Nodo]
    diag: List[Diagnostico]

    '''
        Metodo para imprimir el arbol por consola.
    '''
    def imprimir_arbol(self) -> str:
        if not self.raiz:
            return "(árbol vacío)"
        lineas: List[str] = []

        def rec(n: Any, pref: str = ""):
            if n is None:
                return
            if isinstance(n, list):
                for elem in n:
                    rec(elem, pref)
                return
            if not isinstance(n, Nodo):
                lineas.append(f"{pref}{n!r}")
                return
            info = f"{pref}{n.__class__.__name__}"
            if hasattr(n, "tipo") and isinstance(n.tipo, Tipo):
                info += f" : {n.tipo.name}"
            lineas.append(info)
            for h in n.hijos():
                rec(h, pref + "  ")

        rec(self.raiz)
        return "\n".join(lineas)
    
    '''
        Este metodo le cambia el formato al arbol y lo pasa a formato DOT para ver el arbol en la pagina web mencionada en el informe.
    '''
    def to_dot(self) -> str:
        if not self.raiz:
            return "digraph G {}"
        lines = ["digraph G {", '  node [shape=box, fontname="Courier"];']
        idx = 0
        idmap: Dict[int, str] = {}
        def nid(n: Nodo) -> str:
            nonlocal idx
            key = id(n)
            if key not in idmap:
                idx += 1
                idmap[key] = f"n{idx}"
            return idmap[key]
        def label(n: Nodo) -> str:
            base = n.__class__.__name__
            if isinstance(n, Identificador):
                base += f"\\n{n.nombre}"
            if isinstance(n, Literal):
                base += f"\\n{n.valor}"
            if isinstance(n, Binario):
                base += f"\\n{n.op}"
            if isinstance(n, Unario):
                base += f"\\n{n.op}"
            if isinstance(n, Invocacion):
                base += f"\\n{n.nombre}"
            if hasattr(n, "tipo") and isinstance(n.tipo, Tipo):
                base += f"\\n:{n.tipo.name}"
            return base
        def rec(n: Any):
            if n is None:
                return
            if isinstance(n, list):
                for e in n:
                    rec(e)
                return
            if not isinstance(n, Nodo):
                return
            lines.append(f'  {nid(n)} [label="{label(n)}"];')
            for h in n.hijos():
                if h is None:
                    continue
                if isinstance(h, list):
                    for sub in h:
                        if isinstance(sub, Nodo):
                            lines.append(f"  {nid(n)} -> {nid(sub)};")
                            rec(sub)
                    continue
                lines.append(f"  {nid(n)} -> {nid(h)};")
                rec(h)
        rec(self.raiz)
        lines.append("}")
        return "\n".join(lines)

class ReglasTipos:  
    #Centraliza la logica de tipos.
    # Conjuntos de tipos
    num = {Tipo.UINT, Tipo.DFLOAT}

    #Metodo estatico porque no depende de ninguna instancia de la clase.
    @staticmethod
    def binario(op: str, t1: Tipo, t2: Tipo) -> Tipo:
        # Define el tipo resultante de una operacion binaria entre t1 y t2 con el operador op.
        if op in {"+", "-", "*", "/"}:                                          #Reglas para operaciones aritmeticas                   
            if t1 in ReglasTipos.num and t2 in ReglasTipos.num:                 #Ambos son numeros
                return Tipo.DFLOAT if Tipo.DFLOAT in (t1, t2) else Tipo.UINT
            return Tipo.UNKNOWN                                                 #Si no son numero error.
        if op in {"==", "!=", "<", "<=", ">", ">="}:                            #Reglas para operaciones.
            if t1 in ReglasTipos.num and t2 in ReglasTipos.num:
                return Tipo.BOOL
            return Tipo.UNKNOWN
        return Tipo.UNKNOWN
    @staticmethod
    def compatible_asignacion(dest: Tipo, src: Tipo) -> bool:                   #Reglas para compatibilidad de asignacion
        if dest == src:                                                         #Verifica si se puede asignar src a dest
            return True
        if dest == Tipo.DFLOAT and src == Tipo.UINT:
            return True
        return False
    @staticmethod
    def es_numerico(t: Tipo) -> bool:                 #Verifica si el tipo es numerico
        return t in {Tipo.UINT, Tipo.DFLOAT}

class Mangler:
    _map_t: Dict[Tipo, str] = {
        Tipo.UINT: "U",
        Tipo.DFLOAT: "D",
        Tipo.STRING: "S",
        Tipo.VOID: "Vd",
        Tipo.BOOL: "B",
        Tipo.UNKNOWN: "X",
    }
    @staticmethod
    def mangle_func(nombre: str, params: List[Parametro], ret: Tipo) -> str:    
        #Genera un identificador con información de modos (por referencia o por valor) y tipos.
        # Generamos el codigo de los parametros (V=Valor, R=Referencia).
        modos = "".join(("R" if p.por_ref else "V") + Mangler._map_t.get(p.tipo, "X") for p in params)  
        # Retornamos: Nombre__Parametros__Retorno
        return f"{nombre}__{modos}__{Mangler._map_t.get(ret,'X')}"

class AnalisisSemantico:    
    #mantiene diag y tabla y expone analizar_entrada que convierte la salida del parser a AST y analizar que visita la raíz.
    def __init__(self, tabla: Optional[TablaDeSimbolos] = None) -> None:
        self.diag: List[Diagnostico] = []
        self.tabla = tabla or TablaDeSimbolos()

    # Punto de entrada “general” recibe Nodo del Parser
    def analizar_entrada(self, salida_parser: Any) -> ArbolSemantico:
        if not isinstance(salida_parser, Nodo):
            self.diag.append(Diagnostico("Salida del parser no es un AST válido.", 0, "ERROR"))
            return ArbolSemantico(None, self.diag)
        return self.analizar(salida_parser) # Inicia el recorrido recursivo.
    
    # Metodo publico que llama el main. Recibe lo que salio del parser.
    def analizar(self, raiz: Nodo) -> ArbolSemantico:
        amb = Ambito()                  # Ámbito global inicial     
        self._visitar(raiz, amb)        # Retornamos el arbol semantico con la raiz y los diagnosticos.
        return ArbolSemantico(raiz, self.diag)  

    # Metodo recursivo que visita nodos del AST.
    def _visitar(self, n: Any, amb: Ambito) -> Tipo:   

        # Caso base: si el nodo es None (ej: un else que no existe), devolvemos UNKNOWN.
        if n is None:
            return Tipo.UNKNOWN
        
        # Si es una lista de nodos (ej sentencias en un bloque) visitamos cada uno.
        if isinstance(n, list):
            ultimo = Tipo.VOID
            for elem in n:
                ultimo = self._visitar(elem, amb)
            return ultimo
        
        # Si no es un nodo, no sabemos que hacer.
        if not isinstance(n, Nodo):
            return Tipo.UNKNOWN
        
        '''
            En vez de hacer un if else para cada tipo de nodo, usamos una tecnica llamada reflexion
            el codigo getattr busca si existe un metodo llamado _v_NombreDeLaClase y si existe lo llama.
        '''
        metodo = getattr(self, f"_v_{n.__class__.__name__}", None) # getattr le pregunta a la clase analisis semantico si tiene un metodo llamado _v_NombreDeLaClase
        if metodo:                # Si existe el metodo, lo llamamos    
            n.tipo = metodo(n, amb) # Anotamos el tipo devuelto por el metodo en el nodo
        else:                       # Si no existe el metodo, visitamos recursivamente los hijos
            for h in n.hijos():
                self._visitar(h, amb)
            n.tipo = getattr(n, "tipo", Tipo.UNKNOWN)
        return n.tipo

    def _v_Bloque(self, n: Bloque, amb: Ambito) -> Tipo:
        for s in n.hijos():  # ya aplanado
            self._visitar(s, amb)
        return Tipo.VOID

    def _v_Programa(self, n: Programa, amb: Ambito) -> Tipo:
        #Al ambito raiz le ponemos el nombre del programa
        amb.nombre = n.nombre
        if self.tabla:
            if n.nombre not in self.tabla.simbolos:
                self.tabla.agregar(n.nombre, "Identificador", linea=n.linea)
            self.tabla.asignar_uso(n.nombre, "nombre de programa")
            self.tabla.asignar_tipo(n.nombre, "Identificador")
        if n.cuerpo:
            #usamos el mismo ambito global para el cuerpo
            self._visitar(n.cuerpo, amb)
        return Tipo.VOID

    
    def _v_ErrorNodo(self, n: ErrorNodo, amb: Ambito) -> Tipo:
        self.diag.append(Diagnostico(f"Nodo error: {n.mensaje}", getattr(n, 'linea', 0)))
        n.tipo = Tipo.UNKNOWN
        return n.tipo

    def _v_Lambda(self, n: Lambda, amb: Ambito) -> Tipo:
        # Nuevo ambito para cuerpo
        amb_l = Ambito(amb)
        amb_l.declarar(SimboloVariable(nombre=n.parametro.nombre, tipo=n.parametro.tipo), self.diag)
        self._visitar(n.cuerpo, amb_l)
        self._visitar(n.argumento, amb_l)
        n.tipo = Tipo.VOID
        return n.tipo


    def _v_DeclVar(self, n: DeclVar, amb: Ambito) -> Tipo:
        for ident in n.ids:
            sim = SimboloVariable(nombre=ident.nombre, tipo=n.tipo_decl, linea=ident.linea)
            if amb.declarar(sim, self.diag):
                ident.tipo = n.tipo_decl  # anotar tipo en el nodo
                if self.tabla:
                    mangled = f"{ident.nombre}{amb.get_mangled_path()}" # para decir por ejemplo "var":PROG
                    #Si el lexico ya agrega variable, la migramos y evitamos duplicado
                    if not self.tabla.renombrar(ident.nombre, mangled):
                        self.tabla.agregar(mangled, n.tipo_decl, linea=ident.linea)
                    self.tabla.asignar_tipo(mangled, n.tipo_decl)
                    self.tabla.asignar_uso(mangled, "nombre de variable")
        return Tipo.VOID


    def _v_Identificador(self, n: Identificador, amb: Ambito) -> Tipo:
        #Con el metodo resolver agarramos el "ambito" donde esta declarado 
        # el identificador ya que resolver es una funcion de la clase Ambito que devuelve "amb.simbolos[nombre]" 
        # buscando hacia arriba en la cadena de ambitos padres.
        sim = amb.resolver(n.nombre)
        if sim:
            return sim.tipo
        self.diag.append(Diagnostico(f"Uso de identificador no declarado: '{n.nombre}'", n.linea))
        return Tipo.UNKNOWN


    def _v_IdCalificado(self, n: IdCalificado, amb: Ambito) -> Tipo:
        # Resolver la base (ej AA) para anotar su tipo en el AST.
        # Importante para no encontrar un atributo en un base que no existe.
        sim_base = amb.resolver(n.base.nombre)
        if sim_base:
            n.base.tipo = sim_base.tipo
        
        #Buscamos un ambito visible cuyo nombre sea el prefijo (actual o ancestro)
        amb_base: Optional[Ambito] = amb
        while amb_base and amb_base.nombre != n.base.nombre:
            amb_base = amb_base.padre

        if not amb_base:
            # El prefijo no es visible (no está en la cadena de ancestros)
            self.diag.append(Diagnostico(
                f"Ámbito prefijado '{n.base.nombre}' no es visible desde el ambito actual o no existe.",
                n.linea
            ))
            return Tipo.UNKNOWN
            
        # Buscamos SOLO en ese ambito que encontramos.
        sim = amb_base.simbolos.get(n.atributo.nombre) #agarramos el "atributo" del IdCalificado
        if not sim:
            self.diag.append(Diagnostico(
                f"Identificador '{n.atributo.nombre}' no declarado en el ambito '{n.base.nombre}'.",
                n.linea
            ))
            return Tipo.UNKNOWN
        n.atributo.tipo = sim.tipo
        return sim.tipo #retornamos el tipo de la variable encontrada.
        

    def _v_Literal(self, n: Literal, amb: Ambito) -> Tipo:
        if isinstance(n.valor, int):
            return Tipo.UINT
        if isinstance(n.valor, float):
            return Tipo.DFLOAT
        if isinstance(n.valor, str):
            return Tipo.STRING
        return Tipo.UNKNOWN


    def _v_Unario(self, n: Unario, amb: Ambito) -> Tipo:
        t = self._visitar(n.expr, amb)
        if n.op == "-" and t in {Tipo.UINT, Tipo.DFLOAT}:
            return t
        return Tipo.UNKNOWN


    def _v_Binario(self, n: Binario, amb: Ambito) -> Tipo:
        t1 = self._visitar(n.izq, amb)
        t2 = self._visitar(n.der, amb)
        return ReglasTipos.binario(n.op, t1, t2)


    def _v_Asignacion(self, n: Asignacion, amb: Ambito) -> Tipo:
        # Visitar y anotar el tipo del destino y la expresion 
        t_dest = self._visitar(n.destino, amb)
        t_expr = self._visitar(n.expr, amb)

        if t_dest == Tipo.UNKNOWN:
            # El error ya fue reportado por _v_Identificador
            return Tipo.UNKNOWN

        if not ReglasTipos.compatible_asignacion(t_dest, t_expr):
            self.diag.append(Diagnostico(f"No se puede asignar tipo {t_expr.name} a {t_dest.name}", n.linea))
            return Tipo.UNKNOWN

        return t_dest

    def _v_Print(self, n: Print, amb: Ambito) -> Tipo:
        self._visitar(n.expr, amb)
        return Tipo.VOID

    def _v_Funcion(self, n: Funcion, amb: Ambito) -> Tipo:
        #Declaramos la funcion en el ambito actual
        params_sim = [SimboloParametro(nombre=p.nombre, tipo=p.tipo, por_ref=p.por_ref) for p in n.params]
        mangled_fun = f"{n.nombre}{amb.get_mangled_path()}" 
        sim_func = SimboloFuncion(nombre=n.nombre, tipo=n.retorno, linea=n.linea, params=params_sim, mangle=mangled_fun)
        if not amb.declarar(sim_func, self.diag):
            return Tipo.UNKNOWN # Error de redeclaracion

        # Aca actualizamos la tabla de simbolos 
        if self.tabla:
            if not self.tabla.renombrar(n.nombre, mangled_fun):
                self.tabla.agregar(mangled_fun, n.retorno, linea=n.linea)
            self.tabla.asignar_tipo(mangled_fun, n.retorno)
            self.tabla.asignar_uso(mangled_fun, "nombre de funcion")

        #Creamos ambito para la funcion y asi poder declarar parametros
        amb_func = Ambito(amb, nombre=n.nombre)
        for p, sim_p in zip(n.params, params_sim):
            if amb_func.declarar(sim_p, self.diag):
                p.tipo = sim_p.tipo # Anotar nodo del parametro
                if self.tabla:  #Para poner el tipo del parametro en la tabla de simbolos principal
                    mangled_par = f"{p.nombre}{amb_func.get_mangled_path()}"  
                    if not self.tabla.renombrar(p.nombre, mangled_par):
                        self.tabla.agregar(mangled_par, p.tipo, linea=n.linea)
                    self.tabla.asignar_tipo(mangled_par, p.tipo)
                    uso = "parametro-cvr" if p.por_ref else "parametro-cv"
                    self.tabla.asignar_uso(mangled_par, uso)

        #Visitamos cuerpo de la función
        self._visitar(n.cuerpo, amb_func)
        return n.retorno



    def _v_Parametro(self, n: Parametro, amb: Ambito) -> Tipo:
        # Los parametros ya se declaran en _v_Funcion
        return n.tipo


    def _v_Return(self, n: Return, amb: Ambito) -> Tipo:
        if n.expr:
            return self._visitar(n.expr, amb)
        return Tipo.VOID
    
    
    def _v_Invocacion(self, n: Invocacion, amb: Ambito) -> Tipo:
        #Verificamos si la funcion existe en el ambito
        sim = amb.resolver(n.nombre)
        if not sim:
            self.diag.append(Diagnostico(f"Invocación a función no declarada: {n.nombre}", n.linea))
            # Validar los argumentos para detectar errores anidados
            for arg, _formal in n.argumentos:
                self._visitar(arg, amb)
            return Tipo.UNKNOWN
        # Vemos si el simbolo sea efectivamente una funcion
        if not isinstance(sim, SimboloFuncion):
            self.diag.append(Diagnostico(f"'{n.nombre}' no es una funcion", n.linea))
            for arg, _formal in n.argumentos:
                self._visitar(arg, amb)
            return Tipo.UNKNOWN
        sim_func: SimboloFuncion = sim  

        #Se reordenan los argumentos formales si se pasan en desorden
        argumentos_reordenados = self._reordenar_argumentos(n.argumentos, sim_func.params, n.linea)
        if argumentos_reordenados is not None:
            n.argumentos = argumentos_reordenados

        # Validamos cantidad de argumentos
        if len(n.argumentos) != len(sim_func.params):
            self.diag.append(Diagnostico(
                f"Invocacion a '{n.nombre}': se esperaban {len(sim_func.params)} argumentos, se recibieron {len(n.argumentos)}",
                n.linea
            ))
        # Validamos tipos de los argumentos y reglas CVR
        for i, (arg_expr, formal_nombre) in enumerate(n.argumentos):
            tipo_arg = self._visitar(arg_expr, amb)
            
            if i < len(sim_func.params):
                param_esperado = sim_func.params[i]
                #Validacion en CVR: Si es por referencia, el argumento DEBE ser una variable 
                if param_esperado.por_ref and not isinstance(arg_expr, (Identificador, IdCalificado)):
                    self.diag.append(Diagnostico(
                        f"El parametro '{param_esperado.nombre}' es de tipo CVR (entrada/salida) y requiere una variable, no una constante o expresion.",
                        n.linea,
                        "ERROR"
                    ))
                #Verificamos compatibilidad de tipos
                if not ReglasTipos.compatible_asignacion(param_esperado.tipo, tipo_arg):
                    msg = f"Argumento {i+1} de '{n.nombre}': tipo incompatible. "
                    msg += f"Se esperaba {param_esperado.tipo.name}, se recibio {tipo_arg.name}"
                    if param_esperado.tipo == Tipo.UINT and tipo_arg == Tipo.DFLOAT:
                        msg += " (use trunc(expr))"
                    self.diag.append(Diagnostico(msg, n.linea))
        # Retornamos el tipo de retorno de la función
        return sim_func.tipo

    def _reordenar_argumentos(self, argumentos: List, params: List, linea: int) -> Optional[List]:
        # Si ningun argumento tiene nombre formal, no se reordena nada
        if not any(nombre for _, nombre in argumentos):
            return None
        
        #Se crea un mapa donde nombre_param -> indice
        idx_por_nombre = {p.nombre: i for i, p in enumerate(params)}
        
        #Reordenamos los argumentos segun los nombres formales
        resultado = [None] * len(params)
        for arg, nombre_formal in argumentos:
            if nombre_formal not in idx_por_nombre:
                self.diag.append(Diagnostico(f"Parametro '{nombre_formal}' no existe", linea))
                return None
            idx = idx_por_nombre[nombre_formal]
            if resultado[idx] is not None:
                self.diag.append(Diagnostico(f"Parametro '{nombre_formal}' duplicado", linea))
                return None
            resultado[idx] = (arg, nombre_formal)
        
        #Se verifica que no falten argumentos
        for i, r in enumerate(resultado):
            if r is None:
                self.diag.append(Diagnostico(f"Falta argumento para '{params[i].nombre}'", linea))
                return None
        
        return resultado

    def _v_Trunc(self, n: Trunc, amb: Ambito) -> Tipo:
        t = self._visitar(n.expr, amb)
        if not ReglasTipos.es_numerico(t):
            self.diag.append(Diagnostico("trunc() requiere expresion numerica.", n.linea))
        return Tipo.UINT
    

    def _v_MultiAsignacion(self, n: MultiAsignacion, amb: Ambito) -> Tipo:
        tipos_dest = [self._visitar(dest, amb) for dest in n.destinos]
        tipos_expr = [self._visitar(expr, amb) for expr in n.expresiones]
        num_dest = len(tipos_dest)
        num_expr = len(tipos_expr)
        if num_dest < num_expr:
            sobrantes = num_expr - num_dest
            self.diag.append(Diagnostico(
                f"Asignacion multiple: se descartan {sobrantes} expresiones sobrantes.",
                n.linea,
                "WARNING"
            ))
            tipos_expr = tipos_expr[:num_dest]
        for i, (t_dest, t_expr) in enumerate(zip(tipos_dest, tipos_expr)):
            if not ReglasTipos.compatible_asignacion(t_dest, t_expr):
                self.diag.append(Diagnostico(
                    f"Asignacion multiple, posicion {i+1}: no se puede asignar tipo {t_expr.name} a {t_dest.name}.",
                    n.linea
                ))
        return Tipo.VOID



        
# Metodos para literales
def lit_uint(valor: int, linea: int = 0) -> Literal:
    return Literal(valor=int(valor), tipo=Tipo.UINT, linea=linea)

def lit_dfloat(valor: float, linea: int = 0) -> Literal:
    return Literal(valor=float(valor), tipo=Tipo.DFLOAT, linea=linea)

def lit_string(valor: str, linea: int = 0) -> Literal:
    return Literal(valor=str(valor), tipo=Tipo.STRING, linea=linea)