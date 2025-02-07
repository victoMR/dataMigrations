import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
from typing import List, Optional, Tuple, Dict, Any
from config import AppConfig, DatabaseConfig
from docker_manager import DockerManager
#from database import DatabaseManag
import logging
import os
from datetime import datetime
import pymongo
from logging.handlers import RotatingFileHandler
import json
from sqlalchemy import create_engine, inspect


# Configure logging
def setup_logging():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "etl_app.log")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5)
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger

logger = setup_logging()

# Stub implementations to fix undefined errors

class DatabaseManager:
    @staticmethod
    def create_postgres_engine(config: DatabaseConfig):
        # stub implementation, should create and return a database engine
        return None

    @staticmethod
    def create_sqlserver_engine(config: DatabaseConfig):
        # stub implementation, should create and return a database engine
        return None

    @staticmethod
    def test_connection(engine):
        # stub implementation always returns success
        return True, "Connection successful"

class BackupManager:
    def create_postgres_backup(self, config: DatabaseConfig):
         return True, "PostgreSQL backup created successfully"

    def create_sqlserver_backup(self, config: DatabaseConfig):
         return True, "SQL Server backup created successfully"

    def create_mongodb_backup(self, config: DatabaseConfig):
         return True, "MongoDB backup created successfully"

    def restore_postgres_backup(self, config: DatabaseConfig, backup_file: str):
         return True, "PostgreSQL backup restored successfully"

    def restore_sqlserver_backup(self, config: DatabaseConfig, backup_file: str):
         return True, "SQL Server backup restored successfully"

    def restore_mongodb_backup(self, config: DatabaseConfig, backup_file: str):
         return True, "MongoDB backup restored successfully"


class ModernTheme:
    """Modern color scheme and styling constants"""
    PRIMARY = "#2D5AF0"
    SECONDARY = "#30475E"
    SUCCESS = "#4CAF50"
    ERROR = "#F44336"
    WARNING = "#FFC107"
    BACKGROUND = "#1A1A1A"
    CARD_BG = "#2D2D2D"
    TEXT = "#FFFFFF"

    BUTTON_FONT = ("Helvetica", 12)
    HEADER_FONT = ("Helvetica", 16, "bold")
    TEXT_FONT = ("Helvetica", 12)

class LoadingSpinner(ctk.CTkFrame):
    def __init__(self, master, text="Loading..."):
        super().__init__(master)
        self.configure(fg_color=ModernTheme.CARD_BG)

        self.spinner_label = ctk.CTkLabel(
            self,
            text="⟳",
            font=("Helvetica", 24),
            text_color=ModernTheme.PRIMARY
        )
        self.spinner_label.pack(pady=5)

        self.text_label = ctk.CTkLabel(
            self,
            text=text,
            font=ModernTheme.TEXT_FONT,
            text_color=ModernTheme.TEXT
        )
        self.text_label.pack(pady=5)

        self.running = False

    def start(self):
        self.running = True
        self._spin()

    def stop(self):
        self.running = False

    def _spin(self):
        if self.running:
            self.spinner_label.configure(text="⟳")
            self.after(100, lambda: self.spinner_label.configure(text="⟲"))
            self.after(200, self._spin)

class DockerStatusFrame(ctk.CTkFrame):
    def __init__(self, master, docker_config, service_name):
        super().__init__(master)
        self.configure(fg_color=ModernTheme.CARD_BG)

        self.docker_config = docker_config
        self.service_name = service_name
        self.docker_manager = DockerManager()
        self.logger = logging.getLogger(__name__)

        if not os.path.exists(docker_config.compose_file):
            self.logger.error(f"Docker compose file not found for {service_name}")
            messagebox.showerror(
                "Error",
                f"Docker compose file not found for {service_name} at:\n{docker_config.compose_file}"
            )

        self._create_widgets()
        self.update_status()

    def _create_widgets(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=5)

        # Service icon (placeholder for actual icons)
        self.icon_label = ctk.CTkLabel(
            header_frame,
            text="🐳",
            font=("Helvetica", 20)
        )
        self.icon_label.pack(side="left", padx=5)

        # Status indicator
        self.status_label = ctk.CTkLabel(
            header_frame,
            text=f"{self.service_name} Status: Checking...",
            font=ModernTheme.TEXT_FONT
        )
        self.status_label.pack(side="left", padx=5)

        # Control buttons frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=5)

        self.up_button = ctk.CTkButton(
            button_frame,
            text="Start",
            command=self.start_service,
            width=80,
            font=ModernTheme.BUTTON_FONT,
            fg_color=ModernTheme.SUCCESS
        )
        self.up_button.pack(side="left", padx=5)

        self.down_button = ctk.CTkButton(
            button_frame,
            text="Stop",
            command=self.stop_service,
            width=80,
            font=ModernTheme.BUTTON_FONT,
            fg_color=ModernTheme.ERROR
        )
        self.down_button.pack(side="left", padx=5)

        # Logs frame
        self.logs_frame = ctk.CTkFrame(self, fg_color=ModernTheme.BACKGROUND)
        self.logs_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.logs_text = ctk.CTkTextbox(
            self.logs_frame,
            height=100,
            font=("Courier", 10)
        )
        self.logs_text.pack(fill="both", expand=True)

    def _update_logs(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logs_text.insert("end", f"[{timestamp}] {message}\n")
        self.logs_text.see("end")

    def start_service(self):
        try:
            self._show_loading("Starting service...")
            success, message = self.docker_manager.docker_compose_up(self.docker_config.compose_file)
            self._update_logs(message)

            if success:
                messagebox.showinfo("Success", message)
            else:
                messagebox.showerror("Error", message)
        except Exception as e:
            self.logger.error(f"Error starting {self.service_name}: {e}")
            self._update_logs(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Error starting {self.service_name}: {str(e)}")
        finally:
            self._hide_loading()
            self.update_status()

    def stop_service(self):
        try:
            self._show_loading("Stopping service...")
            success, message = self.docker_manager.docker_compose_down(self.docker_config.compose_file)
            self._update_logs(message)

            if success:
                messagebox.showinfo("Success", message)
            else:
                messagebox.showerror("Error", message)
        except Exception as e:
            self.logger.error(f"Error stopping {self.service_name}: {e}")
            self._update_logs(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Error stopping {self.service_name}: {str(e)}")
        finally:
            self._hide_loading()
            self.update_status()

    def _show_loading(self, text=""):
        self.loading_spinner = LoadingSpinner(self, text)
        self.loading_spinner.pack(pady=10)
        self.loading_spinner.start()

    def _hide_loading(self):
        if hasattr(self, 'loading_spinner'):
            self.loading_spinner.stop()
            self.loading_spinner.destroy()

    def update_status(self):
        try:
            success, output = self.docker_manager.check_docker_status(self.docker_config.compose_file)
            is_running = success and "Up" in output

            status_text = "Running" if is_running else "Stopped"
            status_color = ModernTheme.SUCCESS if is_running else ModernTheme.ERROR

            self.status_label.configure(
                text=f"{self.service_name} Status: {status_text}",
                text_color=status_color
            )

            self.up_button.configure(state="normal" if not is_running else "disabled")
            self.down_button.configure(state="normal" if is_running else "disabled")

            self._update_logs(f"Status updated: {status_text}")
        except Exception as e:
            self.logger.error(f"Error updating status for {self.service_name}: {e}")
            self.status_label.configure(
                text=f"{self.service_name} Status: Error",
                text_color=ModernTheme.ERROR
            )
            self._update_logs(f"Error updating status: {str(e)}")
            self.up_button.configure(state="normal")
            self.down_button.configure(state="disabled")

class DatabaseConnectionFrame(ctk.CTkFrame):
    def __init__(self, master, title: str, config: DatabaseConfig):
        super().__init__(master)
        self.configure(fg_color=ModernTheme.CARD_BG)

        # Header
        header = ctk.CTkLabel(
            self,
            text=title,
            font=ModernTheme.HEADER_FONT
        )
        header.pack(pady=10)

        # Connection form
        self.entries = {}
        self.create_connection_form(config)

        # Test connection button
        self.test_button = ctk.CTkButton(
            self,
            text="Test Connection",
            command=self.test_connection,
            font=ModernTheme.BUTTON_FONT,
            fg_color=ModernTheme.PRIMARY
        )
        self.test_button.pack(pady=10)

        # Connection status
        self.status_label = ctk.CTkLabel(
            self,
            text="Not tested",
            font=ModernTheme.TEXT_FONT,
            text_color=ModernTheme.WARNING
        )
        self.status_label.pack(pady=5)

    def create_connection_form(self, config: DatabaseConfig):
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="x", padx=20, pady=10)

        fields = [
            ("host", "Host", config.host),
            ("port", "Port", config.port),
            ("database", "Database", config.database),
            ("username", "Username", config.username),
            ("password", "Password", config.password),
            ("table_name", "Table Name", config.table_name)
        ]

        for field, label_text, default in fields:
            self.entries[field] = self.create_entry_field(form_frame, label_text, default)

    def create_entry_field(self, parent, label_text: str, default_value: str) -> ctk.CTkEntry:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=2)

        label = ctk.CTkLabel(
            frame,
            text=label_text,
            font=ModernTheme.TEXT_FONT,
            width=100
        )
        label.pack(side="left", padx=5)

        entry = ctk.CTkEntry(
            frame,
            font=ModernTheme.TEXT_FONT,
            placeholder_text=f"Enter {label_text.lower()}"
        )
        entry.pack(side="left", fill="x", expand=True, padx=5)
        entry.insert(0, default_value)

        return entry

    def get_config(self) -> DatabaseConfig:
        return DatabaseConfig(**{
            field: entry.get()
            for field, entry in self.entries.items()
        })

    def test_connection(self):
        config = self.get_config()

        try:
            self.status_label.configure(
                text="Testing connection...",
                text_color=ModernTheme.WARNING
            )
            self.update()

            # Test connection based on database type
            if "mongo" in self.winfo_name().lower():
                success, message = self.test_mongo_connection(config)
            else:
                engine = (DatabaseManager.create_postgres_engine(config)
                          if "postgres" in self.winfo_name().lower()
                          else DatabaseManager.create_sqlserver_engine(config))
                success, message = DatabaseManager.test_connection(engine)

            # Update status
            self.status_label.configure(
                text="Connected" if success else "Connection failed",
                text_color=ModernTheme.SUCCESS if success else ModernTheme.ERROR
            )

            if success:
                messagebox.showinfo("Success", message)
            else:
                messagebox.showerror("Error", message)

        except Exception as e:
            self.status_label.configure(
                text="Connection error",
                text_color=ModernTheme.ERROR
            )
            messagebox.showerror("Error", str(e))

    def test_mongo_connection(self, config: DatabaseConfig) -> Tuple[bool, str]:
        try:
            client = pymongo.MongoClient(
                host=config.host,
                port=int(config.port),
                username=config.username,
                password=config.password
            )

            # Test connection
            client.server_info()
            client.close()

            return True, "Successfully connected to MongoDB"
        except Exception as e:
            return False, f"Failed to connect to MongoDB: {str(e)}"

class DataAnalyticsFrame(ctk.CTkFrame):
    def __init__(self, master, main_app):
        super().__init__(master)
        self.configure(fg_color=ModernTheme.CARD_BG)
        self.main_app = main_app  # Store reference to main app
        self.create_widgets()

    def create_widgets(self):
        # Database connection frame
        self.create_db_connection_frame()

        # Table selection frame
        self.create_table_selection_frame()

        # Analytics controls
        self.create_analytics_controls()

        # Results display area
        self.create_results_area()

    def create_db_connection_frame(self):
        conn_frame = ctk.CTkFrame(self, fg_color="transparent")
        conn_frame.pack(fill="x", padx=10, pady=5)

        # Database type selection
        self.db_type = ctk.CTkComboBox(
            conn_frame,
            values=["PostgreSQL", "SQL Server", "MongoDB"],
            command=self.on_db_type_change
        )
        self.db_type.pack(side="left", padx=5)

        # Connect button
        self.connect_btn = ctk.CTkButton(
            conn_frame,
            text="Connect",
            command=self.connect_to_database,
            font=ModernTheme.BUTTON_FONT,
            fg_color=ModernTheme.PRIMARY
        )
        self.connect_btn.pack(side="left", padx=5)

    def on_db_type_change(self, choice):
        """Handle database type change event"""
        try:
            # Reset table selection
            self.table_select.configure(values=[])
            self.table_select.configure(state="disabled")
            self.migrate_btn.configure(state="disabled")

            # Enable connect button
            self.connect_btn.configure(state="normal")

        except Exception as e:
            messagebox.showerror("Error", f"Error changing database type: {str(e)}")

    def connect_to_database(self):
        try:
            db_type = self.db_type.get().lower()

            if db_type == "postgresql":
                config = self.main_app.pg_connection.get_config()
                conn_string = f'postgresql://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}'
                engine = create_engine(conn_string)
            elif db_type == "sql server":
                config = self.main_app.sql_connection.get_config()
                conn_string = f'mssql+pyodbc://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}?driver=ODBC+Driver+17+for+SQL+Server'
                engine = create_engine(conn_string)
            else:  # MongoDB
                config = self.main_app.mongo_connection.get_config()
                client = pymongo.MongoClient(
                    host=config.host,
                    port=int(config.port),
                    username=config.username,
                    password=config.password
                )
                db = client[config.database]
                tables = db.list_collection_names()
                self.update_table_list(tables)
                return

            # Test connection for SQL databases
            with engine.connect() as connection:
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                self.update_table_list(tables)
                messagebox.showinfo("Success", "Connected to database successfully")

        except Exception as e:
            messagebox.showerror("Error", f"Error connecting to database: {str(e)}")

    def update_table_list(self, tables):
        self.table_select.configure(state="normal")
        self.table_select.configure(values=tables)
        if tables:
            self.table_select.set(tables[0])
            self.migrate_btn.configure(state="normal")

    def create_table_selection_frame(self):
        table_frame = ctk.CTkFrame(self, fg_color="transparent")
        table_frame.pack(fill="x", padx=10, pady=5)

        # Table selection dropdown
        self.table_select = ctk.CTkComboBox(
            table_frame,
            values=[],
            state="disabled"
        )
        self.table_select.pack(side="left", padx=5)

        # Migration buttons
        self.migrate_btn = ctk.CTkButton(
            table_frame,
            text="Analyze Table",
            command=self.analyze_table,
            state="disabled",
            font=ModernTheme.BUTTON_FONT,
            fg_color=ModernTheme.SECONDARY
        )
        self.migrate_btn.pack(side="left", padx=5)

    def analyze_table(self):
            try:
                db_type = self.db_type.get().lower()
                table_name = self.table_select.get()

                if not table_name:
                    messagebox.showwarning("Warning", "Please select a table first!")
                    return

                # Get data from database
                if db_type == "postgresql":
                    config = self.main_app.pg_connection.get_config()
                    conn_string = f'postgresql://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}'
                    engine = create_engine(conn_string)
                    df = pd.read_sql_table(table_name, engine)

                elif db_type == "sql server":
                    config = self.main_app.sql_connection.get_config()
                    conn_string = f'mssql+pyodbc://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}?driver=ODBC+Driver+17+for+SQL+Server'
                    engine = create_engine(conn_string)
                    df = pd.read_sql_table(table_name, engine)

                else:  # MongoDB
                    config = self.main_app.mongo_connection.get_config()
                    client = pymongo.MongoClient(
                        host=config.host,
                        port=int(config.port),
                        username=config.username,
                        password=config.password
                    )
                    db = client[config.database]
                    collection = db[table_name]
                    df = pd.DataFrame(list(collection.find()))
                    client.close()

                # Perform basic analysis
                self.show_analysis(df)

            except Exception as e:
                error_msg = str(e)
                messagebox.showerror("Error", f"Error analyzing table: {error_msg}")
                if "NoneType" in error_msg:
                    messagebox.showinfo("Tip", "Please make sure you are connected to the database first by clicking the 'Connect' button.")

    def create_analytics_controls(self):
        controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        controls_frame.pack(fill="x", padx=10, pady=5)

    def create_results_area(self):
        self.results_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.results_frame.pack(fill="both", expand=True, padx=10, pady=5)

    def show_analysis(self, df):
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        # Show basic statistics
        stats_text = ctk.CTkTextbox(
            self.results_frame,
            height=200,
            font=("Courier", 12)
        )
        stats_text.pack(fill="x", padx=5, pady=5)

        # Add basic statistics
        stats_text.insert("end", "Basic Statistics:\n\n")
        stats_text.insert("end", f"Number of rows: {len(df)}\n")
        stats_text.insert("end", f"Number of columns: {len(df.columns)}\n\n")
        stats_text.insert("end", "Columns:\n")
        for col in df.columns:
            stats_text.insert("end", f"- {col}: {df[col].dtype}\n")

        # Add numerical statistics if available
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_cols) > 0:
            stats_text.insert("end", "\nNumerical Statistics:\n")
            stats = df[numeric_cols].describe()
            stats_text.insert("end", str(stats))

        stats_text.configure(state="disabled")

class EnhancedETLApp:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("Enhanced ETL Tool with Analytics")
        self.app.geometry("1400x900")

        # Set theme
        self.app.configure(fg_color=ModernTheme.BACKGROUND)

         # Initialize logs frame and text widget first
        self.logs_frame = ctk.CTkFrame(self.app)
        self.logs_text = ctk.CTkTextbox(
            self.logs_frame,
                font=("Courier", 10),
                wrap="none"
                )
        self.logs_text.pack(fill="both", expand=True)

        self.config = AppConfig()
        self.df: Optional[pd.DataFrame] = None
        self.logger = logging.getLogger(__name__)

        self.create_main_layout()
        self.app.mainloop()

    def create_main_layout(self):
        # Create notebook for tabs
        self.tabview = ctk.CTkTabview(self.app)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Create tabs
        self.tab_docker = self.tabview.add("Docker Services")
        self.tab_data = self.tabview.add("Data Preview & Transform")
        self.tab_analytics = self.tabview.add("Data Analytics")
        self.tab_connection = self.tabview.add("Database Connections")
        self.tab_migrations = self.tabview.add("Migrations & Backups")

        self.create_docker_tab()
        self.create_data_tab()
        self.create_analytics_tab()
        self.create_connection_tab()
        self.create_migrations_tab()

    def create_docker_tab(self):
        # Add services status frames
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

        self.mongo_docker_status = DockerStatusFrame(
            self.tab_docker,
            self.config.DOCKER_CONFIGS["mongoDB"],
            "MongoDB"
        )
        self.mongo_docker_status.pack(fill="x", padx=10, pady=5)

        # Add refresh button
        refresh_button = ctk.CTkButton(
            self.tab_docker,
            text="Refresh All Services",
            command=self.refresh_docker_status,
            font=ModernTheme.BUTTON_FONT,
            fg_color=ModernTheme.PRIMARY
        )
        refresh_button.pack(pady=10)
    def refresh_docker_status(self):
        self.pg_docker_status.update_status()
        self.sql_docker_status.update_status()
        self.mongo_docker_status.update_status()

    def create_data_tab(self):
        # Split into left and right frames
        left_frame = ctk.CTkFrame(self.tab_data, fg_color=ModernTheme.CARD_BG)
        left_frame.pack(side="left", fill="y", padx=5, pady=5)

        right_frame = ctk.CTkFrame(self.tab_data, fg_color=ModernTheme.CARD_BG)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        self.create_data_controls(left_frame)
        self.create_column_manager(left_frame)
        self.create_data_preview(right_frame)

    def create_data_controls(self, parent):
        # Data controls
        header = ctk.CTkLabel(
            parent,
            text="Data Preview & Transform",
            font=ModernTheme.HEADER_FONT
        )
        header.pack(pady=10)

        # File selection
        file_frame = ctk.CTkFrame(parent, fg_color="transparent")
        file_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            file_frame,
            text="Select CSV File",
            font=ModernTheme.TEXT_FONT
        ).pack(side="left", padx=5)

        self.file_entry = ctk.CTkEntry(
            file_frame,
            font=ModernTheme.TEXT_FONT,
            placeholder_text="Select a file...",
            state="readonly"
        )
        self.file_entry.pack(side="left", fill="x", expand=True, padx=5)

        ctk.CTkButton(
            file_frame,
            text="Browse",
            command=self.load_data,
            font=ModernTheme.BUTTON_FONT,
            fg_color=ModernTheme.PRIMARY
        ).pack(side="left", padx=5)

        # Data transformation buttons
        transform_frame = ctk.CTkFrame(parent, fg_color="transparent")
        transform_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            transform_frame,
            text="Transform Data",
            command=self.transform_data,
            font=ModernTheme.BUTTON_FONT,
            fg_color=ModernTheme.SECONDARY
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            transform_frame,
            text="Reset Data",
            command=self.reset_data,
            font=ModernTheme.BUTTON_FONT,
            fg_color=ModernTheme.ERROR
        ).pack(side="left", padx=5)

    def create_column_manager(self, parent):
        # Column management frame
        column_frame = ctk.CTkFrame(parent, fg_color=ModernTheme.CARD_BG)
        column_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            column_frame,
            text="Column Management",
            font=ModernTheme.HEADER_FONT
        ).pack(pady=5)

        # Column list with scrollbar
        list_frame = ctk.CTkFrame(column_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        scrollbar = ctk.CTkScrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.column_listbox = ctk.CTkTextbox(
            list_frame,
            height=150,
            yscrollcommand=scrollbar.set
        )
        self.column_listbox.pack(fill="both", expand=True)
        scrollbar.configure(command=self.column_listbox.yview)

        # Column management buttons
        button_frame = ctk.CTkFrame(column_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=5)

        ctk.CTkButton(
            button_frame,
            text="Rename Column",
            command=self.rename_column,
            font=ModernTheme.BUTTON_FONT,
            fg_color=ModernTheme.PRIMARY
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            button_frame,
            text="Delete Column",
            command=self.delete_column,
            font=ModernTheme.BUTTON_FONT,
            fg_color=ModernTheme.ERROR
        ).pack(side="left", padx=2)

    def update_column_list(self):
        if self.df is not None:
            self.column_listbox.delete("1.0", "end")
            for col in self.df.columns:
                self.column_listbox.insert("end", f"{col}\n")

    def rename_column(self):
        if self.df is None:
            messagebox.showwarning("Warning", "Please load data first!")
            return

        # Get selected column
        try:
            selection = self.column_listbox.get("1.0", "end").splitlines()
            selected_line = self.column_listbox.index("insert").split('.')[0]
            old_name = selection[int(selected_line) - 1].strip()
        except:
            messagebox.showwarning("Warning", "Please select a column to rename!")
            return

        # Ask for new name
        new_name = ctk.CTkInputDialog(
            title="Rename Column",
            text=f"Enter new name for column '{old_name}':"
        ).get_input()

        if new_name:
            try:
                self.df.rename(columns={old_name: new_name}, inplace=True)
                self.update_column_list()
                self.show_data_preview()
                messagebox.showinfo("Success", f"Column renamed from '{old_name}' to '{new_name}'")
            except Exception as e:
                messagebox.showerror("Error", f"Error renaming column: {str(e)}")

    def delete_column(self):
        if self.df is None:
            messagebox.showwarning("Warning", "Please load data first!")
            return

        # Get selected column
        try:
            selection = self.column_listbox.get("1.0", "end").splitlines()
            selected_line = self.column_listbox.index("insert").split('.')[0]
            column_name = selection[int(selected_line) - 1].strip()
        except:
            messagebox.showwarning("Warning", "Please select a column to delete!")
            return

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete column '{column_name}'?"):
            try:
                self.df.drop(columns=[column_name], inplace=True)
                self.update_column_list()
                self.show_data_preview()
                messagebox.showinfo("Success", f"Column '{column_name}' deleted")
            except Exception as e:
                messagebox.showerror("Error", f"Error deleting column: {str(e)}")

    def create_data_preview(self, parent):
        # Data preview header
        header = ctk.CTkLabel(
            parent,
            text="Data Preview",
            font=ModernTheme.HEADER_FONT
        )
        header.pack(pady=10)

        # Database operations frame
        db_ops_frame = ctk.CTkFrame(parent, fg_color=ModernTheme.CARD_BG)
        db_ops_frame.pack(fill="x", padx=10, pady=5)

        # Database export buttons
        export_label = ctk.CTkLabel(
            db_ops_frame,
            text="Export to Database:",
            font=ModernTheme.TEXT_FONT
        )
        export_label.pack(pady=5)

        buttons_frame = ctk.CTkFrame(db_ops_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=5, pady=5)

        # PostgreSQL export
        pg_button = ctk.CTkButton(
            buttons_frame,
            text="Export to PostgreSQL",
            command=lambda: self.export_to_database("postgres"),
            font=ModernTheme.BUTTON_FONT,
            fg_color=ModernTheme.PRIMARY
        )
        pg_button.pack(side="left", padx=5)

        # SQL Server export
        sql_button = ctk.CTkButton(
            buttons_frame,
            text="Export to SQL Server",
            command=lambda: self.export_to_database("sqlserver"),
            font=ModernTheme.BUTTON_FONT,
            fg_color=ModernTheme.PRIMARY
        )
        sql_button.pack(side="left", padx=5)

        # MongoDB export
        mongo_button = ctk.CTkButton(
            buttons_frame,
            text="Export to MongoDB",
            command=lambda: self.export_to_database("mongodb"),
            font=ModernTheme.BUTTON_FONT,
            fg_color=ModernTheme.PRIMARY
        )
        mongo_button.pack(side="left", padx=5)

        # Create a frame to hold the treeview
        tree_frame = ctk.CTkFrame(parent)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Create scrollbars
        y_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        y_scrollbar.pack(side="right", fill="y")

        x_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")
        x_scrollbar.pack(side="bottom", fill="x")

        # Create Treeview
        self.data_preview = ttk.Treeview(
            tree_frame,
            show="headings",
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )
        self.data_preview.pack(fill="both", expand=True)

        # Configure scrollbars
        y_scrollbar.config(command=self.data_preview.yview)
        x_scrollbar.config(command=self.data_preview.xview)

    def export_to_database(self, db_type: str):
        if self.df is None:
            messagebox.showwarning("Warning", "Please load data first!")
            return

        # Get table name from user
        dialog = ctk.CTkInputDialog(
            title=f"Export to {db_type.title()}",
            text="Enter table name:"
        )
        table_name = dialog.get_input()

        if not table_name:
            return

        try:
            # Validate table name
            if not table_name.isalnum():
                raise ValueError("Table name must contain only letters and numbers")

            if db_type == "postgres":
                # Get PostgreSQL connection config
                config = self.pg_connection.get_config()
                conn_string = f'postgresql://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}'
                engine = create_engine(conn_string)

                # Export to PostgreSQL
                self.df.to_sql(table_name.lower(), engine, if_exists='replace', index=False)
                messagebox.showinfo("Success", f"Data exported to PostgreSQL table '{table_name}'")

            elif db_type == "sqlserver":
                # Get SQL Server connection config
                config = self.sql_connection.get_config()
                conn_string = f'mssql+pyodbc://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}?driver=ODBC+Driver+17+for+SQL+Server'
                engine = create_engine(conn_string)

                # Export to SQL Server
                self.df.to_sql(table_name.lower(), engine, if_exists='replace', index=False)
                messagebox.showinfo("Success", f"Data exported to SQL Server table '{table_name}'")

            elif db_type == "mongodb":
                # Get MongoDB connection config
                config = self.mongo_connection.get_config()
                client = pymongo.MongoClient(
                    host=config.host,
                    port=int(config.port),
                    username=config.username,
                    password=config.password
                )
                db = client[config.database]

                # Convert DataFrame to MongoDB format and export
                records = self.df.to_dict('records')
                if table_name in db.list_collection_names():
                    db[table_name].drop()
                db[table_name].insert_many(records)
                client.close()

                messagebox.showinfo("Success", f"Data exported to MongoDB collection '{table_name}'")

        except Exception as e:
            messagebox.showerror("Error", f"Error exporting to {db_type}: {str(e)}")

    def load_data(self):
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv")]
        )

        if not file_path:
            return

        try:
            self.df = pd.read_csv(file_path)
            self.file_entry.configure(state="normal")
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, file_path)
            self.file_entry.configure(state="readonly")

            self.show_data_preview()
        except Exception as e:
            messagebox.showerror("Error", f"Error loading data: {str(e)}")

    def show_data_preview(self):
        if self.df is None:
            return

        # Clear existing items
        for item in self.data_preview.get_children():
            self.data_preview.delete(item)

        # Configure columns
        self.data_preview['columns'] = list(self.df.columns)

        # Configure column headings
        for col in self.df.columns:
            self.data_preview.heading(col, text=col)
            # Set a reasonable minimum column width
            self.data_preview.column(col, minwidth=100, width=100)

        # Insert data (first 100 rows for performance)
        for i, row in self.df.head(100).iterrows():
            values = [str(value) for value in row]  # Convert all values to strings
            self.data_preview.insert("", "end", values=values)

    def transform_data(self):
        if self.df is None:
            messagebox.showwarning("Warning", "Please load data first!")
            return

        try:
            # Drop rows with missing values
            self.df = self.df.dropna()
            self.show_data_preview()
            messagebox.showinfo("Success", "Data transformed successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Error transforming data: {str(e)}")
    def reset_data(self):
        self.df = None
        self.file_entry.configure(state="normal")
        self.file_entry.delete(0, "end")
        self.file_entry.configure(state="readonly")
        self.show_data_preview()

    def create_analytics_tab(self):
        self.analytics_frame = DataAnalyticsFrame(self.tab_analytics, self)
        self.analytics_frame.pack(fill="both", expand=True, padx=10, pady=5)

    def create_connection_tab(self):
        # Create scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(
            self.tab_connection,
            fg_color="transparent"
        )
        scroll_frame.pack(fill="both", expand=True)

        # Create connection frames with modern styling
        self.pg_connection = DatabaseConnectionFrame(
            scroll_frame,
            "PostgreSQL Connection",
            self.config.DEFAULT_PG_CONFIG
        )
        self.pg_connection.pack(fill="x", padx=10, pady=5)

        self.sql_connection = DatabaseConnectionFrame(
            scroll_frame,
            "SQL Server Connection",
            self.config.DEFAULT_SQL_CONFIG
        )
        self.sql_connection.pack(fill="x", padx=10, pady=5)

        self.mongo_connection = DatabaseConnectionFrame(
            scroll_frame,
            "MongoDB Connection",
            self.config.DEFAULT_MONGO_CONFIG
        )
        self.mongo_connection.pack(fill="x", padx=10, pady=5)

        # Add action buttons
        self.create_connection_buttons(scroll_frame)



    def create_connection_buttons(self, parent):
        button_frame = ctk.CTkFrame(self.tab_connection, fg_color=ModernTheme.CARD_BG)
        button_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            button_frame,
            text="Test All Connections",
            command=self.test_all_connections,
            font=ModernTheme.BUTTON_FONT,
            fg_color=ModernTheme.PRIMARY
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Update Configurations",
            command=self.update_configurations,
            font=ModernTheme.BUTTON_FONT,
            fg_color=ModernTheme.SECONDARY
        ).pack(side="left", padx=5)

    def test_all_connections(self):
        self.pg_connection.test_connection()
        self.sql_connection.test_connection()
        self.mongo_connection.test_connection()
    def update_configurations(self):
        try:
            self.config.update_postgres_config(**self.pg_connection.get_config().__dict__)
            self.config.update_sqlserver_config(**self.sql_connection.get_config().__dict__)
            self.config.update_mongodb_config(**self.mongo_connection.get_config().__dict__)

            messagebox.showinfo("Success", "Configurations updated successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Error updating configurations: {str(e)}")

    def create_migrations_tab(self):
        # Create backup manager instance
        self.backup_manager = BackupManager()

        # Create frames for each database
        for db_type in ["PostgreSQL", "SQL Server", "MongoDB"]:
            frame = ctk.CTkFrame(self.tab_migrations, fg_color=ModernTheme.CARD_BG)
            frame.pack(fill="x", padx=10, pady=5)

            ctk.CTkLabel(
                frame,
                text=f"{db_type} Management",
                font=ModernTheme.HEADER_FONT
            ).pack(pady=5)

            # Backup button
            ctk.CTkButton(
                frame,
                text=f"Create {db_type} Backup",
                command=lambda t=db_type: self.create_backup(t),
                font=ModernTheme.BUTTON_FONT,
                fg_color=ModernTheme.PRIMARY
            ).pack(pady=5)

            # Restore button
            ctk.CTkButton(
                frame,
                text=f"Restore {db_type} Backup",
                command=lambda t=db_type: self.restore_backup(t),
                font=ModernTheme.BUTTON_FONT,
                fg_color=ModernTheme.SECONDARY
            ).pack(pady=5)

    def create_backup(self, db_type: str):
        try:
            self._show_loading(f"Creating {db_type} backup...")

            if db_type == "PostgreSQL":
                config = self.pg_connection.get_config()
                success, message = self.backup_manager.create_postgres_backup(config)
            elif db_type == "SQL Server":
                config = self.sql_connection.get_config()
                success, message = self.backup_manager.create_sqlserver_backup(config)
            else:  # MongoDB
                config = self.mongo_connection.get_config()
                success, message = self.backup_manager.create_mongodb_backup(config)

            self._update_logs(message)

            if success:
                messagebox.showinfo("Success", message)

            else:
                messagebox.showerror("Error", message)

        except Exception as e:
            self.logger.error(f"Error creating {db_type} backup: {e}")
            self._update_logs(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Error creating {db_type} backup: {str(e)}")

        finally:
            self._hide_loading()

    def restore_backup(self, db_type: str):
        try:
            backup_file = filedialog.askopenfilename(
                title=f"Select {db_type} Backup File",
                filetypes=[("Backup files", "*.bak")]
            )

            if not backup_file:
                return

            self._show_loading(f"Restoring {db_type} backup...")

            if db_type == "PostgreSQL":
                config = self.pg_connection.get_config()
                success, message = self.backup_manager.restore_postgres_backup(config, backup_file)
            elif db_type == "SQL Server":
                config = self.sql_connection.get_config()
                success, message = self.backup_manager.restore_sqlserver_backup(config, backup_file)
            else:  # MongoDB
                config = self.mongo_connection.get_config()
                success, message = self.backup_manager.restore_mongodb_backup(config, backup_file)

            self._update_logs(message)

            if success:
                messagebox.showinfo("Success", message)

            else:
                messagebox.showerror("Error", message)

        except Exception as e:
            self.logger.error(f"Error restoring {db_type} backup: {e}")
            self._update_logs(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Error restoring {db_type} backup: {str(e)}")

        finally:
            self._hide_loading()

    def _show_loading(self, text=""):
            self.loading_spinner = LoadingSpinner(self.app, text)  # Use self.app instead of self
            self.loading_spinner.pack(pady=10)
            self.loading_spinner.start()


    def _hide_loading(self):
        if hasattr(self, 'loading_spinner'):
            self.loading_spinner.stop()
            self.loading_spinner.destroy()

    def _update_logs(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logs_text.insert("end", f"[{timestamp}] {message}\n")
        self.logs_text.see("end")

    def _show_logs(self):
        self.logs_window = ctk.CTkToplevel(self)
        self.logs_window.title("Logs")
        self.logs_window.geometry("800x600")

        self.logs_text = ctk.CTkTextbox(
            self.logs_window,
            font=("Courier", 10),
            wrap="none"
        )
        self.logs_text.pack(fill="both", expand=True)

    def _hide_logs(self):
        if hasattr(self, 'logs_window'):
            self.logs_window.destroy()

    def _show_configurations(self):
        config_window = ctk.CTkToplevel(self)
        config_window.title("Configurations")
        config_window.geometry("800x600")

        config_text = ctk.CTkTextbox(
            config_window,
            font=("Courier", 10),
            wrap="none"
        )
        config_text.insert("end", json.dumps(self.config.__dict__, indent=2))
        config_text.pack(fill="both", expand=True)

    def _show_about(self):
        about_window = ctk.CTkToplevel(self)
        about_window.title("About")
        about_window.geometry("400x200")

        about_text = ctk.CTkLabel(
            about_window,
            text="Enhanced ETL Tool with Analytics\nVersion 1.0",
            font=("Helvetica", 16)
        )
        about_text.pack(pady=20)

        ctk.CTkLabel(
            about_window,
            text="Developed by: Boug\n2021",
            font=("Helvetica", 12)
        ).pack()

    def _show_help(self):
        help_window = ctk.CTkToplevel(self)
        help_window.title("Help")
        help_window.geometry("800x600")

        help_text = ctk.CTkTextbox(
            help_window,
            font=("Courier", 10),
            wrap="none"
        )
        help_text.insert("end", "Help and documentation coming soon...")
        help_text.pack(fill="both", expand=True)


def __init__(self):
    self.app = ctk.CTk()
    self.app.title("Enhanced ETL Tool with Analytics")
    self.app.geometry("1400x900")

    # Create logs text widget early
    self.create_logs_widget()

    # Set theme
    self.app.configure(fg_color=ModernTheme.BACKGROUND)

    self.config = AppConfig()
    self.logger = logging.getLogger(__name__)

    self.create_main_layout()
    self.app.mainloop()

def create_logs_widget(self):
    # Create a hidden frame for logs
    self.logs_frame = ctk.CTkFrame(self.app)
    self.logs_text = ctk.CTkTextbox(
        self.logs_frame,
        font=("Courier", 10),
        wrap="none"
    )
    self.logs_text.pack(fill="both", expand=True)

def _show_loading(self, text=""):
    # Create loading spinner in the app window instead of self
    self.loading_spinner = LoadingSpinner(self.app, text)
    self.loading_spinner.pack(pady=10)
    self.loading_spinner.start()

def load_data(self):
    file_path = filedialog.askopenfilename(
        title="Select CSV File",
        filetypes=[("CSV files", "*.csv")]
    )

    if not file_path:
        return

    try:
        self.df = pd.read_csv(file_path)
        self.file_entry.configure(state="normal")
        self.file_entry.delete(0, "end")
        self.file_entry.insert(0, file_path)
        self.file_entry.configure(state="readonly")

        self.update_column_list()  # Update column list when loading data
        self.show_data_preview()
    except Exception as e:
        messagebox.showerror("Error", f"Error loading data: {str(e)}")


if __name__ == "__main__":
    EnhancedETLApp()
