from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

# Importa los tipos y nodos del semántico (ya están en tu repo)
from AnalisisSemantico import (
    Tipo,
    ArbolSemantico,
    Nodo,
    Programa,
    Bloque,
    DeclVar,
    Identificador,
    IdCalificado,
    Literal,
    Unario,
    Binario,
    Asignacion,
    MultiAsignacion,
    Print,
    Return,
    Parametro,
    Invocacion,
    Funcion,
    Trunc,
)

# Utilidades de construcción de WAT
class _WBuilder:
    def __init__(self):
        self.lines: List[str] = []
        self.ind = 0
    def w(self, s: str = ""):
        self.lines.append("  " * self.ind + s)
    def enter(self):
        self.ind += 1
    def exit(self):
        self.ind = max(0, self.ind - 1)
    def text(self) -> str:
        return "\n".join(self.lines)

def wasm_ty(t: Tipo) -> str:
    if t == Tipo.UINT or t == Tipo.BOOL:
        return "i32"
    if t == Tipo.DFLOAT:
        return "f64"
    # Para STRING/VOID/UNKNOWN no generamos código en este mínimo
    return "i32"

@dataclass
class _FuncCtx:
    name: str
    ret: Tipo
    locals_i32: List[str] = field(default_factory=list)
    locals_f64: List[str] = field(default_factory=list)
    ret_local: Optional[str] = None

    def fresh_i32(self, base="t") -> str:
        idx = len(self.locals_i32)
        name = f"${base}{idx}"
        self.locals_i32.append(name)
        return name

    def fresh_f64(self, base="d") -> str:
        idx = len(self.locals_f64)
        name = f"${base}{idx}"
        self.locals_f64.append(name)
        return name

class WasmCodegen:
    """
    Generador mínimo WAT con:
      - + overflow i32
      - / división por cero i32/f64
      - guardia de recursión por función
    """
    def __init__(self, arbol: ArbolSemantico):
        self.arbol = arbol
        self.w = _WBuilder()
        self.globals: Dict[str, Tipo] = {}     # nombre -> tipo
        self.funcs: List[Funcion] = []
        self.func_rec_flag: Dict[str, str] = {}  # nombre -> nombre de global rec

    # Recolecta globals y funciones del programa (solo nivel superior)
    def _collect(self, prog: Programa):
        if not isinstance(prog.cuerpo, Bloque):
            return
        for s in prog.cuerpo.sentencias:
            if isinstance(s, DeclVar):
                for ident in s.ids:
                    # Asumimos variables globales (mínimo indispensable)
                    if ident.nombre not in self.globals:
                        self.globals[ident.nombre] = s.tipo_decl
            elif isinstance(s, Funcion):
                self.funcs.append(s)

    # Emite cabecera e imports
    def _emit_preamble(self, prog_name: str):
        self.w.w("(module")
        self.w.enter()
        # Imports mínimos
        self.w.w('(import "env" "abort" (func $abort (param i32)))')
        self.w.w('(import "env" "print_u" (func $print_u (param i32)))')
        self.w.w('(import "env" "print_d" (func $print_d (param f64)))')
        self.w.w()

        # Globals de variables
        for name, t in self.globals.items():
            wt = wasm_ty(t)
            init = "i32.const 0" if wt == "i32" else "f64.const 0"
            self.w.w(f"(global ${name} (mut {wt}) ({init}))")

        # Globals para banderas de recursión
        for f in self.funcs:
            flag = f"$rec_{f.nombre}"
            self.func_rec_flag[f.nombre] = flag
            self.w.w(f"(global {flag} (mut i32) (i32.const 0))")
        self.w.w()

    def emit_module(self) -> str:
        if not isinstance(self.arbol.raiz, Programa):
            return "(module)"
        prog: Programa = self.arbol.raiz
        self._collect(prog)
        self._emit_preamble(prog.nombre)
        # Emite todas las funciones
        for f in self.funcs:
            self._gen_function(f)
        # Export opcional de variables/funciones básicas
        for name in self.globals.keys():
            self.w.w(f'(export "{name}" (global ${name}))')
        for f in self.funcs:
            self.w.w(f'(export "{f.nombre}" (func ${f.nombre}))')
        self.w.exit()
        self.w.w(")")
        return self.w.text()
