import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
from typing import List, Optional
from config import AppConfig, DatabaseConfig
from docker_manager import DockerManager
from databse import DatabaseManager
import logging
import os

class DockerStatusFrame(ctk.CTkFrame):
    def __init__(self, master, docker_config, service_name):
        super().__init__(master)
        self.docker_config = docker_config
        self.service_name = service_name
        self.docker_manager = DockerManager()  # Crear instancia del DockerManager
        
        self.logger = logging.getLogger(__name__)
        
        # Verificar existencia del archivo docker-compose
        if not os.path.exists(docker_config.compose_file):
            self.logger.error(f"No se encontró el archivo docker-compose para {service_name}")
            messagebox.showerror(
                "Error",
                f"No se encontró el archivo docker-compose para {service_name} en:\n{docker_config.compose_file}"
            )
        
        self._create_widgets()
        self.update_status()

    def _create_widgets(self):
        self.status_label = ctk.CTkLabel(self, text=f"{self.service_name} Status: Checking...")
        self.status_label.pack(side="left", padx=5)
        
        self.up_button = ctk.CTkButton(
            self,
            text="Start",
            command=self.start_service,
            width=80
        )
        self.up_button.pack(side="left", padx=5)
        
        self.down_button = ctk.CTkButton(
            self,
            text="Stop",
            command=self.stop_service,
            width=80
        )
        self.down_button.pack(side="left", padx=5)

    def start_service(self):
        try:
            success, message = self.docker_manager.docker_compose_up(self.docker_config.compose_file)
            if success:
                messagebox.showinfo("Success", message)
            else:
                messagebox.showerror("Error", message)
        except Exception as e:
            self.logger.error(f"Error starting {self.service_name}: {e}")
            messagebox.showerror("Error", f"Error starting {self.service_name}: {str(e)}")
        finally:
            self.update_status()

    def stop_service(self):
        try:
            success, message = self.docker_manager.docker_compose_down(self.docker_config.compose_file)
            if success:
                messagebox.showinfo("Success", message)
            else:
                messagebox.showerror("Error", message)
        except Exception as e:
            self.logger.error(f"Error stopping {self.service_name}: {e}")
            messagebox.showerror("Error", f"Error stopping {self.service_name}: {str(e)}")
        finally:
            self.update_status()

    def update_status(self):
        try:
            success, output = self.docker_manager.check_docker_status(self.docker_config.compose_file)
            is_running = success and "Up" in output
            
            self.status_label.configure(
                text=f"{self.service_name} Status: {'Running' if is_running else 'Stopped'}"
            )
            
            self.up_button.configure(state="normal" if not is_running else "disabled")
            self.down_button.configure(state="normal" if is_running else "disabled")
        except Exception as e:
            self.logger.error(f"Error updating status for {self.service_name}: {e}")
            self.status_label.configure(text=f"{self.service_name} Status: Error")
            self.up_button.configure(state="normal")
            self.down_button.configure(state="normal")

class DatabaseConnectionFrame(ctk.CTkFrame):
    def __init__(self, master, title: str, config: DatabaseConfig):
        super().__init__(master)
        
        ctk.CTkLabel(self, text=title, font=("Arial", 14, "bold")).pack(pady=5)
        
        self.entries = {}
        fields = [
            ("host", "Host", config.host),
            ("port", "Port", config.port),
            ("database", "Database", config.database),
            ("username", "Username", config.username),
            ("password", "Password", config.password),
            ("table_name", "Table Name", config.table_name)
        ]
        
        for field, label, default in fields:
            self.entries[field] = self.create_entry_field(label, default)

    def create_entry_field(self, label_text: str, default_value: str) -> ctk.CTkEntry:
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkLabel(frame, text=label_text, width=100).pack(side="left", padx=5)
        entry = ctk.CTkEntry(frame)
        entry.pack(side="left", fill="x", expand=True, padx=5)
        entry.insert(0, default_value)
        return entry

    def get_config(self) -> DatabaseConfig:
        return DatabaseConfig(**{
            field: entry.get()
            for field, entry in self.entries.items()
        })

class EnhancedETLApp:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("Enhanced ETL Tool with Docker")
        self.app.geometry("1200x800")
        
        self.config = AppConfig()
        self.df: Optional[pd.DataFrame] = None
        
        self.create_main_layout()
        self.app.mainloop()

    def create_main_layout(self):
        # Create notebook for tabs
        self.tabview = ctk.CTkTabview(self.app)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Create tabs
        self.tab_docker = self.tabview.add("Docker Services")
        self.tab_data = self.tabview.add("Data Preview & Transform")
        self.tab_connection = self.tabview.add("Database Connections")
        
        self.create_docker_tab()
        self.create_data_tab()
        self.create_connection_tab()

    def create_docker_tab(self):
        # Create status frames for each service
        self.pg_docker_status = DockerStatusFrame(
            self.tab_docker,
            self.config.DOCKER_CONFIGS["postgres"],
            "PostgreSQL"
        )
        self.pg_docker_status.pack(fill="x", padx=10, pady=5)
        
        self.sql_docker_status = DockerStatusFrame(
            self.tab_docker,
            self.config.DOCKER_CONFIGS["sqlserver"],
            "SQL Server"
        )
        self.sql_docker_status.pack(fill="x", padx=10, pady=5)
        
        # Add refresh button
        ctk.CTkButton(
            self.tab_docker,
            text="Refresh Status",
            command=self.refresh_docker_status
        ).pack(pady=10)

    def create_data_tab(self):
        # Split into left and right frames
        left_frame = ctk.CTkFrame(self.tab_data)
        left_frame.pack(side="left", fill="y", padx=5, pady=5)
        
        right_frame = ctk.CTkFrame(self.tab_data)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # Add data controls to left frame
        self.create_data_controls(left_frame)
        
        # Add preview to right frame
        self.create_data_preview(right_frame)

    def create_connection_tab(self):
        # Create connection frames
        self.pg_connection = DatabaseConnectionFrame(
            self.tab_connection,
            "PostgreSQL Connection",
            self.config.DEFAULT_PG_CONFIG
        )
        self.pg_connection.pack(fill="x", padx=10, pady=5)
        
        self.sql_connection = DatabaseConnectionFrame(
            self.tab_connection,
            "SQL Server Connection",
            self.config.DEFAULT_SQL_CONFIG
        )
        self.sql_connection.pack(fill="x", padx=10, pady=5)
        
        # Add action buttons
        self.create_connection_buttons()

    def create_data_controls(self, parent):
        # File selection
        ctk.CTkButton(
            parent,
            text="Select CSV File",
            command=self.select_csv
        ).pack(pady=5)
        
        self.file_info_label = ctk.CTkLabel(
            parent,
            text="No file selected",
            wraplength=200
        )
        self.file_info_label.pack(pady=5)
        
        # Column management
        ctk.CTkLabel(parent, text="Columns:").pack(pady=5)
        self.columns_listbox = ctk.CTkTextbox(parent, width=200, height=200)
        self.columns_listbox.pack(pady=5)
        
        # Data transformation buttons
        buttons = [
            ("Select Columns", self.select_columns),
            ("Remove Columns", self.remove_columns),
            ("Fill NA Values", self.fill_na_values),
            ("Drop Duplicates", self.drop_duplicates)
        ]
        
        for text, command in buttons:
            ctk.CTkButton(
                parent,
                text=text,
                command=command
            ).pack(pady=5)

    def create_data_preview(self, parent):
        # Create frame for treeview
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True)
        
        # Create scrollbars
        x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal")
        y_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
        
        # Create treeview
        self.tree = ttk.Treeview(
            tree_frame,
            xscrollcommand=x_scroll.set,
            yscrollcommand=y_scroll.set
        )
        
        # Configure scrollbars
        x_scroll.config(command=self.tree.xview)
        y_scroll.config(command=self.tree.yview)
        
        # Pack elements
        self.tree.pack(fill="both", expand=True)
        x_scroll.pack(side="bottom", fill="x")
        y_scroll.pack(side="right", fill="y")

    def create_connection_buttons(self):
        button_frame = ctk.CTkFrame(self.tab_connection)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        buttons = [
            ("Test PostgreSQL", self.test_postgres),
            ("Test SQL Server", self.test_sqlserver),
            ("Upload to PostgreSQL", self.upload_to_postgres),
            ("Migrate to SQL Server", self.migrate_to_sql_server)
        ]
        
        for text, command in buttons:
            ctk.CTkButton(
                button_frame,
                text=text,
                command=command
            ).pack(side="left", padx=5, pady=5)

    def refresh_docker_status(self):
        self.pg_docker_status.update_status()
        self.sql_docker_status.update_status()

    def select_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                self.df = pd.read_csv(file_path)
                self.file_info_label.configure(text=f"Selected file: {file_path}")
                self.update_columns_listbox()
                self.update_data_preview()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def update_columns_listbox(self):
        self.columns_listbox.delete("1.0", "end")
        for column in self.df.columns:
            self.columns_listbox.insert("end", f"{column}\n")

    def update_data_preview(self):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = list(self.df.columns)
        self.tree.heading("#0", text="Index")
        for col in self.df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, stretch=True)
        for i, row in self.df.iterrows():
            self.tree.insert("", "end", text=i, values=list(row))

    def select_columns(self):
        selected_columns = self.get_selected_columns()
        if selected_columns:
            self.df = self.df[selected_columns]
            self.update_columns_listbox()
            self.update_data_preview()

    def remove_columns(self):
        selected_columns = self.get_selected_columns()
        if selected_columns:
            existing_cols = [col for col in selected_columns if col in self.df.columns]
            self.df = self.df.drop(columns=existing_cols)
            self.update_columns_listbox()
            self.update_data_preview()

    def fill_na_values(self):
        self.df = self.df.fillna(0)
        self.update_data_preview()

    def drop_duplicates(self):
        self.df = self.df.drop_duplicates()
        self.update_data_preview()

    def get_selected_columns(self) -> List[str]:
        return [
            line.strip()
            for line in self.columns_listbox.get("1.0", "end").split("\n")
            if line.strip()
        ]
    
    def test_postgres(self):
        config = self.pg_connection.get_config()
        engine = DatabaseManager.create_postgres_engine(config)
        success, message = DatabaseManager.test_connection(engine)
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)

    def test_sqlserver(self):
        config = self.sql_connection.get_config()
        engine = DatabaseManager.create_sqlserver_engine(config)
        success, message = DatabaseManager.test_connection(engine)
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)

    def upload_to_postgres(self):
        config = self.pg_connection.get_config()
        engine = DatabaseManager.create_postgres_engine(config)
        success, message = DatabaseManager.upload_dataframe(self.df, engine, config.table_name)
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)

    def migrate_to_sql_server(self):
        config = self.sql_connection.get_config()
        engine = DatabaseManager.create_sqlserver_engine(config)
        success, message = DatabaseManager.upload_dataframe(self.df, engine, config.table_name)
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)

if __name__ == "__main__":
    app = EnhancedETLApp()
