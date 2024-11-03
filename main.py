#Working Version, welche
#1. Nodes grafisch darstellen
#2. Nodes verschieben (links-klick halten und ziehen)
#3. Nodes bearbeiten (rechts-klick einfach oder doppelt)
#   a) Enter zum sichern
#   b) CTRL + ENTER für nächste Zeile in codesnippet
#   c) Save-Button zum sichern
#4. Menu Bar 
#   Simulation: 
#       i)  Start: führt den Code der Reihe der Node erstellung nach aus
#       ii) Stop: leer
#   Arrows: leer    (Pfeile ergänzen, um Nodes zu verknüpfen)
#   Datei: leer     (load and save setup ergänzen)

import tkinter as tk
from tkinter import Menu, Toplevel, Label, Entry, Text, Button

class Node:
    def __init__(self, editor, x, y, text, codesnippet=""):
        """Initialisiert eine neue Node und platziert sie im Canvas."""
        self.editor = editor
        self.x = x
        self.y = y
        self.radius = 30
        self.text = text
        self.codesnippet = codesnippet
        
        # Zeichne die Node auf dem Canvas
        self.node_id = self.editor.canvas.create_oval(
            x - self.radius, y - self.radius, x + self.radius, y + self.radius,
            fill="lightblue", outline="black"
        )
        self.label_id = self.editor.canvas.create_text(x, y, text=text, font=("Arial", 12))
        
        # Event-Bindungen für die Node-Interaktionen
        self.editor.canvas.tag_bind(self.node_id, "<ButtonPress-1>", self.on_press)
        self.editor.canvas.tag_bind(self.label_id, "<ButtonPress-1>", self.on_press)
        self.editor.canvas.tag_bind(self.node_id, "<B1-Motion>", self.on_move)
        self.editor.canvas.tag_bind(self.label_id, "<B1-Motion>", self.on_move)
        self.editor.canvas.tag_bind(self.node_id, "<ButtonRelease-1>", self.on_release)
        self.editor.canvas.tag_bind(self.label_id, "<ButtonRelease-1>", self.on_release)
        self.editor.canvas.tag_bind(self.node_id, "<ButtonPress-2>", self.open_edit_window)
        self.editor.canvas.tag_bind(self.label_id, "<ButtonPress-2>", self.open_edit_window)

    def on_press(self, event):
        """Setzt diese Node als aktuelle Zieh-Node."""
        self.editor.start_drag(self)

    def on_move(self, event):
        """Bewegt die Node entsprechend der Mausposition."""
        if self.editor.dragging_node == self:
            self.x, self.y = event.x, event.y
            self.editor.canvas.coords(self.node_id, self.x - self.radius, self.y - self.radius, 
                                      self.x + self.radius, self.y + self.radius)
            self.editor.canvas.coords(self.label_id, self.x, self.y)

    def on_release(self, event):
        """Beendet das Ziehen und fixiert die Node an der neuen Position."""
        print(f"Node '{self.text}' abgesetzt bei ({self.x}, {self.y})")
        self.editor.stop_drag()

    def open_edit_window(self, event):
        """Öffnet ein Fenster zur Bearbeitung von Name und codesnippet."""
        edit_window = Toplevel(self.editor.root)
        edit_window.title(f"Bearbeiten von {self.text}")
        edit_window.geometry("400x300")
        edit_window.transient(self.editor.root)  # Macht das Fenster "transient" zum Hauptfenster
        edit_window.grab_set()  # Erzwingt Modalität

        # Name bearbeiten
        Label(edit_window, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        name_entry = Entry(edit_window, width=20)
        name_entry.insert(0, self.text)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        name_entry.focus_set()  # Setzt den initialen Fokus auf das Name-Feld

        def save_name():
            new_name = name_entry.get()
            if new_name:
                self.text = new_name
                self.editor.canvas.itemconfig(self.label_id, text=self.text)
                print(f"Name aktualisiert: {self.text}")
            print("Save-Button für Namen geklickt")

        # Shortcut für Speichern
        edit_window.bind("<Control-Return>", lambda event: save_name())
        edit_window.bind("<Control-Enter>", lambda event: save_code())

        # Enter schließt den Fokus und macht Klick auf Save möglich
        name_entry.bind("<Return>", lambda event: edit_window.focus()) 

        Button(edit_window, text="Save", command=save_name).grid(row=0, column=2, padx=5, pady=5)

        # codesnippet bearbeiten
        Label(edit_window, text="Code:").grid(row=1, column=0, padx=5, pady=5, sticky="nw")
        code_text = Text(edit_window, width=40, height=10)
        code_text.insert("1.0", self.codesnippet)
        code_text.grid(row=1, column=1, columnspan=2, padx=5, pady=5)

        def save_code():
            new_code = code_text.get("1.0", "end-1c")
            self.codesnippet = new_code
            print(f"Code aktualisiert:\n{self.codesnippet}")
            print("Save-Button für Code geklickt")

        code_text.bind("<Control-Return>", lambda event: save_code())
        code_text.bind("<Control-Enter>", lambda event: save_code())
        #TODO: Experimentiere, ob damit besser ist.
        #code_text.bind("<Return>", lambda event: edit_window.focus())  # Enter schließt den Fokus

        Button(edit_window, text="Save", command=save_code).grid(row=2, column=1, pady=5)

        # Fenster schließen und Änderungen speichern
        def close_window():
            edit_window.grab_release()  # Gibt den Fokus wieder frei, wenn das Fenster geschlossen wird
            edit_window.destroy()

        Button(edit_window, text="Close", command=close_window).grid(row=2, column=2, padx=5, pady=5, sticky="e")

class NodeEditor:
    def __init__(self, root):
        """Initialisiert das Node-Editor-Interface und die Canvas-Oberfläche."""
        self.root = root
        self.canvas = tk.Canvas(root, width=700, height=500, bg="white")
        self.canvas.pack(pady=20)
        self.nodes = []
        self.dragging_node = None

    def add_node(self, x=100, y=100, text=None, codesnippet=""):
        """Erstellt eine neue Node und fügt sie der Canvas und dem Node-Manager hinzu."""
        if text is None:
            text = f"Node {len(self.nodes) + 1}"
        node = Node(self, x, y, text, codesnippet)
        self.nodes.append(node)

    def start_drag(self, node):
        """Aktiviert das Ziehen für die angeklickte Node."""
        self.dragging_node = node

    def stop_drag(self):
        """Beendet das Ziehen, wenn die Maustaste losgelassen wird."""
        self.dragging_node = None

    def run_simulation(self):
        """Führt den Python-Code in den Nodes in der Reihenfolge ihrer Erstellung aus."""
        local_scope = {}
        for node in self.nodes:
            print(f"Executing code in {node.text}:")
            try:
                exec(node.codesnippet, {}, local_scope)
            except Exception as e:
                print(f"Fehler beim Ausführen von {node.text}: {e}")
        print("Simulation abgeschlossen.\n")

class MenuBar:
    def __init__(self, root, editor):
        """Erstellt die Menüleiste mit verschiedenen Menüs und Buttons."""
        self.editor = editor
        menubar = Menu(root)
        
        # Datei-Menü
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load", command=lambda: self.display_message("Load"))
        menubar.add_cascade(label="Datei", menu=file_menu)

        # Nodes-Menü
        node_menu = Menu(menubar, tearoff=0)
        node_menu.add_command(label="New Node", command=self.create_node)
        menubar.add_cascade(label="Nodes", menu=node_menu)

        # Arrows-Menü
        arrow_menu = Menu(menubar, tearoff=0)
        arrow_menu.add_command(label="Arrow", command=lambda: self.display_message("Arrow"))
        menubar.add_cascade(label="Arrows", menu=arrow_menu)

        # Simulation-Menü
        sim_menu = Menu(menubar, tearoff=0)
        sim_menu.add_command(label="Start", command=self.editor.run_simulation)
        sim_menu.add_command(label="Stop", command=lambda: self.display_message("Stop"))
        menubar.add_cascade(label="Simulation", menu=sim_menu)

        # Weitere Buttons in der Menüleiste
        menubar.add_command(label="Reset", command=lambda: self.display_message("Reset"))

        # Menubar zum Root-Fenster hinzufügen
        root.config(menu=menubar)

    def create_node(self):
        """Erstellt eine neue Node im NodeEditor."""
        text = f"Node {len(self.editor.nodes) + 1}"
        codesnippet = ""  # Standardmäßig leer, kann angepasst werden
        self.editor.add_node(text=text, codesnippet=codesnippet)
        print("Neue Node erstellt.")

    def display_message(self, message):
        """Gibt den Namen des gedrückten Buttons aus."""
        print(f"{message} wurde geklickt.")

# Hauptanwendung
root = tk.Tk()
root.title("Node Editor mit Menüleiste")
editor = NodeEditor(root)
menu_bar = MenuBar(root, editor)

# Beispielhafte Erstellung von drei interaktiven Nodes mit Code
editor.add_node(100, 250, "Node 1", codesnippet="my_number = 10")
editor.add_node(300, 150, "Node 2", codesnippet="print('Node2:', my_number)")
editor.add_node(500, 300, "Node 3", codesnippet="my_number = 666\nprint('Anpassung in node3:', my_number)")

# Hauptschleife der GUI starten
root.mainloop()
