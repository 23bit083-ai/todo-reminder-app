import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import database
import reminder

class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📝 To-Do Reminder App")
        self.root.geometry("950x700")
        self.root.minsize(850, 600)
        self.root.eval('tk::PlaceWindow . center')
        self.is_dark_mode = False

        database.create_table()
        self.configure_styles()
        self.create_menu()
        self.create_widgets()
        self.setup_shortcuts()
        self.load_tasks()

        reminder.start_reminder_thread()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def configure_styles(self):
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))
        style.configure("TButton", font=("Arial", 10), padding=5)
        style.configure("TLabel", background="#f5f5f5", font=("Arial", 10))
        style.configure("Main.TFrame", background="#f5f5f5")
        style.configure("Title.TLabel", background="#f5f5f5", font=("Helvetica", 20, "bold"))

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export CSV", command=self.export_csv, accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing, accelerator="Ctrl+Q")

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Statistics", command=self.show_stats, accelerator="Ctrl+S")
        view_menu.add_command(label="Dark Mode", command=self.toggle_theme, accelerator="Ctrl+T")

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Shortcuts", command=self.show_help)

    def create_widgets(self):
        self.main_frame = ttk.Frame(self.root, padding="10", style="Main.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(self.main_frame, text="📋 To-Do Reminder App", style="Title.TLabel").pack(pady=10)

        entry_frame = ttk.Frame(self.main_frame, style="Main.TFrame")
        entry_frame.pack(pady=5, fill=tk.X, padx=20)

        ttk.Label(entry_frame, text="Task:").grid(row=0, column=0, padx=5, sticky="w")
        self.task_entry = ttk.Entry(entry_frame, width=60, font=("Arial", 11))
        self.task_entry.grid(row=0, column=1, padx=5, pady=2, columnspan=3, sticky="ew")

        ttk.Label(entry_frame, text="Date:").grid(row=1, column=0, padx=5, sticky="w")
        self.date_entry = ttk.Entry(entry_frame, width=15, font=("Arial", 10))
        self.date_entry.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(entry_frame, text="Time:").grid(row=1, column=2, padx=5, sticky="w")
        self.time_entry = ttk.Entry(entry_frame, width=10, font=("Arial", 10))
        self.time_entry.insert(0, "12:00")
        self.time_entry.grid(row=1, column=3, padx=5, pady=2, sticky="w")

        ttk.Label(entry_frame, text="Priority:").grid(row=2, column=0, padx=5, sticky="w")
        self.priority = tk.StringVar(value="Medium")
        ttk.Combobox(entry_frame, textvariable=self.priority, values=["High", "Medium", "Low"], 
                     width=12, state="readonly").grid(row=2, column=1, padx=5, pady=2, sticky="w")

        ttk.Label(entry_frame, text="Category:").grid(row=2, column=2, padx=5, sticky="w")
        self.category = tk.StringVar(value="General")
        ttk.Combobox(entry_frame, textvariable=self.category, 
                     values=["General", "Work", "Personal", "Shopping", "Health", "Study"], 
                     width=12, state="readonly").grid(row=2, column=3, padx=5, pady=2, sticky="w")

        ttk.Label(entry_frame, text="Notes:").grid(row=3, column=0, padx=5, sticky="nw")
        self.notes_text = tk.Text(entry_frame, height=2, width=60, font=("Arial", 10))
        self.notes_text.grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

        entry_frame.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(self.main_frame, style="Main.TFrame")
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Add Task", command=self.add_task).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Edit Task", command=self.edit_task).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Mark Done", command=self.mark_done).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_task).grid(row=0, column=3, padx=5)

        filter_frame = ttk.Frame(self.main_frame, style="Main.TFrame")
        filter_frame.pack(pady=5)

        ttk.Label(filter_frame, text="Filter:").grid(row=0, column=0, padx=5)
        self.filter_var = tk.StringVar(value="All")
        ttk.Combobox(filter_frame, textvariable=self.filter_var, 
                     values=["All", "Pending", "Done", "High Priority", "Overdue"], 
                     width=15, state="readonly").grid(row=0, column=1, padx=5)
        ttk.Button(filter_frame, text="Apply", command=self.load_tasks).grid(row=0, column=2, padx=5)

        ttk.Label(filter_frame, text="Search:").grid(row=0, column=3, padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=25)
        search_entry.grid(row=0, column=4, padx=5)
        search_entry.bind("<KeyRelease>", lambda e: self.search_tasks())

        self.tree = ttk.Treeview(self.main_frame, 
                                 columns=("ID", "Task", "Time", "Status", "Priority", "Category"), 
                                 show="headings", height=14)
        for col in ("ID", "Task", "Time", "Status", "Priority", "Category"):
            self.tree.heading(col, text=col)
            width = 50 if col == "ID" else 250 if col == "Task" else 120
            self.tree.column(col, width=width, anchor="center" if col != "Task" else "w")

        self.tree.pack(pady=10, fill=tk.BOTH, expand=True, padx=20)
        self.tree.bind('<Double-1>', lambda e: self.edit_task())

        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_shortcuts(self):
        self.root.bind('<Control-n>', lambda e: self.add_task())
        self.root.bind('<Control-e>', lambda e: self.export_csv())
        self.root.bind('<Control-d>', lambda e: self.delete_task())
        self.root.bind('<Control-s>', lambda e: self.show_stats())
        self.root.bind('<Control-t>', lambda e: self.toggle_theme())
        self.root.bind('<Control-q>', lambda e: self.on_closing())
        self.root.bind('<Delete>', lambda e: self.delete_task())
        self.root.bind('<F5>', lambda e: self.load_tasks())

    def validate_datetime(self, date_str, time_str):
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
            datetime.datetime.strptime(time_str, "%H:%M")
            combined = f"{date_str} {time_str}"
            datetime.datetime.strptime(combined, "%Y-%m-%d %H:%M")
            return True, combined
        except ValueError:
            return False, ""

    def add_task(self):
        task = self.task_entry.get().strip()
        date_str = self.date_entry.get().strip()
        time_str = self.time_entry.get().strip()
        priority = self.priority.get()
        category = self.category.get()
        notes = self.notes_text.get("1.0", tk.END).strip()

        if not task:
            messagebox.showwarning("Warning", "Please enter a task")
            return

        valid, datetime_str = self.validate_datetime(date_str, time_str)
        if not valid:
            messagebox.showerror("Error", "Invalid date/time. Use YYYY-MM-DD and HH:MM format")
            return

        task_id = database.add_task(task, datetime_str, priority, notes, category)
        if task_id:
            messagebox.showinfo("Success", "Task added!")
            self.clear_inputs()
            self.load_tasks()
            self.status_bar.config(text=f"Added: {task}")
        else:
            messagebox.showerror("Error", "Failed to add task")

    def clear_inputs(self):
        self.task_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
        self.time_entry.delete(0, tk.END)
        self.time_entry.insert(0, "12:00")
        self.priority.set("Medium")
        self.category.set("General")
        self.notes_text.delete("1.0", tk.END)

    def load_tasks(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        filter_type = self.filter_var.get()
        status_filter = None
        priority_filter = None

        if filter_type == "Pending":
            status_filter = "Pending"
        elif filter_type == "Done":
            status_filter = "Done"
        elif filter_type == "High Priority":
            priority_filter = "High"

        rows = database.get_tasks(status_filter=status_filter, priority_filter=priority_filter)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        for row in rows:
            task_id, task, time_, status, priority, notes, category = row

            if filter_type == "Overdue" and (status != "Pending" or time_ >= now):
                continue

            tags = []
            if status == "Pending" and time_ < now:
                tags.append("overdue")
            elif status == "Done":
                tags.append("done")
            else:
                tags.append(priority)

            self.tree.insert("", tk.END, values=(task_id, task, time_, status, priority, category), 
                           tags=tuple(tags))

        self.tree.tag_configure("High", background="#ffcccc")
        self.tree.tag_configure("Medium", background="#ffffcc")
        self.tree.tag_configure("Low", background="#ccffcc")
        self.tree.tag_configure("overdue", background="#ff6b6b", foreground="white", 
                               font=("Arial", 10, "bold"))
        self.tree.tag_configure("done", foreground="#999999", font=("Arial", 10, "overstrike"))

        self.status_bar.config(text=f"Tasks loaded: {len(rows)}")

    def search_tasks(self):
        keyword = self.search_var.get().lower()
        for item in self.tree.get_children():
            self.tree.delete(item)

        rows = database.get_tasks()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        for row in rows:
            task_id, task, time_, status, priority, notes, category = row
            if keyword in task.lower() or keyword in category.lower():
                tags = []
                if status == "Pending" and time_ < now:
                    tags.append("overdue")
                elif status == "Done":
                    tags.append("done")
                else:
                    tags.append(priority)

                self.tree.insert("", tk.END, values=(task_id, task, time_, status, priority, category), 
                               tags=tuple(tags))

        self.tree.tag_configure("High", background="#ffcccc")
        self.tree.tag_configure("Medium", background="#ffffcc")
        self.tree.tag_configure("Low", background="#ccffcc")
        self.tree.tag_configure("overdue", background="#ff6b6b", foreground="white")
        self.tree.tag_configure("done", foreground="#999999", font=("Arial", 10, "overstrike"))

    def mark_done(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a task")
            return

        task_id = self.tree.item(selected[0])["values"][0]
        if database.mark_done(task_id):
            self.load_tasks()
            self.status_bar.config(text="Task marked as done")

    def delete_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a task")
            return

        if not messagebox.askyesno("Confirm", "Delete this task?"):
            return

        task_id = self.tree.item(selected[0])["values"][0]
        if database.delete_task(task_id):
            self.load_tasks()
            self.status_bar.config(text="Task deleted")

    def edit_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a task")
            return

        task_id = self.tree.item(selected[0])["values"][0]
        task_data = database.get_task_by_id(task_id)

        if not task_data:
            return

        edit_win = tk.Toplevel(self.root)
        edit_win.title("Edit Task")
        edit_win.geometry("500x350")
        edit_win.transient(self.root)

        frame = ttk.Frame(edit_win, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Task:").grid(row=0, column=0, sticky="w", pady=5)
        task_e = ttk.Entry(frame, width=40)
        task_e.insert(0, task_data[0])
        task_e.grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="Date:").grid(row=1, column=0, sticky="w", pady=5)
        date_e = ttk.Entry(frame, width=40)
        date_e.insert(0, task_data[1].split()[0])
        date_e.grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Time:").grid(row=2, column=0, sticky="w", pady=5)
        time_e = ttk.Entry(frame, width=40)
        time_e.insert(0, task_data[1].split()[1])
        time_e.grid(row=2, column=1, pady=5)

        ttk.Label(frame, text="Priority:").grid(row=3, column=0, sticky="w", pady=5)
        priority_e = tk.StringVar(value=task_data[2])
        ttk.Combobox(frame, textvariable=priority_e, values=["High", "Medium", "Low"], 
                     width=37, state="readonly").grid(row=3, column=1, pady=5)

        ttk.Label(frame, text="Category:").grid(row=4, column=0, sticky="w", pady=5)
        category_e = tk.StringVar(value=task_data[4])
        ttk.Combobox(frame, textvariable=category_e, 
                     values=["General", "Work", "Personal", "Shopping", "Health", "Study"],
                     width=37, state="readonly").grid(row=4, column=1, pady=5)

        ttk.Label(frame, text="Notes:").grid(row=5, column=0, sticky="nw", pady=5)
        notes_e = tk.Text(frame, height=3, width=40)
        notes_e.insert("1.0", task_data[3] if task_data[3] else "")
        notes_e.grid(row=5, column=1, pady=5)

        def save_changes():
            new_task = task_e.get().strip()
            new_date = date_e.get().strip()
            new_time = time_e.get().strip()
            new_priority = priority_e.get()
            new_category = category_e.get()
            new_notes = notes_e.get("1.0", tk.END).strip()

            if not new_task:
                messagebox.showwarning("Warning", "Task cannot be empty")
                return

            valid, datetime_str = self.validate_datetime(new_date, new_time)
            if not valid:
                messagebox.showerror("Error", "Invalid date/time format")
                return

            if database.update_task(task_id, new_task, datetime_str, new_priority, new_notes, new_category):
                messagebox.showinfo("Success", "Task updated!")
                edit_win.destroy()
                self.load_tasks()
                self.status_bar.config(text="Task updated")
            else:
                messagebox.showerror("Error", "Failed to update task")

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="Save", command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=edit_win.destroy).pack(side=tk.LEFT, padx=5)

    def show_stats(self):
        stats = database.get_statistics()

        stats_win = tk.Toplevel(self.root)
        stats_win.title("📊 Statistics")
        stats_win.geometry("400x350")
        stats_win.transient(self.root)

        frame = ttk.Frame(stats_win, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Task Statistics", font=("Arial", 16, "bold")).pack(pady=10)

        completion_rate = (stats['done'] / max(stats['total'], 1)) * 100

        text = f"""
        Total Tasks: {stats['total']}
        Pending: {stats['pending']}
        Completed: {stats['done']}
        Completion Rate: {completion_rate:.1f}%

        Priority Breakdown:
        High: {stats['by_priority'].get('High', 0)}
        Medium: {stats['by_priority'].get('Medium', 0)}
        Low: {stats['by_priority'].get('Low', 0)}

        Category Breakdown:
        """

        for cat, count in stats['by_category'].items():
            text += f"  {cat}: {count}\n        "

        ttk.Label(frame, text=text, justify=tk.LEFT, font=("Arial", 10)).pack(pady=10)
        ttk.Button(frame, text="Close", command=stats_win.destroy).pack(pady=10)

    def export_csv(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if filename:
            if database.export_to_csv(filename):
                messagebox.showinfo("Success", f"Exported to {filename}")
                self.status_bar.config(text=f"Exported to {filename}")
            else:
                messagebox.showerror("Error", "Export failed")

    def toggle_theme(self):
        bg = self.root.cget("bg")
        if bg == "#f5f5f5":
            self.root.configure(bg="#2c2c2c")
            self.main_frame.configure(style="Dark.TFrame")
        else:
            self.root.configure(bg="#f5f5f5")
            self.main_frame.configure(style="Main.TFrame")

    def show_help(self):
        help_text = """
        Keyboard Shortcuts:

        Ctrl+N - Add new task
        Ctrl+E - Export to CSV
        Ctrl+D - Delete task
        Ctrl+S - Show statistics
        Ctrl+T - Toggle theme
        Ctrl+Q - Quit
        F5 - Refresh
        Delete - Delete task

        Double-click a task to edit it
        """
        messagebox.showinfo("Help", help_text)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Exit the application?"):
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()
