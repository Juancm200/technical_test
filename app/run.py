import pandas as pd
import sqlite3
import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel, StringVar
import win32com.client as win32 


DB_PATH = 'app/data/database.sqlite'
report = None  # Variable global para almacenar el reporte
parameters = {}  # Diccionario para almacenar los parámetros de cada empresa

def load_data(db_path):
    """
    Carga los datos de la tabla 'apicall' desde la base de datos SQLite.

    Args:
        db_path (str): Ruta a la base de datos SQLite.

    Returns:
        pd.DataFrame: DataFrame con los datos cargados.
    """
    try:
        conn = sqlite3.connect(db_path)
        query = "SELECT * FROM apicall"
        data = pd.read_sql_query(query, conn)
    except Exception as e:
        print(f"Error loading data: {e}")
        data = pd.DataFrame()
    finally:
        conn.close()
    return data

def load_contracts(db_path):
    """
    Carga los contratos de la tabla 'commerce' desde la base de datos SQLite.

    Args:
        db_path (str): Ruta a la base de datos SQLite.

    Returns:
        pd.DataFrame: DataFrame con los contratos cargados.
    """
    try:
        conn = sqlite3.connect(db_path)
        query = "SELECT * FROM commerce"
        contracts = pd.read_sql_query(query, conn)
    except Exception as e:
        print(f"Error loading contracts: {e}")
        contracts = pd.DataFrame()
    finally:
        conn.close()
    return contracts

def clean_data(data):
    """
    Limpia los datos eliminando filas con valores nulos en la columna 'commerce_id'.

    Args:
        data (pd.DataFrame): DataFrame con los datos a limpiar.

    Returns:
        pd.DataFrame: DataFrame limpio.
    """
    data = data.dropna(subset=['commerce_id'])
    return data

def assign_commerce_names(data, contracts):
    """
    Asigna nombres de comercio a los datos mediante una unión con los contratos.

    Args:
        data (pd.DataFrame): DataFrame con los datos.
        contracts (pd.DataFrame): DataFrame con los contratos.

    Returns:
        pd.DataFrame: DataFrame con los nombres de comercio asignados.
    """
    data = clean_data(data)
    
    # Ensure commerce_id is of the same type in both dataframes
    data['commerce_id'] = data['commerce_id'].astype(str)
    contracts['commerce_id'] = contracts['commerce_id'].astype(str)
    
    data_merge = pd.merge(data, contracts, on='commerce_id', how='left')
    return data_merge


def add_condition(commerce_id, ranged_option, min_value, max_value, rate, type_condition):
    """
    Agrega una nueva condición a la base de datos.

    Args:
        commerce_id (str): ID del comercio.
        ranged_option (str): Opción de rango ('fixed' o 'range').
        min_value (float): Valor mínimo.
        max_value (float): Valor máximo.
        rate (float): Tasa.
        type_condition (str): Tipo de condición ('fee' o 'discount').
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO conditions_commerce (commerce_id, ranged_option, min_value, max_value, rate, type_condition)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (commerce_id, ranged_option, min_value, max_value, rate, type_condition))
        conn.commit()
        messagebox.showinfo("Success", "Condition added successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Error adding condition: {e}")
    finally:
        conn.close()

def update_condition(condition_id, ranged_option, min_value, max_value, rate, type_condition):
    """
    Actualiza una condición existente en la base de datos.

    Args:
        condition_id (int): ID de la condición.
        ranged_option (str): Opción de rango ('fixed' o 'range').
        min_value (float): Valor mínimo.
        max_value (float): Valor máximo.
        rate (float): Tasa.
        type_condition (str): Tipo de condición ('fee' o 'discount').
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE conditions_commerce
            SET ranged_option = ?, min_value = ?, max_value = ?, rate = ?, type_condition = ?
            WHERE id = ?
        ''', (ranged_option, min_value, max_value, rate, type_condition, condition_id))
        conn.commit()
        messagebox.showinfo("Success", "Condition updated successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Error updating condition: {e}")
    finally:
        conn.close()

def delete_condition(condition_id):
    """
    Elimina una condición de la base de datos.

    Args:
        condition_id (int): ID de la condición.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM conditions_commerce WHERE id = ?', (condition_id,))
        conn.commit()
        messagebox.showinfo("Success", "Condition deleted successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Error deleting condition: {e}")
    finally:
        conn.close()

def calculate_commissions(data):
    """
    Calcula las comisiones basadas en los datos y las condiciones almacenadas en la base de datos.

    Args:
        data (pd.DataFrame): DataFrame con los datos.

    Returns:
        pd.DataFrame: DataFrame con las comisiones calculadas.
    """
    # Solicitar los meses que se desean calcular
    start_month_dialog = ctk.CTkInputDialog(text="Ingrese el fecha de inicio (YYYY-MM):", title="Fecha de Inicio")
    start_month_dialog.geometry("+{}+{}".format(int(start_month_dialog.winfo_screenwidth()/2 - start_month_dialog.winfo_reqwidth()/2), 
                                                int(start_month_dialog.winfo_screenheight()/2 - start_month_dialog.winfo_reqheight()/2)))
    start_month = start_month_dialog.get_input()

    end_month_dialog = ctk.CTkInputDialog(text="Ingrese el fecha de fin (YYYY-MM):", title="Fecha de Fin")
    end_month_dialog.geometry("+{}+{}".format(int(end_month_dialog.winfo_screenwidth()/2 - end_month_dialog.winfo_reqwidth()/2), 
                                              int(end_month_dialog.winfo_screenheight()/2 - end_month_dialog.winfo_reqheight()/2)))
    end_month = end_month_dialog.get_input()

    # Convertir las entradas a períodos de pandas
    start_period = pd.Period(start_month, freq='M')
    end_period = pd.Period(end_month, freq='M')

    # Filtrar los datos para los meses seleccionados
    data['month'] = pd.to_datetime(data['date_api_call']).dt.to_period('M')
    data = data[(data['month'] >= start_period) & (data['month'] <= end_period)]

    # Filtrar solo las empresas activas
    data = data[data['commerce_status'] == 'Active']

    grouped = data.groupby(['commerce_name', 'month', 'commerce_email', 'commerce_id']).agg(
        successful_calls=('ask_status', lambda x: (x == 'Successful').sum()),
        unsuccessful_calls=('ask_status', lambda x: (x == 'Unsuccessful').sum())
    ).reset_index()

    def calculate_row(row):
        commerce_id = row['commerce_id']
        successful = row['successful_calls']
        unsuccessful = row['unsuccessful_calls']
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM conditions_commerce WHERE commerce_id = ?', (commerce_id,))
        conditions = cursor.fetchall()
        conn.close()

        commission = 0
        discount = 0
        for condition in conditions:
            _, _, ranged_option, min_value, max_value, rate, type_condition = condition
            if ranged_option == 'fixed':
                if type_condition == 'fee':
                    commission += successful * rate
                elif type_condition == 'discount':
                    discount += rate
            elif ranged_option == 'range':
                if type_condition == 'fee' and min_value <= successful <= (max_value if max_value is not None else float('inf')):
                    commission += successful * rate
                elif type_condition == 'discount' and min_value <= unsuccessful <= (max_value if max_value is not None else float('inf')):
                    discount += rate

        # Aplicar el descuento a la comisión
        commission -= commission * (discount / 100)

        iva = commission * 0.19
        total = commission + iva
        return pd.Series([commission, iva, total])

    grouped[['commission', 'iva', 'total']] = grouped.apply(calculate_row, axis=1)
    return grouped

def select_db_path():
    """
    Abre un cuadro de diálogo para seleccionar la ruta de la base de datos.
    """
    global DB_PATH
    DB_PATH = filedialog.askopenfilename(filetypes=[("SQLite files", "*.sqlite"), ("All files", "*.*")])
    db_path_label.configure(text=f"Database Path: {DB_PATH}")

def execute_calculation():
    """
    Ejecuta el cálculo de comisiones y muestra el resultado.
    """
    global report
    data = load_data(DB_PATH)
    contracts = load_contracts(DB_PATH)
    data = assign_commerce_names(data, contracts)
    report = calculate_commissions(data)
    messagebox.showinfo("Success", "Calculation completed successfully!")
    print("\nCommission Report:")
    print(report.head())

def export_to_excel():
    """
    Exporta el reporte de comisiones a un archivo Excel.
    """
    global report
    if report is not None:
        report.to_excel('app/data/commission_report.xlsx', index=False)
        messagebox.showinfo("Success", "Report exported to Excel successfully!")
    else:
        messagebox.showwarning("Warning", "No report to export. Please calculate commissions first.")

# Enviar email
import win32com.client as win32
import pandas as pd
from tkinter import messagebox

def send_email():
    """
    Envía el reporte de comisiones por correo electrónico.
    """
    global report
    if report is not None:
        outlook = win32.Dispatch('outlook.application')
        
        # Estilo de la tabla HTML
        table_style_html = """
        <style>
            .styled-table {
                border-collapse: collapse;
                margin: 15px 0;
                font-size: 0.9em;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                min-width: 600px;
                max-width: 100%;
                width: auto; /* Asegura que la tabla se ajuste al contenido */
                box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
                word-wrap: break-word; /* Permite que el texto se ajuste dentro de la celda */
            }
            .styled-table thead tr {
                background-color: #009879;
                color: #ffffff;
                text-align: left;
            }
            .styled-table th,
            .styled-table td {
                padding: 2px 4px; /* Corrige el valor de padding para que sea 4px, no 4x */
                max-width: 300px; /* Establece un ancho máximo para las celdas */
                overflow-wrap: break-word; /* Permite que el texto largo se ajuste */
            }
            .styled-table tbody tr {
                border-bottom: 1px solid #dddddd;
            }
            .styled-table tbody tr:nth-of-type(even) {
                background-color: #f3f3f3;
            }
            .styled-table tbody tr:last-of-type {
                border-bottom: 2px solid #009879;
            }
        </style>
        """
        namespace = outlook.GetNamespace("MAPI")
        correo_usuario = namespace.CurrentUser.Address

        mail = outlook.CreateItem(0)
        mail.To = correo_usuario
        mail.Subject = "Informe de Comisiones Calculadas"
        mail.Body = "Resumen del Informe de Comisiones Calculadas para los meses seleccionados."

        # Seleccionar las columnas necesarias
        report_filtered = report[['month', 'commerce_name', 'commerce_id', 'commission', 'iva', 'total', 'commerce_email']]
        report_filtered.columns = ['Fecha-Mes', 'Nombre', 'Nit', 'Valor_comision', 'Valor_iva', 'Valor_Total', 'Correo']

        # Convertir el reporte a una tabla HTML
        table_html = report_filtered.to_html(table_id='your_table', index=False)
        table_html = table_html.replace('class="dataframe" id="your_table">', 'class="styled-table" id="your_table">')
        final_html = table_style_html + table_html

        # Crear el cuerpo del correo con la tabla HTML
        mail.HTMLBody = f"""
        <html>
        <body>
        <p>Please find the attached commission report.</p>
        {final_html}
        </body>
        </html>
        """

        mail.Send()
        print(f"Email sent successfully to {correo_usuario}")
        
        messagebox.showinfo("Success", "Email sent successfully!")
    else:
        messagebox.showwarning("Warning", "No report to send. Please calculate commissions first.")

def open_conditions_window():
    """
    Abre una ventana para gestionar las condiciones de los comercios.
    """
    conditions_window = Toplevel(root)
    conditions_window.title("Manage Conditions")
    conditions_window.geometry("700x600")

    def load_conditions():
        """
        Carga las condiciones para un comercio específico.
        """
        commerce_id = commerce_id_var.get()
        if not commerce_id:
            messagebox.showerror("Error", "Please enter a Commerce ID before loading conditions.", parent=conditions_window)
            return
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Comprueba si commerce_id existe en la tabla de comercio
        cursor.execute('SELECT 1 FROM commerce WHERE commerce_id = ?', (commerce_id,))
        if cursor.fetchone() is None:
            messagebox.showerror("Error", "Commerce ID does not exist in the commerce table.", parent=conditions_window)
            conn.close()
            return
        
        cursor.execute('SELECT * FROM conditions_commerce WHERE commerce_id = ?', (commerce_id,))
        conditions = cursor.fetchall()
        conn.close()
        for widget in conditions_frame.winfo_children():
            widget.destroy()
        
        for condition in conditions:
            condition_id, commerce_id, ranged_option, min_value, max_value, rate, type_condition = condition
            ctk.CTkLabel(conditions_frame, text=f"ID: {condition_id}").grid(row=condition_id, column=0, pady=5, padx=10)
            ctk.CTkLabel(conditions_frame, text=f"Type: {ranged_option}").grid(row=condition_id, column=1, pady=5, padx=10)
            ctk.CTkLabel(conditions_frame, text=f"Min: {min_value}").grid(row=condition_id, column=2, pady=5, padx=10)
            ctk.CTkLabel(conditions_frame, text=f"Max: {max_value}").grid(row=condition_id, column=3, pady=5, padx=10)
            ctk.CTkLabel(conditions_frame, text=f"Rate: {rate}").grid(row=condition_id, column=4, pady=5, padx=5)
            ctk.CTkLabel(conditions_frame, text=f"Type Condition: {type_condition}").grid(row=condition_id, column=5, pady=5, padx=5)
            ctk.CTkButton(conditions_frame, text="Edit", command=lambda cid=condition_id: edit_condition_ui(cid), width=90).grid(row=condition_id, column=6, pady=5, padx=5)
            ctk.CTkButton(conditions_frame, text="Delete", command=lambda cid=condition_id: delete_condition_ui(cid), width=90).grid(row=condition_id, column=7, pady=5, padx=5)

    def add_condition_ui():
        """
        Interfaz de usuario para agregar una nueva condición.
        """
        commerce_id = commerce_id_var.get()
        if not commerce_id:
            messagebox.showerror("Error", "Please select a company before adding a condition.", parent=conditions_window)
            return

        ranged_option = ranged_option_var.get()
        type_condition = type_condition_var.get()
        
        if ranged_option == 'fixed':
            min_value = None
            max_value = None
        else:
            min_value = int(min_value_var.get()) if min_value_var.get() else None
            max_value = max_value_var.get()
            if max_value.lower() == 'inf' or max_value == '':
                max_value = float('inf')
            else:
                max_value = int(max_value)
        
        rate = float(rate_var.get()) if rate_var.get() else None

        # Comprueba si commerce_id existe en la tabla de comercio
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, ranged_option FROM conditions_commerce WHERE commerce_id = ?', (commerce_id,))
        existing_conditions = cursor.fetchall()

        if existing_conditions:
            existing_types = {cond[1] for cond in existing_conditions}
            if ranged_option == 'fixed' and 'range' in existing_types:
                messagebox.showerror("Error", "Cannot add a fixed condition when range conditions exist for this commerce ID.", parent=conditions_window)
                conn.close()
                return
            elif ranged_option == 'range' and 'fixed' in existing_types:
                messagebox.showerror("Error", "Cannot add a range condition when a fixed condition exists for this commerce ID.", parent=conditions_window)
                conn.close()
                return
            elif ranged_option == 'fixed' and 'fixed' in existing_types:
                # Update the existing fixed condition
                cursor.execute('''
                    UPDATE conditions_commerce
                    SET ranged_option = ?, min_value = ?, max_value = ?, rate = ?, type_condition = ?
                    WHERE commerce_id = ? AND ranged_option = 'fixed'
                ''', (ranged_option, min_value, max_value, rate, type_condition, commerce_id))
                conn.commit()
                messagebox.showinfo("Success", "Fixed condition updated successfully!", parent=conditions_window)
                load_conditions()
                conn.close()
                return

        add_condition(commerce_id, ranged_option, min_value, max_value, rate, type_condition)
        load_conditions()
        conn.close()

    def edit_condition_ui(condition_id):
        """
        Interfaz de usuario para editar una condición existente.
        """
        edit_window = Toplevel(conditions_window)
        edit_window.title("Edit Condition")
        edit_window.geometry("300x250")

        ranged_option_var = StringVar()
        min_value_var = StringVar()
        max_value_var = StringVar()
        rate_var = StringVar()
        type_condition_var = StringVar()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM conditions_commerce WHERE id = ?', (condition_id,))
        condition = cursor.fetchone()
        conn.close()

        _, _, ranged_option, min_value, max_value, rate, type_condition = condition

        ranged_option_var.set(ranged_option)
        min_value_var.set(min_value)
        max_value_var.set(max_value)
        rate_var.set(rate)
        type_condition_var.set(type_condition)

        edit_window.grid_columnconfigure(0, weight=1)
        edit_window.grid_columnconfigure(1, weight=2)

        # Etiqueta y menú desplegable para Condition Type
        ctk.CTkLabel(edit_window, text="Condition Type").grid(row=0, column=0, pady=5, padx=10, sticky="e")
        ranged_option_menu = ctk.CTkOptionMenu(edit_window, variable=ranged_option_var, values=["fixed", "range"])
        ranged_option_menu.grid(row=0, column=1, pady=5, padx=10, sticky="ew")

        # Etiqueta y entrada para Min Value
        ctk.CTkLabel(edit_window, text="Min Value").grid(row=1, column=0, pady=5, padx=10, sticky="e")
        min_value_entry = ctk.CTkEntry(edit_window, textvariable=min_value_var)
        min_value_entry.grid(row=1, column=1, pady=5, padx=10, sticky="ew")

        # Etiqueta y entrada para Max Value
        ctk.CTkLabel(edit_window, text="Max Value").grid(row=2, column=0, pady=5, padx=10, sticky="e")
        max_value_entry = ctk.CTkEntry(edit_window, textvariable=max_value_var)
        max_value_entry.grid(row=2, column=1, pady=5, padx=10, sticky="ew")

        # Etiqueta y entrada para Rate
        ctk.CTkLabel(edit_window, text="Rate").grid(row=3, column=0, pady=5, padx=10, sticky="e")
        ctk.CTkEntry(edit_window, textvariable=rate_var).grid(row=3, column=1, pady=5, padx=10, sticky="ew")

        # Etiqueta y entrada para Type Condition

        ctk.CTkLabel(edit_window, text="Type Condition").grid(row=4, column=0, pady=5, padx=10, sticky="e")
        type_condition_menu = ctk.CTkOptionMenu(edit_window, variable=type_condition_var, values=["fee", "discount"])
        type_condition_menu.grid(row=4, column=1, pady=5, padx=10, sticky="ew")

        def save_changes():
            """
            Guarda los cambios realizados en la condición.

            Obtiene los valores de las variables de entrada, los procesa y actualiza la condición en la base de datos.
            Luego, cierra la ventana de edición y recarga las condiciones.
            """
            ranged_option = ranged_option_var.get()
            min_value = int(min_value_var.get()) if min_value_var.get() else None
            max_value = max_value_var.get()
            if max_value.lower() == 'inf' or max_value == '':
                max_value = float('inf')
            else:
                max_value = int(max_value)
            rate = float(rate_var.get()) if rate_var.get() else None
            type_condition = type_condition_var.get()
            update_condition(condition_id, ranged_option_var.get(), min_value_var.get(), max_value_var.get(), rate_var.get(), type_condition_var.get())
            edit_window.destroy()
            load_conditions()

        ranged_option_var.trace_add("write", lambda: toggle_fields(ranged_option_var.get(), min_value_entry, max_value_entry))

        ctk.CTkButton(edit_window, text="Save Changes", command=save_changes).grid(row=5, column=0, columnspan=2, pady=10)

        toggle_fields(ranged_option_var.get(), min_value_entry, max_value_entry)

    def delete_condition_ui(condition_id):
        """
        Elimina una condición específica.

        Llama a la función delete_condition para eliminar la condición de la base de datos y luego recarga las condiciones.
        """
        delete_condition(condition_id)
        load_conditions()

    def toggle_fields(ranged_option, min_value_entry, max_value_entry):
        """
        Alterna la visibilidad de los campos de entrada Min Value y Max Value.

        Si la opción de rango es "fixed", oculta los campos de entrada. De lo contrario, los muestra.
        """
        if ranged_option == "fixed":
            min_value_entry.grid_remove()
            max_value_entry.grid_remove()
        else:
            min_value_entry.grid()
            max_value_entry.grid()

    commerce_id_var = StringVar()
    ranged_option_var = StringVar()
    commerce_id_name = StringVar()
    min_value_var = StringVar()
    max_value_var = StringVar()
    rate_var = StringVar()
    type_condition_var = StringVar()

    conditions_window.grid_columnconfigure(0, weight=1)
    conditions_window.grid_columnconfigure(1, weight=2)

    # Etiqueta y entrada para Commerce ID
    ctk.CTkLabel(conditions_window, text="Commerce ID ").grid(row=0, column=0, pady=5, padx=10, sticky="e")
    ctk.CTkEntry(conditions_window, textvariable=commerce_id_var).grid(row=0, column=1, pady=5, padx=10, sticky="ew")

    def update_commerce_name(*args):
        """
        Actualiza el nombre del comercio basado en el ID del comercio.

        Obtiene el ID del comercio de la variable commerce_id_var, consulta la base de datos para obtener el nombre del comercio
        y actualiza la variable commerce_id_name con el nombre del comercio.
        """
        commerce_id = commerce_id_var.get()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT commerce_name FROM commerce WHERE commerce_id = ?', (commerce_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            commerce_id_name.set(result[0])
        else:
            commerce_id_name.set("")

    commerce_id_var.trace_add("write", update_commerce_name)
    ctk.CTkLabel(conditions_window, textvariable=commerce_id_name, font=("Arial", 12, "underline", "bold")).grid(row=0, column=0, pady=5, padx=10, sticky="w")

    # Botón para cargar condiciones
    ctk.CTkButton(conditions_window, text="Load Conditions", command=load_conditions).grid(row=1, column=0, columnspan=2, pady=10, padx=10, sticky="ew")

    # Frame para las condiciones
    conditions_frame = ctk.CTkFrame(conditions_window)
    conditions_frame.grid(row=2, column=0, columnspan=2, pady=10, padx=10, sticky="ew")

    # Etiqueta y menú desplegable para Condition Type
    ctk.CTkLabel(conditions_window, text="Add Condition").grid(row=3, column=1, pady=5, padx=10, sticky="ew")

    ctk.CTkLabel(conditions_window, text="Type Condition").grid(row=4, column=0, pady=5, padx=10, sticky="e")
    type_condition_menu = ctk.CTkOptionMenu(conditions_window, variable=type_condition_var, values=["fee", "discount"])
    type_condition_menu.grid(row=4, column=1, pady=5, padx=10, sticky="ew")

    ctk.CTkLabel(conditions_window, text="Range Option").grid(row=5, column=0, pady=5, padx=10, sticky="e")
    ranged_option_menu = ctk.CTkOptionMenu(conditions_window, variable=ranged_option_var, values=["fixed", "range"])
    ranged_option_menu.grid(row=5, column=1, pady=5, padx=10, sticky="ew")

    # Etiqueta y entrada para Min Value
    ctk.CTkLabel(conditions_window, text="Min Value").grid(row=6, column=0, pady=5, padx=10, sticky="e")
    min_value_entry = ctk.CTkEntry(conditions_window, textvariable=min_value_var)
    min_value_entry.grid(row=6, column=1, pady=5, padx=10, sticky="ew")

    # Etiqueta y entrada para Max Value
    ctk.CTkLabel(conditions_window, text="Max Value").grid(row=7, column=0, pady=5, padx=10, sticky="e")
    max_value_entry = ctk.CTkEntry(conditions_window, textvariable=max_value_var)
    max_value_entry.grid(row=7, column=1, pady=5, padx=10, sticky="ew")

    # Etiqueta y entrada para Rate
    ctk.CTkLabel(conditions_window, text="Rate").grid(row=8, column=0, pady=5, padx=10, sticky="e")
    ctk.CTkEntry(conditions_window, textvariable=rate_var).grid(row=8, column=1, pady=5, padx=10, sticky="ew")



    # Toggle de campos basado en el tipo de condición
    ranged_option_var.trace("w", lambda *args: toggle_fields(ranged_option_var.get(), min_value_entry, max_value_entry))

    # Botón para agregar una condición
    def validate_and_add_condition():
        """
        Valida los campos de entrada y agrega una nueva condición.

        Verifica que los campos requeridos estén completos antes de llamar a la función add_condition_ui para agregar la condición.
        """
        ranged_option = ranged_option_var.get()
        if ranged_option == 'fixed':
            if not rate_var.get():
                messagebox.showerror("Error", "Rate is required for fixed condition.", parent=conditions_window)
                return
        else:
            if not min_value_var.get() or not max_value_var.get() or not rate_var.get():
                messagebox.showerror("Error", "Min Value, Max Value, and Rate are required for range condition.", parent=conditions_window)
                return
        add_condition_ui()

    add_condition_button = ctk.CTkButton(conditions_window, text="Add Condition", command=validate_and_add_condition)
    add_condition_button.grid(row=10, column=0, columnspan=2, pady=10, padx=10, sticky="ew")
    add_condition_button.configure(state="disabled")

    def enable_add_condition_button():
        """
        Habilita el botón para agregar una condición.

        Cambia el estado del botón add_condition_button a "normal".
        """
        add_condition_button.configure(state="normal")

    def load_conditions_with_enable():
        """
        Carga las condiciones y habilita el botón para agregar una condición.

        Llama a la función load_conditions para cargar las condiciones y luego habilita el botón add_condition_button.
        """
        load_conditions()
        enable_add_condition_button()

    ctk.CTkButton(conditions_window, text="Load Conditions", command=load_conditions_with_enable).grid(row=1, column=0, columnspan=2, pady=10, padx=10, sticky="ew")

    # Ejecutar la ventana
    toggle_fields(ranged_option_var.get(), min_value_entry, max_value_entry)
# Crear la interfaz gráfica con customtkinter
ctk.set_appearance_mode("System")  # Modo de apariencia
ctk.set_default_color_theme("green")  # Tema de color

root = ctk.CTk()
root.title("Commission Calculator")

# Centrar ventana principal
window_width = 600
window_height = 400
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
position_top = int(screen_height / 4 - window_height / 4)
position_right = int(screen_width / 2 - window_width / 2)
root.geometry(f"{window_width}x{window_height}+{position_right}+{position_top}")

# Configurar el grid layout para el root
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

frame = ctk.CTkFrame(root)
frame.grid(row=0, column=0, sticky="nsew", pady=20, padx=20)

# Configurar el grid layout para el frame
frame.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)
frame.grid_columnconfigure((0, 1), weight=1)

db_path_label = ctk.CTkLabel(frame, text=f"Database Path: {DB_PATH}.", font=("Arial", 16))
db_path_label.grid(row=0, column=0, columnspan=2, pady=10, sticky="ew")

select_db_button = ctk.CTkButton(frame, text="Select Database", command=select_db_path,font=("Arial", 16, "bold"),height=50)
select_db_button.grid(row=1, column=0,columnspan=2, padx=10, pady=2, sticky="ew")


manage_conditions_button = ctk.CTkButton(frame, text="Manage Conditions", command=open_conditions_window,font=("Arial", 16, "bold"),height=50)
manage_conditions_button.grid(row=2, column=0, columnspan=2, padx=10, pady=2, sticky="ew")

calculate_button = ctk.CTkButton(frame, text="Calculate Commissions", command=execute_calculation,font=("Arial", 16, "bold"),height=50)
calculate_button.grid(row=3, column=0, columnspan=2, padx=10, pady=2, sticky="ew")

export_button = ctk.CTkButton(frame, text="Export to Excel", command=export_to_excel,font=("Arial", 16, "bold"),height=50)
export_button.grid(row=4, column=0, columnspan=2, padx=10, pady=2, sticky="ew")

send_email_button = ctk.CTkButton(frame, text="Send Email", command=send_email,font=("Arial", 16, "bold"),height=50)
send_email_button.grid(row=5, column=0, columnspan=2, padx=10, pady=2, sticky="ew")

root.mainloop()