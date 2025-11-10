"""
biblioteca.py
Versión actualizada: Sistema de gestión de biblioteca usando árboles (ABB)
Autor: deiger garcia
Descripción:
 - Reemplaza la implementación basada en estructuras lineales por árboles binarios de búsqueda (ABB)
 - Árboles usados:
    * arbol_usuarios_por_id    : ABB key = usuario.id -> Usuario
    * arbol_libros_por_id      : ABB key = libro.id -> Libro
    * arbol_libros_por_titulo  : ABB key = titulo.lower() -> list de Libro (maneja títulos repetidos)
    * arbol_libros_por_autor   : ABB key = autor.lower() -> list de Libro (múltiples libros por autor)
 - Mantiene: pila de préstamos por usuario, cola de solicitudes para libros no disponibles.
 - Interfaz: Tkinter (similar al prototipo anterior).

"""

from collections import deque
import tkinter as tk
from tkinter import messagebox, simpledialog

# ---------------------------
# ESTRUCTURAS: Árbol Binario (mapa clave -> valor)
# ---------------------------

class NodoArbol:
    def __init__(self, clave, valor):
        self.clave = clave
        self.valor = valor
        self.izquierdo = None
        self.derecho = None

class ArbolMap:
    """
    Árbol binario de búsqueda simple que mapea clave -> valor.
    Si el valor debe soportar múltiples elementos (p. ej. título con varios libros),
    el 'valor' puede ser una lista y el método insertar lo agregará.
    """
    def __init__(self):
        self.raiz = None

    def insertar(self, clave, valor, append_if_exists=False):
        """
        Inserta clave->valor. Si append_if_exists True y la clave existe:
        - si el nodo.valor es lista -> se hace append,
        - si no es lista -> lo reemplaza.
        """
        clave_proc = clave
        self.raiz = self._insertar_rec(self.raiz, clave_proc, valor, append_if_exists)

    def _insertar_rec(self, nodo, clave, valor, append_if_exists):
        if nodo is None:
            # si se espera mantener varios valores por clave (valor ya puede ser lista)
            return NodoArbol(clave, valor)
        if clave < nodo.clave:
            nodo.izquierdo = self._insertar_rec(nodo.izquierdo, clave, valor, append_if_exists)
        elif clave > nodo.clave:
            nodo.derecho = self._insertar_rec(nodo.derecho, clave, valor, append_if_exists)
        else:
            # clave ya existe
            if append_if_exists:
                if isinstance(nodo.valor, list):
                    # si valor es lista, agregamos la(s) nuevas entradas
                    if isinstance(valor, list):
                        nodo.valor.extend(valor)
                    else:
                        nodo.valor.append(valor)
                else:
                    # reemplazamos si no es lista
                    nodo.valor = valor
            else:
                # reemplazo por defecto
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

    def eliminar(self, clave):
        self.raiz, eliminado = self._eliminar_rec(self.raiz, clave)
        return eliminado

    def _eliminar_rec(self, nodo, clave):
        if nodo is None:
            return nodo, None
        if clave < nodo.clave:
            nodo.izquierdo, eliminado = self._eliminar_rec(nodo.izquierdo, clave)
            return nodo, eliminado
        elif clave > nodo.clave:
            nodo.derecho, eliminado = self._eliminar_rec(nodo.derecho, clave)
            return nodo, eliminado
        else:
            # encontramos
            if nodo.izquierdo is None:
                return nodo.derecho, nodo.valor
            elif nodo.derecho is None:
                return nodo.izquierdo, nodo.valor
            else:
                # nodo con dos hijos: sustituir por sucesor (mínimo en subárbol derecho)
                sucesor = self._minimo(nodo.derecho)
                nodo.clave, nodo.valor = sucesor.clave, sucesor.valor
                nodo.derecho, _ = self._eliminar_rec(nodo.derecho, sucesor.clave)
                return nodo, sucesor.valor

    def _minimo(self, nodo):
        actual = nodo
        while actual.izquierdo is not None:
            actual = actual.izquierdo
        return actual

    def inorder(self):
        """Retorna lista de (clave, valor) en orden ascendente por clave."""
        resultados = []
        self._inorder_rec(self.raiz, resultados)
        return resultados

    def _inorder_rec(self, nodo, resultados):
        if nodo is None:
            return
        self._inorder_rec(nodo.izquierdo, resultados)
        resultados.append((nodo.clave, nodo.valor))
        self._inorder_rec(nodo.derecho, resultados)

    def valores(self):
        """Retorna lista de valores (sin claves) en orden."""
        return [v for _, v in self.inorder()]

# ---------------------------
# CLASES DEL DOMINIO (Libro, Usuario)
# ---------------------------

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
    """Pila (LIFO) para historial de préstamos de un usuario."""
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

# ---------------------------
# BIBLIOTECA (usa ArbolMap y estructuras auxiliares)
# ---------------------------

class Biblioteca:
    def __init__(self):
        # Árboles principales
        self.arbol_usuarios_por_id = ArbolMap()    # clave = id_usuario -> Usuario
        self.arbol_libros_por_id = ArbolMap()      # clave = id_libro -> Libro

        # Índices por campos textuales (clave = titulo.lower() / autor.lower() -> list[Libro])
        self.arbol_libros_por_titulo = ArbolMap()
        self.arbol_libros_por_autor = ArbolMap()

        # Cola para solicitudes cuando libro no está disponible
        self.solicitudes = deque()

    # ---------- Registro ----------
    def registrar_usuario(self, id, nombre, correo):
        if self.arbol_usuarios_por_id.buscar(id) is not None:
            return False, f"Error: El ID de usuario {id} ya está registrado."
        nuevo_usuario = Usuario(id, nombre, correo)
        self.arbol_usuarios_por_id.insertar(id, nuevo_usuario)
        return True, f"Usuario '{nombre}' registrado con éxito."

    def registrar_libro(self, id, titulo, autor, genero, anio):
        if self.arbol_libros_por_id.buscar(id) is not None:
            return False, f"Error: El ID de libro {id} ya está registrado."
        nuevo_libro = Libro(id, titulo, autor, genero, anio)
        # Insertar en árbol por id
        self.arbol_libros_por_id.insertar(id, nuevo_libro)
        # Insertar en índice por título (lista)
        clave_titulo = titulo.strip().lower()
        existente_titulo = self.arbol_libros_por_titulo.buscar(clave_titulo)
        if existente_titulo is None:
            self.arbol_libros_por_titulo.insertar(clave_titulo, [nuevo_libro])
        else:
            # append a la lista existente
            self.arbol_libros_por_titulo.insertar(clave_titulo, nuevo_libro, append_if_exists=True)

        # Insertar en índice por autor (lista)
        clave_autor = autor.strip().lower()
        existente_autor = self.arbol_libros_por_autor.buscar(clave_autor)
        if existente_autor is None:
            self.arbol_libros_por_autor.insertar(clave_autor, [nuevo_libro])
        else:
            self.arbol_libros_por_autor.insertar(clave_autor, nuevo_libro, append_if_exists=True)

        return True, f"Libro '{titulo}' registrado con éxito."

    # ---------- Búsquedas ----------
    def buscar_usuario_por_id(self, id):
        return self.arbol_usuarios_por_id.buscar(id)

    def buscar_libro_por_id(self, id):
        return self.arbol_libros_por_id.buscar(id)

    def buscar_libros_por_titulo(self, titulo_fragmento):
        """
        Busca títulos que contengan el fragmento (case-insensitive).
        Dado que el índice es por título exacto, hacemos:
         - si hay coincidencia exacta -> devolvemos lista
         - si no, hacemos recorrido inorder y filtramos por substring
        """
        clave_exacta = titulo_fragmento.strip().lower()
        exacto = self.arbol_libros_por_titulo.buscar(clave_exacta)
        resultados = []
        if exacto:
            resultados.extend(exacto if isinstance(exacto, list) else [exacto])

        # Además, filtrado por substring (parcial)
        for clave, lista_libros in self.arbol_libros_por_titulo.inorder():
            if clave_exacta in clave:
                if isinstance(lista_libros, list):
                    resultados.extend(lista_libros)
                else:
                    resultados.append(lista_libros)
        # eliminar duplicados por id
        unique = {}
        for l in resultados:
            unique[l.id] = l
        return list(unique.values())

    def buscar_libros_por_autor(self, autor_fragmento):
        clave_exacta = autor_fragmento.strip().lower()
        exacto = self.arbol_libros_por_autor.buscar(clave_exacta)
        resultados = []
        if exacto:
            resultados.extend(exacto if isinstance(exacto, list) else [exacto])
        for clave, lista_libros in self.arbol_libros_por_autor.inorder():
            if clave_exacta in clave:
                if isinstance(lista_libros, list):
                    resultados.extend(lista_libros)
                else:
                    resultados.append(lista_libros)
        unique = {}
        for l in resultados:
            unique[l.id] = l
        return list(unique.values())

    # ---------- Préstamo y devolución ----------
    def prestar_libro(self, id_usuario, id_libro):
        usuario = self.buscar_usuario_por_id(id_usuario)
        if usuario is None:
            return False, "Error: Usuario no encontrado."
        libro = self.buscar_libro_por_id(id_libro)
        if libro is None:
            return False, "Error: Libro no encontrado."
        if not libro.disponible:
            # encolar solicitud (id_usuario, id_libro)
            self.solicitudes.append((id_usuario, id_libro))
            return False, f"El libro '{libro.titulo}' no está disponible. Solicitud encolada."
        # prestar
        libro.disponible = False
        usuario.prestamos.push(id_libro)
        return True, f"Libro '{libro.titulo}' prestado a {usuario.nombre} con éxito."

    def devolver_libro(self, id_libro):
        libro = self.buscar_libro_por_id(id_libro)
        if libro is None:
            return False, "Error: Libro no encontrado."
        if libro.disponible:
            return False, f"Error: El libro '{libro.titulo}' ya está marcado como disponible."

        # Buscar usuario que tenga este libro como último préstamo (LIFO)
        usuario_encontrado = None
        for usuario in self.arbol_usuarios_por_id.valores():
            # usuarios pueden devolverse desde pila
            if usuario.prestamos.peek_last() == id_libro:
                usuario_encontrado = usuario
                break

        if usuario_encontrado is None:
            # alternativa: si nadie lo tiene como último, intentar encontrar en cualquier pila (no LIFO estricto)
            for usuario in self.arbol_usuarios_por_id.valores():
                if id_libro in usuario.prestamos:
                    usuario_encontrado = usuario
                    break

        if usuario_encontrado is None:
            # Si no se encontró usuario con préstamo, devolvemos error
            return False, "Error: No se encontró un préstamo activo para este libro."

        # realizar devolución
        libro.disponible = True
        # Si está como último, pop; sino eliminar instancia en la pila (buscar desde arriba)
        if usuario_encontrado.prestamos.peek_last() == id_libro:
            usuario_encontrado.prestamos.pop_last()
        else:
            # remover la primera aparición desde el final (comportamiento aproximado)
            for i in range(len(usuario_encontrado.prestamos)-1, -1, -1):
                if usuario_encontrado.prestamos[i] == id_libro:
                    usuario_encontrado.prestamos.pop(i)
                    break

        # Procesar solicitudes en cola: si hay peticiones para este libro, asignarlo al primer solicitante
        nueva_cola = deque()
        asignado = False
        while self.solicitudes:
            sol = self.solicitudes.popleft()
            sol_usuario_id, sol_libro_id = sol
            if not asignado and sol_libro_id == id_libro:
                # intentar asignar
                solicitante = self.buscar_usuario_por_id(sol_usuario_id)
                if solicitante:
                    # prestar al solicitante
                    libro.disponible = False
                    solicitante.prestamos.push(id_libro)
                    asignado = True
                    # notificar éxito en retorno del método (pero aquí solo procesamos la cola)
                    # Si quieres, podrías retornar info de a quién se reasignó
                    continue
                else:
                    # si usuario ya no existe, ignorar esta solicitud
                    continue
            else:
                nueva_cola.append(sol)
        self.solicitudes = nueva_cola

        if asignado:
            return True, f"Libro '{libro.titulo}' devuelto y reasignado automáticamente al primer solicitante en cola."
        return True, f"Libro '{libro.titulo}' devuelto por {usuario_encontrado.nombre} con éxito."

    # ---------- Utilitarios para mostrar datos ----------
    def listar_todos_los_libros(self):
        """Retorna lista de todos los libros (orden por id)."""
        pares = self.arbol_libros_por_id.inorder()
        return [valor for _, valor in pares]

    def listar_todos_los_usuarios(self):
        return [valor for _, valor in self.arbol_usuarios_por_id.inorder()]

# ---------------------------
# INTERFAZ GRÁFICA (Tkinter)
# ---------------------------

class AppBiblioteca:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión de Biblioteca - (Árboles)")
        self.biblioteca = Biblioteca()
        self.crear_interfaz()

    def crear_interfaz(self):
        tk.Button(self.root, text="1. Registrar Libro", width=30, command=self.registrar_libro).pack(pady=5)
        tk.Button(self.root, text="2. Registrar Usuario", width=30, command=self.registrar_usuario).pack(pady=5)
        tk.Button(self.root, text="3. Prestar Libro", width=30, command=self.prestar_libro).pack(pady=5)
        tk.Button(self.root, text="4. Devolver Libro", width=30, command=self.devolver_libro).pack(pady=5)
        tk.Button(self.root, text="5. Buscar Libro", width=30, command=self.buscar_libro).pack(pady=5)
        tk.Button(self.root, text="6. Listar Libros (por ID)", width=30, command=self.listar_libros).pack(pady=5)
        tk.Button(self.root, text="7. Listar Usuarios (por ID)", width=30, command=self.listar_usuarios).pack(pady=5)
        tk.Button(self.root, text="Salir", width=30, command=self.root.quit).pack(pady=8)

    def mostrar_mensaje(self, exito, mensaje, tipo_info="info"):
        if exito:
            messagebox.showinfo("Éxito", mensaje)
        else:
            messagebox.showerror("Error", mensaje)

    def input_seguro(self, prompt, es_id=False):
        try:
            valor = simpledialog.askstring("Entrada", prompt)
            if valor is None:
                return None
            if es_id:
                # intentamos convertir a entero si es dígito, sino dejamos tal cual (IDs flexibles)
                try:
                    return int(valor)
                except ValueError:
                    return valor.strip()
            return valor.strip()
        except Exception:
            messagebox.showerror("Error", "Entrada inválida.")
            return None

    def registrar_libro(self):
        id_libro = self.input_seguro("ID del libro:", es_id=True)
        if id_libro is None: return
        titulo = self.input_seguro("Título del libro:")
        if titulo is None: return
        autor = self.input_seguro("Autor del libro:")
        if autor is None: return
        genero = self.input_seguro("Género del libro:")
        if genero is None: return
        anio = self.input_seguro("Año de publicación:")
        if anio is None: return
        exito, msg = self.biblioteca.registrar_libro(id_libro, titulo, autor, genero, anio)
        self.mostrar_mensaje(exito, msg)

    def registrar_usuario(self):
        id_usuario = self.input_seguro("ID del usuario:", es_id=True)
        if id_usuario is None: return
        nombre = self.input_seguro("Nombre del usuario:")
        if nombre is None: return
        correo = self.input_seguro("Correo del usuario:")
        if correo is None: return
        exito, msg = self.biblioteca.registrar_usuario(id_usuario, nombre, correo)
        self.mostrar_mensaje(exito, msg)

    def prestar_libro(self):
        id_usuario = self.input_seguro("ID del usuario:", es_id=True)
        if id_usuario is None: return
        id_libro = self.input_seguro("ID del libro:", es_id=True)
        if id_libro is None: return
        exito, msg = self.biblioteca.prestar_libro(id_usuario, id_libro)
        self.mostrar_mensaje(exito, msg)

    def devolver_libro(self):
        id_libro = self.input_seguro("ID del libro a devolver:", es_id=True)
        if id_libro is None: return
        exito, msg = self.biblioteca.devolver_libro(id_libro)
        self.mostrar_mensaje(exito, msg)

    def buscar_libro(self):
        opcion = simpledialog.askstring("Búsqueda", "Buscar por (id/titulo/autor):")
        if not opcion:
            return
        opcion = opcion.strip().lower()
        if opcion == "id":
            id_libro = self.input_seguro("ID del libro:", es_id=True)
            if id_libro is None: return
            libro = self.biblioteca.buscar_libro_por_id(id_libro)
            if libro:
                msg = f"ID: {libro.id}\nTítulo: {libro.titulo}\nAutor: {libro.autor}\nGénero: {libro.genero}\nAño: {libro.anio}\nDisponible: {libro.disponible}"
                self.mostrar_mensaje(True, msg)
            else:
                self.mostrar_mensaje(False, "No se encontró el libro con ese ID.")
        elif opcion == "titulo":
            valor = simpledialog.askstring("Búsqueda", "Título o fragmento a buscar:")
            if not valor: return
            resultados = self.biblioteca.buscar_libros_por_titulo(valor)
            if not resultados:
                self.mostrar_mensaje(False, f"No se encontraron títulos que contengan '{valor}'.")
                return
            msg = "Resultados:\n"
            for l in resultados:
                msg += f"ID: {l.id} | Título: {l.titulo} | Autor: {l.autor} | Disponible: {l.disponible}\n"
            self.mostrar_mensaje(True, msg)
        elif opcion == "autor":
            valor = simpledialog.askstring("Búsqueda", "Autor o fragmento a buscar:")
            if not valor: return
            resultados = self.biblioteca.buscar_libros_por_autor(valor)
            if not resultados:
                self.mostrar_mensaje(False, f"No se encontraron libros del autor que contenga '{valor}'.")
                return
            msg = "Resultados:\n"
            for l in resultados:
                msg += f"ID: {l.id} | Título: {l.titulo} | Autor: {l.autor} | Disponible: {l.disponible}\n"
            self.mostrar_mensaje(True, msg)
        else:
            self.mostrar_mensaje(False, "Opción de búsqueda inválida. Use 'id', 'titulo' o 'autor'.")

    def listar_libros(self):
        libros = self.biblioteca.listar_todos_los_libros()
        if not libros:
            self.mostrar_mensaje(False, "No hay libros registrados.")
            return
        msg = "Libros (orden por ID):\n"
        for l in libros:
            msg += f"ID: {l.id} | Título: {l.titulo} | Autor: {l.autor} | Disponible: {l.disponible}\n"
        self.mostrar_mensaje(True, msg)

    def listar_usuarios(self):
        usuarios = self.biblioteca.listar_todos_los_usuarios()
        if not usuarios:
            self.mostrar_mensaje(False, "No hay usuarios registrados.")
            return
        msg = "Usuarios (orden por ID):\n"
        for u in usuarios:
            msg += f"ID: {u.id} | Nombre: {u.nombre} | Correo: {u.correo} | Prestamos activos: {len(u.prestamos)}\n"
        self.mostrar_mensaje(True, msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = AppBiblioteca(root)
    root.mainloop()
