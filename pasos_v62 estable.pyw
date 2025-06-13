import tkinter as tk
from tkinter import messagebox
import data
from tkinter import ttk
import heapq
from PIL import Image, ImageTk
import sys
import os

def resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso para ejecutables creados con PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# === UI Style Constants ===
BG_COLOR = "#E6F0FA"
FG_COLOR = "black"
BTN_BG = "lightgrey"
BTN_FG = "black"
BTN_FONT = ("Arial", 10, "bold")
TITLE_FONT = ("Arial", 18, "bold")
VERSION = "v.2.22.100"
AUTOR = "Zala"

def create_button(parent, text, command, **kwargs):
    """Crea un botón estilizado."""
    btn = tk.Button(parent, text=text, command=command,
                    bg=BTN_BG, fg=BTN_FG, font=BTN_FONT,
                    activebackground="#3366cc")
    for k, v in kwargs.items():
        setattr(btn, k, v)
    return btn

def normalize(name):
    """Normaliza el nombre de una estación."""
    return name.replace('-', '').replace(' ', '').upper()

def cargar_fondo(frame, archivo, ancho=1280, alto=1024, opacidad=0.25):
    """Carga y coloca una imagen de fondo redimensionada y con opacidad."""
    try:
        imagen = Image.open(resource_path(archivo)).convert("RGBA")
        imagen = imagen.resize((ancho, alto), Image.LANCZOS)
        alpha = imagen.split()[3]
        alpha = alpha.point(lambda p: int(p * opacidad))
        imagen.putalpha(alpha)
        fondo_img = ImageTk.PhotoImage(imagen)
        fondo = tk.Label(frame, image=fondo_img, bg=BG_COLOR)
        fondo.image = fondo_img  # Evita que se borre por el recolector de basura
        fondo.place(relx=0.5, rely=0.5, anchor="center")
        fondo.lower()
        return fondo
    except Exception as e:
        print(f"Error cargando fondo: {e}")

        

class PathFinder:
    """Calcula rutas mínimas entre estaciones."""
    def __init__(self, listas, correspondencias, excepciones, depositos_asoc, corresp_depositos):
        self.listas = listas
        self.correspondencias = correspondencias
        self.excepciones = excepciones
        self.depositos_asoc = depositos_asoc
        self.corresp_depositos = corresp_depositos
        self.graph = self._build_graph()
        self.excepciones2 = data.EXCEPCIONES2
        self.station_to_line = {
            normalize(est): linea for linea, lista in self.listas.items() for est in lista
        }
        self.normalized_to_original = {
            normalize(est): est for lista in self.listas.values() for est in lista
        }

    def _build_graph(self):
        graph = {}
        LINEAS_CIRCULARES = ["Línea 6", "Línea 12"]
        for linea, estaciones in self.listas.items():
            if linea.strip().upper() == "DEPOSITOS":
                continue
            for i in range(len(estaciones) - 1):
                e1, e2 = normalize(estaciones[i]), normalize(estaciones[i + 1])
                graph.setdefault(e1, []).append(e2)
                graph.setdefault(e2, []).append(e1)
            if linea in LINEAS_CIRCULARES:
                e_inicio, e_final = normalize(estaciones[0]), normalize(estaciones[-1])
                graph.setdefault(e_inicio, []).append(e_final)
                graph.setdefault(e_final, []).append(e_inicio)
        for origen, destinos in self.correspondencias.items():
            for destino in destinos:
                o_n, d_n = normalize(origen), normalize(destino)
                graph.setdefault(o_n, []).append(d_n)
                graph.setdefault(d_n, []).append(o_n)
        for origen, destinos in self.corresp_depositos.items():
            for destino in destinos:
                o_n, d_n = normalize(origen), normalize(destino)
                graph.setdefault(o_n, []).append(d_n)
                graph.setdefault(d_n, []).append(o_n)
        for dep, est in self.depositos_asoc.items():
            dep_n, est_n = normalize(dep), normalize(est)
            graph.setdefault(dep_n, []).append(est_n)
            graph.setdefault(est_n, []).append(dep_n)
        return graph

    def _get_excepcion_coste(self, est1, est2):
        k1, k2 = (normalize(est1), normalize(est2)), (normalize(est2), normalize(est1))
        return self.excepciones.get(k1) or self.excepciones.get(k2) \
            or self.excepciones2.get(k1) or self.excepciones2.get(k2) or 1

    def find_path(self, origen, destino):
        origen_calc = normalize(self.depositos_asoc.get(origen, origen))
        destino_calc = normalize(self.depositos_asoc.get(destino, destino))
        if origen_calc not in self.graph or destino_calc not in self.graph:
            return None, []
        pq = [(0, origen_calc, [origen_calc])]
        best = {origen_calc: 0}
        ruta_nucleo = []
        while pq:
            cost, nodo, path = heapq.heappop(pq)
            if nodo == destino_calc:
                ruta_nucleo = path
                pasos_finales = cost
                break
            for vecino in self.graph.get(nodo, []):
                key = (normalize(nodo), normalize(vecino))
                key_inv = (normalize(vecino), normalize(nodo))
                step = self.excepciones.get(key) or self.excepciones.get(key_inv) \
                    or self.excepciones2.get(key) or self.excepciones2.get(key_inv) \
                    or self.corresp_depositos.get(key) or self.corresp_depositos.get(key_inv) \
                    or 1
                new_cost = cost + step
                if new_cost < best.get(vecino, float('inf')):
                    best[vecino] = new_cost
                    heapq.heappush(pq, (new_cost, vecino, path + [vecino]))
        if not ruta_nucleo:
            return None, []
        ruta_final = ruta_nucleo[:]
        pasos_finales = best[destino_calc]
        if origen in self.depositos_asoc:
            paso_extra = self._get_excepcion_coste(origen, self.depositos_asoc[origen])
            pasos_finales += paso_extra
            ruta_final = [normalize(origen)] + ruta_final
        if destino in self.depositos_asoc:
            paso_extra = self._get_excepcion_coste(self.depositos_asoc[destino], destino)
            pasos_finales += paso_extra
            ruta_final = ruta_final + [normalize(destino)]
        if origen in self.corresp_depositos and destino in self.corresp_depositos[origen]:
            return 1, [origen, destino]
        if destino in self.corresp_depositos and origen in self.corresp_depositos[destino]:
            return 1, [origen, destino]
        return pasos_finales, ruta_final

# === Application with Frames ===
class App(tk.Tk):
    """Ventana principal de la aplicación."""
    def __init__(self):
        super().__init__()
        self.title("SCMM - Pasos")
        try:
            self.iconbitmap(resource_path("icono.ico"))
        except Exception as e:
            print(f"Icono no encontrado: {e}")
        self.geometry("800x600")
        self.configure(bg=BG_COLOR)
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        for F in (MenuFrame, StepsFrame, OptionBFrame):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(MenuFrame)

    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        frame.tkraise()

class MenuFrame(tk.Frame):
    """Menú principal."""
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_COLOR)
        cargar_fondo(self, "marca_agua.png")
        tk.Label(self, text="🚆  SCMM - Selección de Modo", fg="darkblue",
                bg=BG_COLOR, font=TITLE_FONT).pack(pady=(40,10))
        tk.Frame(self, bg="darkblue", height=2, width=500).pack(pady=(0,20))
        create_button(self, "🚆 Opción A - PASOS Origen - Destino",
                      lambda: controller.show_frame(StepsFrame),
                      width=40, pady=10).pack(pady=10)
        create_button(self, "🚆 Opción B - DESTINOS",
                      lambda: controller.show_frame(OptionBFrame),
                      width=40, pady=10).pack(pady=10)
        create_button(self, "❌ SALIR", controller.quit,
              width=40, pady=10).pack(pady=(30, 10))
        tk.Label(self, text=AUTOR, fg="#CCAA80", bg=BG_COLOR,
                 font=("Arial",8,"italic")).place(x=10, rely=1.0, anchor="sw")
        tk.Label(self, text=VERSION, fg="#CCAA80", bg=BG_COLOR,
                 font=("Arial",8,"italic")).place(relx=1.0, rely=1.0, anchor="se")

class OptionBFrame(tk.Frame):
    """Opción B: muestra los destinos mínimos desde una estación."""
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_COLOR)
        cargar_fondo(self, "marca_agua.png")
        self.controller = controller
        self.listas = data.LISTAS
        tk.Label(self, text="🚆  SCMM - DESTINOS", fg="darkblue",
                bg=self["bg"], font=TITLE_FONT).pack(pady=(40,10))
        tk.Frame(self, bg="darkblue", height=2, width=400).pack(pady=(0,20))
        col = tk.Frame(self, bg=BG_COLOR)
        col.pack(pady=10)
        tk.Label(col, text="Línea", fg=FG_COLOR,
                 bg=BG_COLOR, font=("Arial",12,"bold")).pack()
        self.linea_origen_b = tk.StringVar(value=list(self.listas.keys())[0])
        opt_linea = tk.OptionMenu(col, self.linea_origen_b, *self.listas.keys())
        opt_linea.config(bg=BTN_BG, fg=BTN_FG, font=BTN_FONT)
        opt_linea.pack()
        create_button(col, "Seleccionar estación", self._abrir_listbox_b).pack(pady=5)
        self.estacion_origen_b = tk.StringVar()
        btn_frame = tk.Frame(self, bg=BG_COLOR)
        btn_frame.pack(pady=10)
        create_button(btn_frame, "Calcular pasos", self.calcular_minimos_desde_origen).pack(side="left", padx=5)
        create_button(btn_frame, "Borrar datos", self.borrar_datos).pack(side="left", padx=5)
        self.lista_resultados = tk.Text(self, font=("Arial", 11), bg="#ccffcc", width=50, height=12, wrap="none")
        self.lista_resultados.tag_configure("pasos", foreground="red", font=("Arial", 11, "bold"))
        self.lista_resultados.config(state="disabled")
        self.lista_resultados.pack(pady=(10, 5))
        volver_frame = tk.Frame(self, bg=BG_COLOR)
        volver_frame.pack(side="bottom", pady=10)
        create_button(volver_frame, "⬅ Volver al Menú", lambda: controller.show_frame(MenuFrame)).pack()
        tk.Label(self, text=AUTOR, fg="#CCAA80", bg=BG_COLOR,
                 font=("Arial",8,"italic")).place(x=10, rely=1.0, anchor="sw")
        tk.Label(self, text=VERSION, fg="#CCAA80", bg=BG_COLOR,
                 font=("Arial",8,"italic")).place(relx=1.0, rely=1.0, anchor="se")
        tk.Label(col, textvariable=self.estacion_origen_b, fg=FG_COLOR,
                 bg=BG_COLOR, font=("Arial",10)).pack()

    def borrar_datos(self):
        self.estacion_origen_b.set("")
        self.lista_resultados.config(state="normal")
        self.lista_resultados.delete("1.0", tk.END)
        self.lista_resultados.config(state="disabled")

    def calcular_minimos_desde_origen(self):
        origen = self.estacion_origen_b.get()
        if not origen:
            messagebox.showerror("Error", "Selecciona una estación de origen")
            return
        pf = PathFinder(data.LISTAS, data.CORRESPONDENCIAS, data.EXCEPCIONES, data.DEPOSITOS_ASOCIACIONES, data.CORRESPONDENCIAS_DEPOSITOS)
        mejores = []
        destinos = data.CABECERAS + data.DEPOSITOS
        for destino in destinos:
            if destino == origen:
                continue
            pasos, _ = pf.find_path(origen, destino)
            if pasos is not None:
                mejores.append((pasos, destino))
        if not mejores:
            messagebox.showinfo("Resultado", "Sin rutas posibles")
        else:
            from data import ORDEN_LINEAS
            def orden_linea(est):
                clave = est.split('-')[0]
                return ORDEN_LINEAS.get(clave, 999)
            mejores.sort(key=lambda x: (x[0], orden_linea(x[1])))
            self.lista_resultados.config(state="normal")
            self.lista_resultados.delete("1.0", tk.END)
            for i, (pasos, estacion) in enumerate(mejores[:20], start=1):
                texto = f"{i:<4}{pasos:<4}{estacion}\n"
                self.lista_resultados.insert(tk.END, texto[:4])  # Número de orden
                self.lista_resultados.insert(tk.END, texto[4:8], "pasos")  # Número de pasos en rojo
                self.lista_resultados.insert(tk.END, texto[8:])  # Nombre estación
            self.lista_resultados.config(state="disabled")

    def _abrir_listbox_b(self):
        win = tk.Toplevel(self)
        win.title("Seleccionar estación")
        win.configure(bg=BG_COLOR)
        entry = tk.Entry(win, font=("Arial",10))
        entry.pack(fill="x", padx=10, pady=(10,0))
        frame = tk.Frame(win)
        frame.pack(padx=10, pady=5)
        tree = ttk.Treeview(frame, show='tree', height=10)
        vsb = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)
        estaciones = self.listas[self.linea_origen_b.get()]
        tree.tag_configure('cabecera', font=("Arial",10,"bold"), foreground='black')
        tree.tag_configure('deposito', font=("Arial",10,"bold"), foreground='black')
        for est in estaciones:
            tag = 'cabecera' if est in getattr(data, 'CABECERAS', []) else 'deposito' if est in getattr(data, 'DEPOSITOS', []) else ''
            tree.insert('', 'end', text=est, tags=(tag,))
        def select():
            sel = tree.item(tree.selection()[0], 'text')
            self.estacion_origen_b.set(sel)
            win.destroy()
        create_button(win, "Seleccionar", select).pack(pady=10)
        tree.bind("<Double-1>", lambda e: select())

class StepsFrame(tk.Frame):
    """Opción A: calcula pasos entre origen y destino."""
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_COLOR)
        cargar_fondo(self, "marca_agua.png")
        self.controller = controller
        self.listas = data.LISTAS
        self.cabeceras = data.CABECERAS
        self.depositos = data.DEPOSITOS
        self.station_to_line = {
            est: linea for linea, lista in self.listas.items() for est in lista
        }
        self.normalized_to_original = {
            normalize(est): est for linea, lista in self.listas.items() for est in lista
        }

        # TÍTULO PRINCIPAL CON ICONO Y ESTILO
        tk.Label(self, text="🚆  SCMM - Origen - Destino", fg="darkblue",
                 bg=BG_COLOR, font=TITLE_FONT).pack(pady=(40,10))
        tk.Frame(self, bg="darkblue", height=2, width=500).pack(pady=(0,20))

        cont = tk.Frame(self, bg=BG_COLOR)
        cont.pack(pady=10)
        
        cont = tk.Frame(self, bg=BG_COLOR)
        cont.pack(pady=10)
        col_o = tk.Frame(cont, bg=BG_COLOR)
        col_o.grid(row=0, column=0, padx=20)
        tk.Label(col_o, text="Línea Origen", fg=FG_COLOR,
                bg=BG_COLOR, font=("Arial",12,"bold")).pack()
        self.linea_origen_var = tk.StringVar(value=list(self.listas.keys())[0])
        opt_o = tk.OptionMenu(col_o, self.linea_origen_var, *self.listas.keys())
        opt_o.config(bg=BTN_BG, fg=BTN_FG, font=BTN_FONT)
        opt_o.pack()
        create_button(col_o, "Seleccionar estación", self.abrir_listbox_origen).pack(pady=5)
        self.origen_var = tk.StringVar()
        tk.Label(col_o, textvariable=self.origen_var, fg=FG_COLOR,
                bg=BG_COLOR, font=("Arial",10)).pack()
        col_d = tk.Frame(cont, bg=BG_COLOR)
        col_d.grid(row=0, column=1, padx=20)
        tk.Label(col_d, text="Línea Destino", fg=FG_COLOR,
                bg=BG_COLOR, font=("Arial",12,"bold")).pack()
        self.linea_destino_var = tk.StringVar(value=list(self.listas.keys())[0])
        opt_d = tk.OptionMenu(col_d, self.linea_destino_var, *self.listas.keys())
        opt_d.config(bg=BTN_BG, fg=BTN_FG, font=BTN_FONT)
        opt_d.pack()
        create_button(col_d, "Seleccionar estación", self.abrir_listbox_destino).pack(pady=5)
        self.destino_var = tk.StringVar()
        tk.Label(col_d, textvariable=self.destino_var, fg=FG_COLOR,
                bg=BG_COLOR, font=("Arial",10)).pack()
        btn_frame = tk.Frame(self, bg=BG_COLOR)
        btn_frame.pack(pady=10)
        create_button(btn_frame, "Calcular pasos", self.calcular_distancia).pack(side="left", padx=5)
        create_button(btn_frame, "Borrar datos", self.borrar_datos).pack(side="left", padx=5)
        self.ruta_label = tk.Label(self, text="", bg="#ccffcc",
                                    font=("Arial",9), relief="groove", bd=2)
        self.ruta_label.pack(fill="x", padx=20, pady=(5,2))
        self.resultado_label = tk.Label(self, text="", bg="#ccffcc",
                                        font=("Arial",14,"bold"), relief="groove", bd=2)
        self.resultado_label.pack(fill="x", padx=20, pady=(2,10))
        tk.Label(self, text=AUTOR, fg="#CCAA80", bg=BG_COLOR,
                 font=("Arial",8,"italic")).place(x=10, rely=1.0, anchor="sw")
        tk.Label(self, text=VERSION, fg="#CCAA80", bg=BG_COLOR,
                 font=("Arial",8,"italic")).place(relx=1.0, rely=1.0, anchor="se")
        create_button(self, "⬅ Volver al Menú",
                      lambda: controller.show_frame(MenuFrame)).pack(side="bottom", pady=10)

    def abrir_listbox_origen(self):
        self._abrir_listbox('origen')
    def abrir_listbox_destino(self):
        self._abrir_listbox('destino')
    def _abrir_listbox(self, tipo):
        win = tk.Toplevel(self)
        win.title("Seleccionar estación")
        win.configure(bg=BG_COLOR)
        entry = tk.Entry(win, font=("Arial",10))
        entry.pack(fill="x", padx=10, pady=(10,0))
        frame = tk.Frame(win)
        frame.pack(padx=10, pady=5)
        tree = ttk.Treeview(frame, show='tree', height=10)
        vsb = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)
        tree.tag_configure('cabecera', font=("Arial",10,"bold"), foreground='black')
        tree.tag_configure('deposito', font=("Arial",10,"bold"), foreground='black')
        estaciones = self.listas[self.linea_origen_var.get()] if tipo=='origen' else self.listas[self.linea_destino_var.get()]
        for est in estaciones:
            if est in self.cabeceras:
                tag = 'cabecera'
            elif est in self.depositos:
                tag = 'deposito'
            else:
                tag = ''
            tree.insert('', 'end', text=est, tags=(tag,))
        def select():
            sel = tree.item(tree.selection()[0], 'text')
            if tipo=='origen':
                self.origen_var.set(sel)
            else:
                self.destino_var.set(sel)
            win.destroy()
        create_button(win, "Seleccionar", select).pack(pady=10)
        tree.bind("<Double-1>", lambda e: select())

    def calcular_distancia(self):
        origen = self.origen_var.get()
        destino = self.destino_var.get()
        if not origen or not destino:
            messagebox.showerror("Error", "Selecciona origen y destino.")
            return
        pf = PathFinder(
            self.listas,
            data.CORRESPONDENCIAS,
            data.EXCEPCIONES,
            data.DEPOSITOS_ASOCIACIONES,
            data.CORRESPONDENCIAS_DEPOSITOS
        )
        pasos, ruta = pf.find_path(origen, destino)
        if pasos is None:
            self.resultado_label.config(text="Ruta no encontrada", fg="red")
            self.ruta_label.config(text="")
        else:
            resumida = []
            linea_anterior = self.station_to_line.get(self.normalized_to_original.get(ruta[0], ruta[0]), "")
            resumida.append(self.normalized_to_original.get(ruta[0], ruta[0]))
            for i in range(1, len(ruta)):
                actual = ruta[i]
                est_nombre = self.normalized_to_original.get(actual, actual)
                linea_actual = self.station_to_line.get(est_nombre, "")
                if linea_actual != linea_anterior:
                    resumida.append(est_nombre)
                linea_anterior = linea_actual
            nombre_final = self.normalized_to_original.get(ruta[-1], ruta[-1])
            if resumida[-1] != nombre_final:
                resumida.append(nombre_final)
            ruta_texto = ' → '.join(resumida)
            max_linea = 80
            lineas = []
            actual = ""
            for tramo in ruta_texto.split(' → '):
                if len(actual) + len(tramo) + 3 <= max_linea:
                    actual += (' → ' if actual else '') + tramo
                else:
                    lineas.append(actual)
                    actual = tramo
            if actual:
                lineas.append(actual)
            ruta_final = '\n'.join(lineas)
            self.ruta_label.config(text=ruta_final, fg="black")
            self.resultado_label.config(text=f"{pasos} pasos", fg="green")

    def borrar_datos(self):
        self.origen_var.set("")
        self.destino_var.set("")
        self.ruta_label.config(text="")
        self.resultado_label.config(text="")

if __name__ == "__main__":
    app = App()
    app.mainloop()
    print("Interfaz lanzada correctamente")