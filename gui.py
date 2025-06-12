# src/gui.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import re
from database import init_db, get_attendance_records, add_contact
import os
import subprocess
from visualizer import create_modern_dashboard
import time
import sys


class AddPersonDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Add New Person")
        self.geometry("400x250")
        self.parent = parent  # Store parent reference

        # Validation patterns
        self.parent_phone_re = re.compile(r"^\+\d{10,15}$")
        self.email_re = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

        # Input fields and validation
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="Full Name:").grid(row=0, column=0, padx=10, pady=5)
        self.name_entry = ttk.Entry(self)
        self.name_entry.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(self, text="Mobile Number:").grid(row=1, column=0, padx=10, pady=5)
        self.parent_phone_entry = ttk.Entry(self)
        self.parent_phone_entry.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(self, text="Email Address:").grid(row=2, column=0, padx=10, pady=5)
        self.email_entry = ttk.Entry(self)
        self.email_entry.grid(row=2, column=1, padx=10, pady=5)

        ttk.Button(self, text="Start Face Capture", command=self.validate_inputs).grid(row=4, column=1, pady=10)

    def validate_inputs(self):
        name = self.name_entry.get().strip()
        parent_phone = self.parent_phone_entry.get().strip()
        email = self.email_entry.get().strip()

        # Name validation
        if not name:
            messagebox.showerror("Error", "Name is required!")
            return

        # parent_phone validation
        if not self.parent_phone_re.match(parent_phone):
            messagebox.showerror("Error",
                                 "parent_phone format Must be international format: +[country code][number]")
            return

        # Email validation
        if not self.email_re.match(email):
            messagebox.showerror("Error",
                                 "Invalid email format!\nValid example: john.doe@example.com")
            return

        # Proceed if all valid
        add_contact(name, parent_phone, email)
        time.sleep(0.5)  # Add small delay to prevent database locking
        
        # Get script paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        capture_script = os.path.join(current_dir, "capture_faces.py")
        encode_script = os.path.join(current_dir, "encode_faces.py")
        
        # Start face capture
        capture_process = subprocess.Popen([sys.executable, capture_script, name])
        messagebox.showinfo("Info", f"Face capture started for {name}!\nPress SPACE to capture images.\nPress ESC when done.")
        
        # Wait for capture process to complete
        capture_process.wait()
        
        # After capture is done, run face encoding
        if capture_process.returncode == 0:
            encode_process = subprocess.Popen([sys.executable, encode_script])
            encode_process.wait()
            if encode_process.returncode == 0:
                messagebox.showinfo("Success", f"Successfully added {name} to the system!")
            else:
                messagebox.showerror("Error", "Face encoding failed. Please try again.")
        else:
            messagebox.showerror("Error", "Face capture failed. Please try again.")
        
        self.destroy()


class AttendanceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Attendance System")
        self.geometry("800x600")
        init_db()
        self.create_widgets()

    def create_widgets(self):
        # Control buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="Add New Person", command=self.add_person).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="Start Attendance", command=self.start_attendance).grid(row=0, column=1, padx=10)
        ttk.Button(btn_frame, text="View Logs", command=self.show_logs).grid(row=0, column=2, padx=10)
        ttk.Button(btn_frame, text="Exit", command=self.quit).grid(row=0, column=3, padx=10)
        ttk.Button(btn_frame, text="View Analytics",command=self.show_analytics).grid(row=0, column=4, padx=10)


        # Logs display
        self.logs_area = scrolledtext.ScrolledText(self, width=90, height=25)
        self.logs_area.pack(pady=10)

    def show_analytics(self):
        try:
            create_modern_dashboard(self)
        except Exception as e:
            self.logs_area.insert(tk.END, f"\nChart Error: {str(e)}")

    def add_person(self):
        AddPersonDialog(self)

    def start_attendance(self):
        try:
            # Get the absolute path to attendance_system.py
            current_dir = os.path.dirname(os.path.abspath(__file__))
            attendance_script = os.path.join(current_dir, "attendance_system.py")
            
            # Use the system Python instead of venv
            subprocess.Popen([sys.executable, attendance_script])
            messagebox.showinfo("Info", "Attendance system started!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start attendance system: {str(e)}")

    def show_logs(self):
        self.logs_area.delete(1.0, tk.END)
        records = get_attendance_records()

        if not records:
            self.logs_area.insert(tk.END, "No attendance records found!")
            return

        for record in records:
            self.logs_area.insert(tk.END,
                                  f"Name: {record[0]} | Date: {record[1]} | Hour: {record[2]}\n")



if __name__ == "__main__":
    app = AttendanceApp()
    app.mainloop()