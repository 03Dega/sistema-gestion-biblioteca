"""
biblioteca.py
Versión actual: Sistema de gestión de biblioteca usando:
 - Árboles Binarios de Búsqueda (ABB)
 - Pila de préstamos
 - Cola de solicitudes
 - Grafo de interacciones usuario–libro

Autor: Deiger García
"""

from collections import deque
import tkinter as tk
from tkinter import messagebox, simpledialog

# ============================
# ESTRUCTURA DE GRAFO
# ============================

class Grafo:
    def __init__(self):
        self.ady = {}   # nodo -> [nodos conectados]

    def agregar_nodo(self, nodo):
        nodo = str(nodo)
        if nodo not in self.ady:
            self.ady[nodo] = []

    def agregar_arista(self, a, b):
        a, b = str(a), str(b)
        self.agregar_nodo(a)
        self.agregar_nodo(b)

        if b not in self.ady[a]:
            self.ady[a].append(b)
        if a not in self.ady[b]:
            self.ady[b].append(a)

    def vecinos(self, nodo):
        nodo = str(nodo)
        return self.ady.get(nodo, [])

    def __repr__(self):
        return f"Grafo({self.ady})"


# ============================
# ÁRBOL BINARIO (MAPA CLAVE -> VALOR)
# ============================

class NodoArbol:
    def __init__(self, clave, valor):
        self.clave = clave
        self.valor = valor
        self.izquierdo = None
        self.derecho = None

class ArbolMap:
    def __init__(self):
        self.raiz = None

    def insertar(self, clave, valor, append_if_exists=False):
        self.raiz = self._insertar_rec(self.raiz, clave, valor, append_if_exists)

    def _insertar_rec(self, nodo, clave, valor, append_if_exists):
        if nodo is None:
            return NodoArbol(clave, valor)
        if clave < nodo.clave:
            nodo.izquierdo = self._insertar_rec(nodo.izquierdo, clave, valor, append_if_exists)
        elif clave > nodo.clave:
            nodo.derecho = self._insertar_rec(nodo.derecho, clave, valor, append_if_exists)
        else:
            if append_if_exists:
                if isinstance(nodo.valor, list):
                    if isinstance(valor, list):
                        nodo.valor.extend(valor)
                    else:
                        nodo.valor.append(valor)
                else:
                    nodo.valor = valor
            else:
                nodo.valor = valor
        return nodo

    def buscar(self, clave):
        return self._buscar_rec(self.raiz, clave)

    def _buscar_rec(self, nodo, clave):
        if nodo is None:
            return None
        if clave == nodo.clave:
            return nodo.valor
        elif clave < nodo.clave:
            return self._buscar_rec(nodo.izquierdo, clave)
        else:
            return self._buscar_rec(nodo.derecho, clave)

    def inorder(self):
        resultados = []
        self._inorder_rec(self.raiz, resultados)
        return resultados

    def _inorder_rec(self, nodo, resultados):
        if not nodo:
            return
        self._inorder_rec(nodo.izquierdo, resultados)
        resultados.append((nodo.clave, nodo.valor))
        self._inorder_rec(nodo.derecho, resultados)

    def valores(self):
        return [v for _, v in self.inorder()]


# ============================
# CLASES PRINCIPALES
# ============================

class Libro:
    def __init__(self, id, titulo, autor, genero, anio):
        self.id = id
        self.titulo = titulo
        self.autor = autor
        self.genero = genero
        self.anio = anio
        self.disponible = True

    def __repr__(self):
        return f"<Libro id={self.id} titulo='{self.titulo}' autor='{self.autor}' disponible={self.disponible}>"

class PilaPrestamos(list):
    def push(self, book_id):
        self.append(book_id)

    def pop_last(self):
        if self:
            return self.pop()
        return None

    def peek_last(self):
        if self:
            return self[-1]
        return None

class Usuario:
    def __init__(self, id, nombre, correo):
        self.id = id
        self.nombre = nombre
        self.correo = correo
        self.prestamos = PilaPrestamos()

    def __repr__(self):
        return f"<Usuario id={self.id} nombre='{self.nombre}'>"


# ============================
# BIBLIOTECA PRINCIPAL
# ============================

class Biblioteca:
    def __init__(self):
        # Árboles
        self.arbol_usuarios_por_id = ArbolMap()
        self.arbol_libros_por_id = ArbolMap()

        self.arbol_libros_por_titulo = ArbolMap()
        self.arbol_libros_por_autor = ArbolMap()

        # Cola solicitudes
        self.solicitudes = deque()

        # Grafo de interacciones
        self.grafo_interacciones = Grafo()

    # ---------- REGISTRO ----------
    def registrar_usuario(self, id, nombre, correo):
        if self.arbol_usuarios_por_id.buscar(id) is not None:
            return False, f"El ID de usuario {id} ya existe."

        nuevo = Usuario(id, nombre, correo)
        self.arbol_usuarios_por_id.insertar(id, nuevo)

        # grafo
        self.grafo_interacciones.agregar_nodo(id)

        return True, f"Usuario '{nombre}' registrado."

    def registrar_libro(self, id, titulo, autor, genero, anio):
        if self.arbol_libros_por_id.buscar(id) is not None:
            return False, f"El ID {id} ya pertenece a otro libro."

        nuevo = Libro(id, titulo, autor, genero, anio)
        self.arbol_libros_por_id.insertar(id, nuevo)

        titulo_key = titulo.strip().lower()
        autor_key = autor.strip().lower()

        ext_t = self.arbol_libros_por_titulo.buscar(titulo_key)
        if ext_t is None:
            self.arbol_libros_por_titulo.insertar(titulo_key, [nuevo])
        else:
            self.arbol_libros_por_titulo.insertar(titulo_key, nuevo, append_if_exists=True)

        ext_a = self.arbol_libros_por_autor.buscar(autor_key)
        if ext_a is None:
            self.arbol_libros_por_autor.insertar(autor_key, [nuevo])
        else:
            self.arbol_libros_por_autor.insertar(autor_key, nuevo, append_if_exists=True)

        # grafo
        self.grafo_interacciones.agregar_nodo(id)

        return True, f"Libro '{titulo}' registrado."

    # ---------- PRÉSTAMO ----------
    def prestar_libro(self, id_usuario, id_libro):
        usuario = self.arbol_usuarios_por_id.buscar(id_usuario)
        if not usuario:
            return False, "Usuario no encontrado."

        libro = self.arbol_libros_por_id.buscar(id_libro)
        if not libro:
            return False, "Libro no encontrado."

        if not libro.disponible:
            self.solicitudes.append((id_usuario, id_libro))
            return False, f"Libro no disponible. Solicitud agregada."

        libro.disponible = False
        usuario.prestamos.push(id_libro)

        # grafo: conectar usuario <-> libro
        self.grafo_interacciones.agregar_arista(id_usuario, id_libro)

        return True, f"Libro '{libro.titulo}' prestado a {usuario.nombre}."

    # ---------- DEVOLUCIÓN ----------
    def devolver_libro(self, id_libro):
        libro = self.arbol_libros_por_id.buscar(id_libro)
        if not libro:
            return False, "Libro no encontrado."

        if libro.disponible:
            return False, "El libro ya está disponible."

        # identificar quién lo tiene
        usuario_encontrado = None
        for u in self.arbol_usuarios_por_id.valores():
            if u.prestamos.peek_last() == id_libro:
                usuario_encontrado = u
                break

        if not usuario_encontrado:
            for u in self.arbol_usuarios_por_id.valores():
                if id_libro in u.prestamos:
                    usuario_encontrado = u
                    break

        if not usuario_encontrado:
            return False, "No se encontró préstamo activo."

        libro.disponible = True

        if usuario_encontrado.prestamos.peek_last() == id_libro:
            usuario_encontrado.prestamos.pop_last()
        else:
            for i in range(len(usuario_encontrado.prestamos)-1, -1, -1):
                if usuario_encontrado.prestamos[i] == id_libro:
                    usuario_encontrado.prestamos.pop(i)
                    break

        # cola de solicitudes
        nueva = deque()
        asignado = False
        while self.solicitudes:
            usr, lib = self.solicitudes.popleft()
            if not asignado and lib == id_libro:
                solicitante = self.arbol_usuarios_por_id.buscar(usr)
                if solicitante:
                    libro.disponible = False
                    solicitante.prestamos.push(id_libro)

                    # grafo
                    self.grafo_interacciones.agregar_arista(usr, id_libro)

                    asignado = True
                    continue
            nueva.append((usr, lib))
        self.solicitudes = nueva

        if asignado:
            return True, f"Libro devuelto y asignado al usuario en espera."

        return True, f"Libro devuelto correctamente."

    # ---------- CONSULTAS ----------
    def buscar_usuario_por_id(self, id):
        return self.arbol_usuarios_por_id.buscar(id)

    def buscar_libro_por_id(self, id):
        return self.arbol_libros_por_id.buscar(id)

    def listar_todos_los_libros(self):
        return [v for _, v in self.arbol_libros_por_id.inorder()]

    def listar_todos_los_usuarios(self):
        return [v for _, v in self.arbol_usuarios_por_id.inorder()]

    # ---------- GRAFO ----------
    def conexiones_de(self, nodo):
        return self.grafo_interacciones.vecinos(nodo)


# ============================
# INTERFAZ GRÁFICA
# ============================

class AppBiblioteca:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Biblioteca (Árboles + Grafo)")
        self.biblioteca = Biblioteca()
        self.crear_interfaz()

    def crear_interfaz(self):
        tk.Button(self.root, text="Registrar Libro", width=30, command=self.registrar_libro).pack(pady=5)
        tk.Button(self.root, text="Registrar Usuario", width=30, command=self.registrar_usuario).pack(pady=5)
        tk.Button(self.root, text="Prestar Libro", width=30, command=self.prestar_libro).pack(pady=5)
        tk.Button(self.root, text="Devolver Libro", width=30, command=self.devolver_libro).pack(pady=5)
        tk.Button(self.root, text="Listar Libros", width=30, command=self.listar_libros).pack(pady=5)
        tk.Button(self.root, text="Listar Usuarios", width=30, command=self.listar_usuarios).pack(pady=5)
        tk.Button(self.root, text="Ver Conexiones (Grafo)", width=30, command=self.ver_conexiones).pack(pady=5)
        tk.Button(self.root, text="Salir", width=30, command=self.root.quit).pack(pady=5)

    def mostrar(self, exito, msg):
        if exito:
            messagebox.showinfo("Éxito", msg)
        else:
            messagebox.showerror("Error", msg)

    def input(self, text, es_id=False):
        v = simpledialog.askstring("Entrada", text)
        if v is None:
            return None
        if es_id:
            try:
                return int(v)
            except:
                return v.strip()
        return v.strip()

    def registrar_libro(self):
        id = self.input("ID del libro:", es_id=True)
        if id is None: return
        t = self.input("Título:")
        if t is None: return
        a = self.input("Autor:")
        if a is None: return
        g = self.input("Género:")
        if g is None: return
        y = self.input("Año:")
        if y is None: return

        ex, msg = self.biblioteca.registrar_libro(id, t, a, g, y)
        self.mostrar(ex, msg)

    def registrar_usuario(self):
        id = self.input("ID del usuario:", es_id=True)
        if id is None: return
        n = self.input("Nombre:")
        if n is None: return
        c = self.input("Correo:")
        if c is None: return

        ex, msg = self.biblioteca.registrar_usuario(id, n, c)
        self.mostrar(ex, msg)

    def prestar_libro(self):
        u = self.input("ID Usuario:", es_id=True)
        if u is None: return
        l = self.input("ID Libro:", es_id=True)
        if l is None: return

        ex, msg = self.biblioteca.prestar_libro(u, l)
        self.mostrar(ex, msg)

    def devolver_libro(self):
        l = self.input("ID Libro:", es_id=True)
        if l is None: return

        ex, msg = self.biblioteca.devolver_libro(l)
        self.mostrar(ex, msg)

    def listar_libros(self):
        libros = self.biblioteca.listar_todos_los_libros()
        if not libros:
            self.mostrar(False, "No hay libros.")
            return
        msg = "\n".join([f"{l.id} | {l.titulo} | {l.autor} | {'Disponible' if l.disponible else 'Prestado'}"
                         for l in libros])
        self.mostrar(True, msg)

    def listar_usuarios(self):
        usuarios = self.biblioteca.listar_todos_los_usuarios()
        if not usuarios:
            self.mostrar(False, "No hay usuarios.")
            return
        msg = "\n".join([f"{u.id} | {u.nombre} | Prestamos: {len(u.prestamos)}" for u in usuarios])
        self.mostrar(True, msg)

    def ver_conexiones(self):
        n = self.input("ID de usuario o libro:", es_id=True)
        if n is None: return
        con = self.biblioteca.conexiones_de(n)
        if not con:
            self.mostrar(True, f"No hay conexiones para {n}.")
        else:
            msg = f"Conexiones de {n}:\n" + ", ".join(con)
            self.mostrar(True, msg)


if __name__ == "__main__":
    root = tk.Tk()
    AppBiblioteca(root)
    root.mainloop()
