from collections import deque
import tkinter as tk
from tkinter import messagebox, simpledialog

class Nodo:
    """Nodo para la Lista Enlazada de usuarios."""
    def __init__(self, data):
        self.data = data
        self.next = None

class ListaEnlazada:
    """Lista Enlazada para gestionar usuarios dinámicamente."""
    def __init__(self):
        self.head = None

    def append(self, data):
        """Inserta un nuevo usuario al final de la lista."""
        new_node = Nodo(data)
        if not self.head:
            self.head = new_node
            return
        last = self.head
        while last.next:
            last = last.next
        last.next = new_node

    def find_by_id(self, user_id):
        """Busca un usuario por ID (O(n))."""
        current = self.head
        while current:
            if current.data["id"] == user_id:
                return current.data
            current = current.next
        return None

    def remove_by_id(self, user_id):
        """Elimina un usuario por ID (no usado en este prototipo, pero útil)."""
        if not self.head:
            return
        if self.head.data["id"] == user_id:
            self.head = self.head.next
            return
        current = self.head
        while current.next:
            if current.next.data["id"] == user_id:
                current.next = current.next.next
                return
            current = current.next

class ArrayLibros(list):
    """Arreglo (lista dinámica) para libros con acceso rápido."""
    def find_by_id(self, book_id):
        """Busca un libro por ID (O(n))."""
        for libro in self:
            if libro.id == book_id:
                return libro
        return None

    def search_by_criteria(self, criterio, valor):
        """Busca libros por título o autor."""
        resultados = [libro for libro in self if valor.lower() in libro.__dict__[criterio].lower()]
        return resultados

class PilaPrestamos(list):
    """Pila (LIFO) para historial de préstamos de un usuario."""
    def push(self, book_id):
        """Agrega un préstamo (append)."""
        self.append(book_id)

    def pop_last(self):
        """Remueve el último préstamo (pop)."""
        if self:
            return self.pop()
        return None

    def peek_last(self):
        """Ve el último préstamo sin remover."""
        if self:
            return self[-1]
        return None

class ColaSolicitudes(deque):
    """Cola (FIFO) para solicitudes de préstamo en espera."""
    def enqueue(self, request):
        """Agrega una solicitud."""
        self.append(request)

    def dequeue_first(self):
        """Remueve la primera solicitud."""
        if self:
            return self.popleft()
        return None

class Libro:
    """Clase para representar un libro."""
    def __init__(self, id, titulo, autor, genero, anio):
        self.id = id
        self.titulo = titulo
        self.autor = autor
        self.genero = genero
        self.anio = anio
        self.disponible = True

    def __dict__(self):
        return {
            'titulo': self.titulo,
            'autor': self.autor
        }

class Usuario:
    """Clase para representar un usuario."""
    def __init__(self, id, nombre, correo):
        self.id = id
        self.nombre = nombre
        self.correo = correo
        self.prestamos = PilaPrestamos()  # Pila para historial

class Biblioteca:
    def __init__(self):
        self.libros = ArrayLibros()  # Arreglo para libros
        self.usuarios = ListaEnlazada()  # Lista enlazada para usuarios
        self.solicitudes = ColaSolicitudes()  # Cola para solicitudes en espera
        self.indices_usuarios = {}  # Diccionario para búsqueda rápida por ID

    def registrar_libro(self, id, titulo, autor, genero, anio):
        """Registra un nuevo libro si el ID no está duplicado."""
        if any(libro.id == id for libro in self.libros):
            return False, f"Error: El ID {id} ya está registrado."
        nuevo_libro = Libro(id, titulo, autor, genero, anio)
        self.libros.append(nuevo_libro)
        return True, f"Libro '{titulo}' registrado con éxito."

    def registrar_usuario(self, id, nombre, correo):
        """Registra un nuevo usuario si el ID no está duplicado."""
        if id in self.indices_usuarios:
            return False, f"Error: El ID {id} ya está registrado."
        nuevo_usuario = Usuario(id, nombre, correo)
        self.usuarios.append(nuevo_usuario)
        self.indices_usuarios[id] = nuevo_usuario  # Índice para optimización
        return True, f"Usuario '{nombre}' registrado con éxito."

    def prestar_libro(self, id_usuario, id_libro):
        """Presta un libro: si disponible, lo asigna; si no, encola solicitud."""
        usuario = self.indices_usuarios.get(id_usuario)
        libro = self.libros.find_by_id(id_libro)
        
        if not usuario:
            return False, "Error: Usuario no encontrado."
        if not libro:
            return False, "Error: Libro no encontrado."
        if not libro.disponible:
            # Encola solicitud en lugar de rechazar
            self.solicitudes.enqueue((id_usuario, id_libro))
            return False, f"El libro '{libro.titulo}' no está disponible. Solicitud encolada."

        libro.disponible = False
        usuario.prestamos.push(id_libro)  # Agrega a pila (historial LIFO)
        return True, f"Libro '{libro.titulo}' prestado a {usuario.nombre} con éxito."

    def devolver_libro(self, id_libro):
        """Devuelve un libro: verifica que sea el último de algún usuario."""
        libro = self.libros.find_by_id(id_libro)
        if not libro:
            return False, "Error: Libro no encontrado."
        if libro.disponible:
            return False, f"Error: El libro '{libro.titulo}' ya está disponible."

        # Buscar usuario que tenga este libro como último préstamo (LIFO)
        usuario_encontrado = None
        for user_id in list(self.indices_usuarios.keys()):
            usuario = self.indices_usuarios[user_id]
            if usuario.prestamos.peek_last() == id_libro:
                usuario_encontrado = usuario
                break
        
        if not usuario_encontrado:
            return False, "Error: No se encontró un préstamo activo para este libro."

        libro.disponible = True
        usuario_encontrado.prestamos.pop_last()  # Remueve de pila
        # Remover de cola si está (por si acaso)
        self.solicitudes = ColaSolicitudes([req for req in self.solicitudes if req[1] != id_libro])
        return True, f"Libro '{libro.titulo}' devuelto por {usuario_encontrado.nombre} con éxito."

    def buscar_libro(self, criterio, valor):
        """Busca libros por título o autor."""
        if criterio not in ["titulo", "autor"]:
            return False, "Criterio inválido. Use 'titulo' o 'autor'."
        resultados = self.libros.search_by_criteria(criterio, valor)
        if not resultados:
            return False, f"No se encontraron libros con {criterio} = {valor}."
        msg = "Resultados:\n"
        for libro in resultados:
            msg += f"ID: {libro.id}, Título: {libro.titulo}, Autor: {libro.autor}, " \
                   f"Género: {libro.genero}, Año: {libro.anio}, Disponible: {libro.disponible}\n"
        return True, msg

# Interfaz Gráfica con Tkinter
class AppBiblioteca:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión de Biblioteca")
        self.biblioteca = Biblioteca()
        self.crear_interfaz()

    def crear_interfaz(self):
        # Menú principal
        tk.Button(self.root, text="1. Registrar Libro", command=self.registrar_libro).pack(pady=5)
        tk.Button(self.root, text="2. Registrar Usuario", command=self.registrar_usuario).pack(pady=5)
        tk.Button(self.root, text="3. Prestar Libro", command=self.prestar_libro).pack(pady=5)
        tk.Button(self.root, text="4. Devolver Libro", command=self.devolver_libro).pack(pady=5)
        tk.Button(self.root, text="5. Buscar Libro", command=self.buscar_libro).pack(pady=5)
        tk.Button(self.root, text="Salir", command=self.root.quit).pack(pady=5)

    def mostrar_mensaje(self, exito, mensaje):
        if exito:
            messagebox.showinfo("Éxito", mensaje)
        else:
            messagebox.showerror("Error", mensaje)

    def input_seguro(self, prompt):
        """Input seguro con validación. Infiera tipo basado en prompt."""
        is_id = "ID" in prompt
        tipo = int if is_id else str
        try:
            valor = simpledialog.askstring("Entrada", prompt)
            if valor is None:
                return None
            return tipo(valor)
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Entrada inválida. Intente de nuevo.")
            return None

    def registrar_libro(self):
        id_libro = self.input_seguro("ID del libro:")
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
        id_usuario = self.input_seguro("ID del usuario:")
        if id_usuario is None: return
        nombre = self.input_seguro("Nombre del usuario:")
        if nombre is None: return
        correo = self.input_seguro("Correo del usuario:")
        if correo is None: return
        exito, msg = self.biblioteca.registrar_usuario(id_usuario, nombre, correo)
        self.mostrar_mensaje(exito, msg)

    def prestar_libro(self):
        id_usuario = self.input_seguro("ID del usuario:")
        if id_usuario is None: return
        id_libro = self.input_seguro("ID del libro:")
        if id_libro is None: return
        exito, msg = self.biblioteca.prestar_libro(id_usuario, id_libro)
        self.mostrar_mensaje(exito, msg)

    def devolver_libro(self):
        id_libro = self.input_seguro("ID del libro a devolver:")
        if id_libro is None: return
        exito, msg = self.biblioteca.devolver_libro(id_libro)
        self.mostrar_mensaje(exito, msg)

    def buscar_libro(self):
        criterio_input = simpledialog.askstring("Búsqueda", "Buscar por (titulo/autor):")
        if not criterio_input: return
        valor = simpledialog.askstring("Búsqueda", "Valor a buscar:")
        if not valor: return
        exito, msg = self.biblioteca.buscar_libro(criterio_input, valor)
        self.mostrar_mensaje(exito, msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = AppBiblioteca(root)
    root.mainloop()