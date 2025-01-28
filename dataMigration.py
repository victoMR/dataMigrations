import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
from sqlalchemy import create_engine

class DataMigrationApp:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("CSV to Database Migration Tool")
        self.app.geometry("500x500")

        self.csv_file_path = None
        
        # UI Elements
        self.create_widgets()
        self.app.mainloop()

    def create_widgets(self):
        ctk.CTkLabel(self.app, text="CSV to PostgreSQL and SQL Server Migration", font=("Arial", 18)).pack(pady=20)

        # Button to select CSV
        self.csv_button = ctk.CTkButton(self.app, text="Select CSV File", command=self.select_csv)
        self.csv_button.pack(pady=10)

        # Input fields for PostgreSQL
        self.pg_label = ctk.CTkLabel(self.app, text="PostgreSQL Connection Details")
        self.pg_label.pack(pady=5)

        self.pg_host_entry = ctk.CTkEntry(self.app, placeholder_text="Host (e.g., 127.0.0.1)")
        self.pg_host_entry.insert(0, "127.0.0.1")
        self.pg_host_entry.pack(pady=5)

        self.pg_port_entry = ctk.CTkEntry(self.app, placeholder_text="Port (default: 5433)")
        self.pg_port_entry.insert(0, "5433")
        self.pg_port_entry.pack(pady=5)

        self.pg_db_entry = ctk.CTkEntry(self.app, placeholder_text="Database Name")
        self.pg_db_entry.insert(0, "anime_list")
        self.pg_db_entry.pack(pady=5)

        self.pg_user_entry = ctk.CTkEntry(self.app, placeholder_text="Username")
        self.pg_user_entry.insert(0, "my_user")
        self.pg_user_entry.pack(pady=5)

        self.pg_pass_entry = ctk.CTkEntry(self.app, placeholder_text="Password", show="*")
        self.pg_pass_entry.insert(0, "Batmanlol1")
        self.pg_pass_entry.pack(pady=5)

        # Button to upload CSV to PostgreSQL
        self.pg_button = ctk.CTkButton(self.app, text="Upload CSV to PostgreSQL", command=self.upload_to_postgres)
        self.pg_button.pack(pady=10)

        # Button to migrate data to SQL Server
        self.sqlserver_button = ctk.CTkButton(self.app, text="Migrate Data to SQL Server", command=self.migrate_to_sql_server)
        self.sqlserver_button.pack(pady=10)

    def select_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.csv_file_path = file_path
            messagebox.showinfo("File Selected", f"Selected file: {file_path}")

    def upload_to_postgres(self):
        if not self.csv_file_path:
            messagebox.showerror("Error", "Please select a CSV file first.")
            return

        host = self.pg_host_entry.get() or "127.0.0.1"
        port = self.pg_port_entry.get() or "5433"
        db = self.pg_db_entry.get()
        user = self.pg_user_entry.get()
        password = self.pg_pass_entry.get()

        if not (db and user and password):
            messagebox.showerror("Error", "Please fill in all PostgreSQL connection fields.")
            return

        try:
            # Create PostgreSQL connection
            engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')

            # Load CSV and write to PostgreSQL
            df = pd.read_csv(self.csv_file_path)
            table_name = "anime_list"
            df.to_sql(table_name, engine, if_exists='replace', index=False)

            messagebox.showinfo("Success", f"Data successfully uploaded to PostgreSQL table '{table_name}'.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload data: {e}")

    def migrate_to_sql_server(self):
        try:
            # SQL Server connection details
            host = "127.0.0.1"
            port = "1433"
            db = "TestDB"
            user = "sa"
            password = "Batmanlol1"

            pg_host = self.pg_host_entry.get() or "127.0.0.1"
            pg_port = self.pg_port_entry.get() or "5433"
            pg_db = self.pg_db_entry.get()
            pg_user = self.pg_user_entry.get()
            pg_password = self.pg_pass_entry.get()

            if not (pg_db and pg_user and pg_password):
                messagebox.showerror("Error", "Please fill in PostgreSQL connection fields.")
                return

            # Connect to PostgreSQL
            pg_engine = create_engine(f'postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}')
            df = pd.read_sql_table("anime_list", pg_engine)

            # Connect to SQL Server
            sqlserver_engine = create_engine(f'mssql+pymssql://{user}:{password}@{host}:{port}/{db}')
            df.to_sql("anime_list", sqlserver_engine, if_exists='replace', index=False)

            messagebox.showinfo("Success", "Data successfully migrated to SQL Server.")
        except Exception as e:
            messagebox.showerror("Error", f"Migration failed: {e}")

if __name__ == "__main__":
    DataMigrationApp()
