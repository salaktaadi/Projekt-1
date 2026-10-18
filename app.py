import json
import os
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry
from PIL import Image, ImageTk

# --- WINDOWS HI-DPI ÉLESÍTÉSI JAVÍTÁS (Megszünteti a pixelességet) ---
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

FILENAME = "tasks.json"

def load_tasks():
    if os.path.exists(FILENAME):
        try:
            with open(FILENAME, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_tasks(tasks):
    with open(FILENAME, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def get_transparent_shield_logo(logo_path, target_height=48):
    """
    Betölti a logo.png-t, eltávolítja a fehér hátteret (átlátszóvá teszi),
    a fekete vonalakat világos kékre/ezüstre szzínezi és levágja a margót.
    """
    if not os.path.exists(logo_path):
        return None

    try:
        img = Image.open(logo_path).convert("RGBA")
        datas = img.getdata()
        new_data = []
        for item in datas:
            # Fehér háttér kiszűrése -> Átlátszó
            if item[0] > 210 and item[1] > 210 and item[2] > 210:
                new_data.append((255, 255, 255, 0))
            else:
                # Sötét vonalak -> Világos kék/ezüst
                new_data.append((240, 246, 252, 255))

        img.putdata(new_data)

        # Üres margók levágása
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)

        # Méretezés
        aspect_ratio = img.width / img.height
        target_width = int(target_height * aspect_ratio)
        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

        return ImageTk.PhotoImage(img)
    except Exception as e:
        print("Logó feldolgozási hiba:", e)
        return None

class PerseusTaskApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Perseus Dataworks // Céges Feladatkezelő")
        self.root.geometry("1060x660")
        self.root.minsize(960, 580)
        self.root.config(bg="#07090e")

        self.tasks = load_tasks()
        self.selected_task_id = None

        # Modern UI Stílusok
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("Treeview", 
                        background="#111827", 
                        foreground="#f3f4f6", 
                        fieldbackground="#111827", 
                        rowheight=35,
                        font=("Inter", 10))
        style.configure("Treeview.Heading", 
                        background="#1f2937", 
                        foreground="#9ca3af", 
                        font=("Inter", 10, "bold"),
                        relief="flat")
        style.map("Treeview", 
                  background=[("selected", "#0ea5e9")], 
                  foreground=[("selected", "#ffffff")])

        # Fő konténer
        main_container = tk.Frame(root, bg="#07090e")
        main_container.pack(fill=tk.BOTH, expand=True, padx=24, pady=24)

        # --- FELSŐ MÁRKÁS SÁV (Perseus Dataworks) ---
        brand_bar = tk.Frame(main_container, bg="#111827", highlightbackground="#1f2937", highlightthickness=1)
        brand_bar.pack(fill=tk.X, pady=(0, 16))

        brand_inner = tk.Frame(brand_bar, bg="#111827", padx=18, pady=12)
        brand_inner.pack(fill=tk.X)

        # Logó betöltése
        self.logo_photo = get_transparent_shield_logo("logo.png", target_height=44)
        if self.logo_photo:
            logo_lbl = tk.Label(brand_inner, image=self.logo_photo, bg="#111827")
            logo_lbl.pack(side=tk.LEFT, padx=(0, 16))

        title_frame = tk.Frame(brand_inner, bg="#111827")
        title_frame.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(title_frame, text="PERSEUS DATAWORKS", font=("Inter", 13, "bold"), bg="#111827", fg="#ffffff").pack(anchor="w")
        tk.Label(title_frame, text="Vállalati Feladatkezelő & Admin Vezérlő", font=("Inter", 8, "bold"), bg="#111827", fg="#38bdf8").pack(anchor="w")

        # Osztott terület
        content_container = tk.Frame(main_container, bg="#07090e")
        content_container.pack(fill=tk.BOTH, expand=True)

        # ------------------- BAL OLDAL: Lista és Keresés -------------------
        left_panel = tk.Frame(content_container, bg="#111827", highlightbackground="#1f2937", highlightthickness=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 16))

        header_frame = tk.Frame(left_panel, bg="#111827")
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 12))

        tk.Label(header_frame, text="Aktív Céges Feladatok", font=("Inter", 13, "bold"), bg="#111827", fg="#f3f4f6").pack(anchor="w")

        search_frame = tk.Frame(left_panel, bg="#111827")
        search_frame.pack(fill=tk.X, padx=20, pady=(0, 15))

        tk.Label(search_frame, text="Keresés", font=("Inter", 9, "bold"), bg="#111827", fg="#9ca3af").pack(anchor="w", pady=(0, 4))
        self.search_entry = tk.Entry(search_frame, font=("Inter", 10), bg="#07090e", fg="#f3f4f6", insertbackground="white", relief=tk.FLAT)
        self.search_entry.pack(fill=tk.X, ipady=6)
        self.search_entry.bind("<KeyRelease>", self.filter_tasks)

        tree_frame = tk.Frame(left_panel, bg="#111827")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        columns = ("date", "category", "important", "title")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("date", text="Határidő")
        self.tree.heading("category", text="Munkaterület")
        self.tree.heading("important", text="Prioritás")
        self.tree.heading("title", text="Feladat Neve")

        self.tree.column("date", width=105, anchor="center")
        self.tree.column("category", width=155, anchor="center")
        self.tree.column("important", width=90, anchor="center")
        self.tree.column("title", width=220, anchor="w")

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_task_select)

        # ------------------- JOBB OLDAL: Kezelőpanel -------------------
        right_panel = tk.Frame(content_container, bg="#111827", highlightbackground="#1f2937", highlightthickness=1, width=350)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(0, 0))
        right_panel.pack_propagate(False)

        form_frame = tk.Frame(right_panel, bg="#111827", padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(form_frame, text="Feladat Szerkesztő", font=("Inter", 12, "bold"), bg="#111827", fg="#f3f4f6").pack(anchor="w", pady=(0, 16))

        # Határidő
        tk.Label(form_frame, text="Határidő", font=("Inter", 9, "bold"), bg="#111827", fg="#9ca3af").pack(anchor="w")
        self.date_entry = DateEntry(form_frame, width=20, background='#0ea5e9', foreground='#ffffff', 
                                    headersbackground='#1f2937', headersforeground='#f3f4f6',
                                    borderwidth=1, date_pattern='yyyy-mm-dd', font=("Inter", 10))
        self.date_entry.pack(fill=tk.X, pady=(4, 14), ipady=3)

        # Munkaterület
        tk.Label(form_frame, text="Munkaterület", font=("Inter", 9, "bold"), bg="#111827", fg="#9ca3af").pack(anchor="w")
        self.category_var = tk.StringVar(value="Fejlesztés & IT")
        corporate_categories = [
            "Fejlesztés & IT",
            "Adminisztráció & HR",
            "Értékesítés & Sales",
            "Marketing & Kommunikáció",
            "Logisztika & Üzemeltetés",
            "Pénzügy & Könyvelés",
            "Általános céges feladat"
        ]
        self.cat_dropdown = ttk.Combobox(form_frame, textvariable=self.category_var, values=corporate_categories, state="readonly", font=("Inter", 10))
        self.cat_dropdown.pack(fill=tk.X, pady=(4, 14), ipady=3)

        # Fontos Checkbox
        self.important_var = tk.BooleanVar()
        self.important_check = tk.Checkbutton(form_frame, text="Kiemelten fontos prioritás", variable=self.important_var,
                                               bg="#111827", fg="#f59e0b", activebackground="#111827", activeforeground="#f59e0b",
                                               selectcolor="#07090e", font=("Inter", 9, "bold"))
        self.important_check.pack(anchor="w", pady=(0, 14))

        # Cím
        tk.Label(form_frame, text="Feladat megnevezése", font=("Inter", 9, "bold"), bg="#111827", fg="#9ca3af").pack(anchor="w")
        self.title_entry = tk.Entry(form_frame, font=("Inter", 10), bg="#07090e", fg="#f3f4f6", insertbackground="white", relief=tk.FLAT)
        self.title_entry.pack(fill=tk.X, pady=(4, 14), ipady=6)

        # Leírás
        tk.Label(form_frame, text="Részletes leírás", font=("Inter", 9, "bold"), bg="#111827", fg="#9ca3af").pack(anchor="w")
        self.desc_text = tk.Text(form_frame, font=("Inter", 9), height=4, bg="#07090e", fg="#f3f4f6", insertbackground="white", relief=tk.FLAT)
        self.desc_text.pack(fill=tk.X, pady=(4, 20))

        # Gombok
        self.save_btn = tk.Button(form_frame, text="Feladat rögzítése", bg="#10b981", fg="#ffffff", font=("Inter", 9, "bold"), relief=tk.FLAT, cursor="hand2", command=self.save_task)
        self.save_btn.pack(fill=tk.X, pady=4, ipady=8)

        self.clear_btn = tk.Button(form_frame, text="Űrlap ürítése", bg="#374151", fg="#ffffff", font=("Inter", 9, "bold"), relief=tk.FLAT, cursor="hand2", command=self.clear_form)
        self.clear_btn.pack(fill=tk.X, pady=4, ipady=6)

        self.delete_btn = tk.Button(form_frame, text="Kijelölt törlése", bg="#ef4444", fg="#ffffff", font=("Inter", 9, "bold"), relief=tk.FLAT, cursor="hand2", command=self.delete_task)
        self.delete_btn.pack(fill=tk.X, pady=4, ipady=6)

        self.refresh_list()

    def refresh_list(self, filter_text=""):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for t in self.tasks:
            title = t.get("title", "")
            if filter_text and filter_text.lower() not in title.lower():
                continue

            date_val = t.get("date", "")
            cat_val = t.get("category", "Általános céges feladat")
            imp_val = "⭐ Kiemelt" if t.get("important", False) else "Szokásos"
            
            self.tree.insert("", tk.END, values=(date_val, cat_val, imp_val, title), iid=t["id"])

    def filter_tasks(self, event):
        text = self.search_entry.get().strip()
        self.refresh_list(text)

    def clear_form(self):
        self.selected_task_id = None
        self.date_entry.set_date(datetime.now())
        self.category_var.set("Fejlesztés & IT")
        self.important_var.set(False)
        self.title_entry.delete(0, tk.END)
        self.desc_text.delete("1.0", tk.END)
        self.save_btn.config(text="Feladat rögzítése", bg="#10b981")

    def on_task_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        task_id = int(selected_items[0])
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        if task:
            self.selected_task_id = task["id"]
            
            try:
                dt = datetime.strptime(task["date"], "%Y-%m-%d")
                self.date_entry.set_date(dt)
            except Exception:
                pass

            self.category_var.set(task.get("category", "Fejlesztés & IT"))
            self.important_var.set(task.get("important", False))
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, task.get("title", ""))
            self.desc_text.delete("1.0", tk.END)
            self.desc_text.insert("1.0", task.get("description", ""))
            self.save_btn.config(text="Módosítás mentése", bg="#0ea5e9")

    def save_task(self):
        date_str = self.date_entry.get_date().strftime("%Y-%m-%d")
        category = self.category_var.get()
        is_important = self.important_var.get()
        title = self.title_entry.get().strip()
        description = self.desc_text.get("1.0", tk.END).strip()

        if not title:
            messagebox.showerror("Hiba", "A feladat megnevezése kötelező!")
            return

        if self.selected_task_id:
            for t in self.tasks:
                if t["id"] == self.selected_task_id:
                    t["date"] = date_str
                    t["category"] = category
                    t["important"] = is_important
                    t["title"] = title
                    t["description"] = description
                    break
        else:
            new_task = {
                "id": int(datetime.now().timestamp() * 1000),
                "date": date_str,
                "category": category,
                "important": is_important,
                "title": title,
                "description": description
            }
            self.tasks.append(new_task)

        save_tasks(self.tasks)
        self.refresh_list()
        self.clear_form()
        messagebox.showinfo("Siker", "A céges feladat sikeresen mentve!")

    def delete_task(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Figyelmeztetés", "Előbb válassz ki egy feladatot a listából!")
            return
        
        if messagebox.askyesno("Megerősítés", "Biztosan törölni akarod ezt a feladatot a rendszerből?"):
            task_id = int(selected_items[0])
            self.tasks = [t for t in self.tasks if t["id"] != task_id]
            save_tasks(self.tasks)
            self.refresh_list()
            self.clear_form()

if __name__ == "__main__":
    root = tk.Tk()
    app = PerseusTaskApp(root)
    root.mainloop()