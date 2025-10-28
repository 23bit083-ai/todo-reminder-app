# main.py
# GUI and main app logic

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import database
import reminder

class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📝 To-Do Reminder App")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        self.root.eval('tk::PlaceWindow . center')
        self.root.configure(bg="#f5f5f5")

        # Custom theme styling
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"))
        style.configure("TButton", font=("Arial", 10), padding=5)
        style.configure("TLabel", background="#f5f5f5", font=("Arial", 11))

        ttk.Label(root, text="📋 To-Do Reminder App", font=("Helvetica", 20, "bold"), background="#f5f5f5").pack(pady=10)

        # --- Task Entry Section ---
        entry_frame = ttk.Frame(root)
        entry_frame.pack(pady=5)

        ttk.Label(entry_frame, text="Task:").grid(row=0, column=0, padx=5)
        self.task_entry = ttk.Entry(entry_frame, width=35)
        self.task_entry.grid(row=0, column=1, padx=5)

        ttk.Label(entry_frame, text="Time (YYYY-MM-DD HH:MM):").grid(row=1, column=0, padx=5)
        self.time_entry = ttk.Entry(entry_frame, width=35)
        self.time_entry.grid(row=1, column=1, padx=5)

        ttk.Label(entry_frame, text="Priority:").grid(row=2, column=0, padx=5)
        self.priority = tk.StringVar(value="Medium")
        ttk.Combobox(entry_frame, textvariable=self.priority, values=["High", "Medium", "Low"], width=32).grid(row=2, column=1, padx=5)

        # --- Buttons ---
        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Add Task", command=self.add_task).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Edit Task", command=self.edit_task).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Mark Done", command=self.mark_done).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_task).grid(row=0, column=3, padx=5)
        ttk.Button(btn_frame, text="Dark Mode", command=self.toggle_theme).grid(row=0, column=4, padx=5)

        # --- Filter + Search Section ---
        filter_frame = ttk.Frame(root)
        filter_frame.pack(pady=5)

        ttk.Label(filter_frame, text="Filter:").grid(row=0, column=0, padx=5)
        self.filter_var = tk.StringVar(value="All")
        ttk.Combobox(filter_frame, textvariable=self.filter_var, values=["All", "Pending", "Done", "High Priority"], width=15).grid(row=0, column=1, padx=5)
        ttk.Button(filter_frame, text="Apply", command=self.load_tasks).grid(row=0, column=2, padx=5)

        ttk.Label(filter_frame, text="Search:").grid(row=0, column=3, padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=25)
        search_entry.grid(row=0, column=4, padx=5)
        search_entry.bind("<KeyRelease>", lambda e: self.filter_tasks())

        # --- Treeview ---
        self.tree = ttk.Treeview(root, columns=("Task", "Time", "Status", "Priority"), show="headings", height=12)
        for col in ("Task", "Time", "Status", "Priority"):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=180, anchor="center")
        self.tree.pack(pady=10, fill=tk.BOTH, expand=True)

        self.load_tasks()
        reminder.start_reminder_thread()

    # --- Functions ---
    def add_task(self):
        task = self.task_entry.get()
        reminder_time = self.time_entry.get()
        priority = self.priority.get()
        if not task or not reminder_time:
            messagebox.showwarning("Warning", "Enter all fields")
            return
        try:
            datetime.datetime.strptime(reminder_time, "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Error", "Invalid time format!")
            return
        database.add_task(task, reminder_time, priority)
        self.load_tasks()

    def load_tasks(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        rows = database.get_tasks()
        filter_type = self.filter_var.get()

        for row in rows:
            task, time_, status, priority = row
            if filter_type == "Pending" and status != "Pending":
                continue
            elif filter_type == "Done" and status != "Done":
                continue
            elif filter_type == "High Priority" and priority != "High":
                continue

            tag = "high" if priority == "High" else "low" if priority == "Low" else "med"
            self.tree.insert("", tk.END, values=row, tags=(tag,))

        self.tree.tag_configure("high", background="#ffcccc")
        self.tree.tag_configure("med", background="#ffffcc")
        self.tree.tag_configure("low", background="#ccffcc")

    def mark_done(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a task to mark done.")
            return
        task = self.tree.item(selected[0])["values"][0]
        database.mark_done(task)
        self.load_tasks()

    def delete_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a task to delete.")
            return
        task = self.tree.item(selected[0])["values"][0]
        database.delete_task(task)
        self.load_tasks()

    def edit_task(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select a task to edit.")
            return
        old_task = self.tree.item(selected[0])["values"][0]
        new_task = self.task_entry.get()
        new_time = self.time_entry.get()
        if not new_task or not new_time:
            messagebox.showwarning("Warning", "Fill new task and time.")
            return
        database.update_task(old_task, new_task, new_time)
        self.load_tasks()

    def filter_tasks(self):
        keyword = self.search_var.get().lower()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in database.get_tasks():
            if keyword in row[0].lower():
                tag = "high" if row[3] == "High" else "low" if row[3] == "Low" else "med"
                self.tree.insert("", tk.END, values=row, tags=(tag,))
        self.tree.tag_configure("high", background="#ffcccc")
        self.tree.tag_configure("med", background="#ffffcc")
        self.tree.tag_configure("low", background="#ccffcc")

    def toggle_theme(self):
        bg = self.root.cget("bg")
        if bg == "#f5f5f5":
            self.root.configure(bg="#2c2c2c")
        else:
            self.root.configure(bg="#f5f5f5")


if __name__ == "__main__":
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()
