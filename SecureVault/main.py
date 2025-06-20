import os
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import tempfile
import subprocess
from cryptography.fernet import Fernet

KEY_FILE = "config/key.key"
USER_FILE = "data/users.txt"

# Generate encryption key if not present
def generate_key():
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key)

# Load the key
def load_key():
    return open(KEY_FILE, "rb").read()

if not os.path.exists("config"):
    os.makedirs("config")
if not os.path.exists("data"):
    os.makedirs("data")
if not os.path.exists("vault"):
    os.makedirs("vault")
if not os.path.exists(KEY_FILE):
    generate_key()

key = load_key()
cipher = Fernet(key)

def open_login():
    login_win = tk.Toplevel()
    login_win.title("Login")
    login_win.geometry("350x250")
    login_win.config(bg="#1e1e1e")

    tk.Label(login_win, text="Username", fg="white", bg="#1e1e1e").pack(pady=5)
    username_entry = tk.Entry(login_win)
    username_entry.pack()

    tk.Label(login_win, text="Password", fg="white", bg="#1e1e1e").pack(pady=5)
    password_entry = tk.Entry(login_win, show="*")
    password_entry.pack()

    def login():
        username = username_entry.get()
        password = password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "All fields are required")
            return

        try:
            with open(USER_FILE, "r") as f:
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) != 3:
                        continue

                    saved_user, encrypted_pw, encrypted_pin = parts
                    if username == saved_user:
                        decrypted_pw = cipher.decrypt(encrypted_pw.encode()).decode()
                        decrypted_pin = cipher.decrypt(encrypted_pin.encode()).decode()

                        if password != decrypted_pw:
                            messagebox.showerror("Error", "Incorrect password")
                            return

                        entered_pin = simpledialog.askstring("PIN Required", "Enter your 4-digit PIN", show="*")
                        if entered_pin == decrypted_pin:
                            messagebox.showinfo("Success", "Login Successful!")
                            login_win.destroy()
                            vault_dashboard(username)
                            return
                        else:
                            messagebox.showerror("Error", "Incorrect PIN")
                            return

            messagebox.showerror("Error", "Username not found")
        except FileNotFoundError:
            messagebox.showerror("Error", "No users registered yet!")

    tk.Button(login_win, text="Login", bg="blue", fg="white", command=login).pack(pady=15)

def vault_dashboard(username):
    dash = tk.Toplevel()
    dash.title("SecureVault - Dashboard")
    dash.geometry("500x450")
    dash.config(bg="#1e1e1e")

    tk.Label(dash, text=f"Welcome, {username}", fg="white", bg="#1e1e1e", font=("Arial", 16)).pack(pady=10)
    
    file_listbox = tk.Listbox(dash, width=60)
    file_listbox.pack(pady=10)

    def refresh_files():
        file_listbox.delete(0, tk.END)
        for file in os.listdir("vault"):
            if file.endswith(".vault"):
                clean_name = file.replace(".vault", "")
                file_listbox.insert(tk.END, clean_name)

    def upload_file():
        filepath = filedialog.askopenfilename()
        if filepath:
            with open(filepath, "rb") as f:
                data = f.read()
            encrypted = cipher.encrypt(data)
            filename = os.path.basename(filepath)
            with open(f"vault/{filename}.vault", "wb") as f:
                f.write(encrypted)
            messagebox.showinfo("Success", f"{filename} encrypted and stored!")
            refresh_files()

    def decrypt_and_open():
        selected = file_listbox.get(tk.ACTIVE)
        if not selected:
            messagebox.showerror("Error", "No file selected!")
            return

        vault_file = f"vault/{selected}.vault"
        if not os.path.exists(vault_file):
            messagebox.showerror("Error", f"{vault_file} not found!")
            return

        try:
            with open(vault_file, "rb") as f:
                encrypted = f.read()

            decrypted = cipher.decrypt(encrypted)

            # Save to a temporary file with the original name (without .vault)
            original_filename = selected  # selected doesn't have .vault
            temp_path = os.path.join(tempfile.gettempdir(), original_filename)

            with open(temp_path, "wb") as f:
                f.write(decrypted)

            # Open the file using default app
            os.startfile(temp_path)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to decrypt/open file:\n{e}")

    def logout():
        dash.destroy()

    tk.Button(dash, text="Upload File", bg="#4CAF50", fg="white", command=upload_file).pack(pady=5)
    tk.Button(dash, text="Decrypt & Open", bg="#2196F3", fg="white", command=decrypt_and_open).pack(pady=5)
    tk.Button(dash, text="Refresh Files", bg="#666666", fg="white", command=refresh_files).pack(pady=5)
    tk.Button(dash, text="Logout", bg="#f44336", fg="white", command=logout).pack(pady=5)

    refresh_files()

def open_signup():
    signup_win = tk.Toplevel()
    signup_win.title("Signup")
    signup_win.geometry("350x250")
    signup_win.config(bg="#1e1e1e")

    tk.Label(signup_win, text="Username", fg="white", bg="#1e1e1e").pack(pady=5)
    username_entry = tk.Entry(signup_win)
    username_entry.pack()

    tk.Label(signup_win, text="Password", fg="white", bg="#1e1e1e").pack(pady=5)
    password_entry = tk.Entry(signup_win, show="*")
    password_entry.pack()

    def register():
        username = username_entry.get()
        password = password_entry.get()

        pin = simpledialog.askstring("Set PIN", "Enter 4-digit PIN", show="*")
        if not pin or len(pin) != 4 or not pin.isdigit():
            messagebox.showerror("Error", "PIN must be 4 digits")
            return

        if not username or not password:
            messagebox.showerror("Error", "All fields are required")
            return

        encrypted_pw = cipher.encrypt(password.encode())
        encrypted_pin = cipher.encrypt(pin.encode())

        with open(USER_FILE, "a") as f:
            f.write(f"{username},{encrypted_pw.decode()},{encrypted_pin.decode()}\n")

        messagebox.showinfo("Success", "Signup successful!")
        signup_win.destroy()

    tk.Button(signup_win, text="Register", bg="green", fg="white", command=register).pack(pady=15)

root = tk.Tk()
root.title("SecureVault - File Locker")
root.geometry("400x300")
root.config(bg="#121212")

title = tk.Label(root, text="🔐 SecureVault", font=("Arial", 20, "bold"), bg="#121212", fg="white")
title.pack(pady=30)

login_btn = tk.Button(root, text="Login", font=("Arial", 14), command=open_login, bg="#4CAF50", fg="white", width=20)
login_btn.pack(pady=10)

signup_btn = tk.Button(root, text="Signup", font=("Arial", 14), command=open_signup, bg="#2196F3", fg="white", width=20)
signup_btn.pack(pady=10)

root.mainloop()
