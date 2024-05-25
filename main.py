import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import math
import tkinter as tk
from tkinter import ttk
import mysql.connector

# Cargar datos
df = pd.read_csv("shoes_dataset.csv")
df['Date'] = pd.to_datetime(df['Date'])
df['Year'] = df['Date'].dt.year
df['Month'] = df['Date'].dt.month
df['Day'] = df['Date'].dt.day
df['SalePrice'] = df['SalePrice'].apply(lambda x: float(x[2:]))
df['UnitPrice'] = df['UnitPrice'].apply(lambda x: float(x[2:]))

# Conectar a MySQL con el usuario creado
conn = mysql.connector.connect(
    host="localhost",
    user="user",
    password="password123!",
    database="shoe_store"
)
cursor = conn.cursor()

# Función para crear tablas si no existen y guardar datos
def save_data_to_db(table_name, data):
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        category VARCHAR(255),
        quantity INT
    )
    """)
    # Eliminar datos existentes antes de insertar nuevos datos para evitar duplicación
    cursor.execute(f"DELETE FROM {table_name}")
    for index, row in data.iterrows():
        cursor.execute(f"INSERT INTO {table_name} (category, quantity) VALUES (%s, %s)", (row['category'], int(row['quantity'])))
    conn.commit()

# Función para guardar la matriz de correlación en MySQL
def save_correlation_matrix_to_db(corr_matrix):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS CorrelationMatrix (
        var1 VARCHAR(255),
        var2 VARCHAR(255),
        correlation FLOAT
    )
    """)
    cursor.execute("DELETE FROM CorrelationMatrix")
    for i in range(corr_matrix.shape[0]):
        for j in range(corr_matrix.shape[1]):
            cursor.execute("INSERT INTO CorrelationMatrix (var1, var2, correlation) VALUES (%s, %s, %s)", 
                           (corr_matrix.index[i], corr_matrix.columns[j], corr_matrix.iloc[i, j]))
    conn.commit()

# Función para guardar los datos agrupados en MySQL
def save_grouped_data_to_db(grouped_data):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS GroupedData (
        size_us VARCHAR(255),
        year INT,
        month INT,
        quantity INT
    )
    """)
    cursor.execute("DELETE FROM GroupedData")
    for index, row in grouped_data.iterrows():
        for col in grouped_data.columns:
            cursor.execute("INSERT INTO GroupedData (size_us, year, month, quantity) VALUES (%s, %s, %s, %s)", 
                           (col, index[0], index[1], int(row[col])))
    conn.commit()

# Función para graficar y guardar la matriz de correlación
def plot_correlation_matrix():
    numeric_df = df.select_dtypes(include=[float, int])
    corr = numeric_df.corr()
    sns.heatmap(corr, vmin=-1, vmax=1, center=0,
                cmap=sns.diverging_palette(20, 220, n=200),
                square=True)
    plt.show()
    save_correlation_matrix_to_db(corr)

def plot_grouped_data():
    grouped = df[(df['Year'] != 2014) & (df['Gender'] == 'Male') & (df['Country'] == 'United States')]\
        .groupby(['Size (US)', 'Year', 'Month']).size().unstack(level=0).fillna(value=0)

    means = []
    standard_errors = []
    for column in grouped.columns:
        means.append(grouped[column].mean())
        standard_errors.append(grouped[column].sem())

    d = {'means': means, 'std_error': standard_errors}
    df_calculations = pd.DataFrame(data=d, index=grouped.columns)

    df_calculations['error_margin'] = df_calculations['std_error'].apply(lambda x: x * 2.07)
    df_calculations['low_margin'] = df_calculations.apply(lambda x: x['means'] - x['error_margin'], axis=1)
    df_calculations['up_margin'] = df_calculations.apply(lambda x: x['means'] + x['error_margin'], axis=1)
    df_calculations['math_round_up'] = df_calculations.apply(lambda x: math.ceil(x['up_margin']), axis=1)

    df_calculations.plot(kind='bar', y='means', yerr='std_error', capsize=4)
    plt.show()

    # Guardar los datos agrupados en la base de datos
    save_grouped_data_to_db(grouped)

# Interfaz gráfica
root = tk.Tk()
root.title("Selección de Gráficos")

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

label = ttk.Label(frame, text="Seleccione el gráfico que desea ver:")
label.grid(row=0, column=0, columnspan=2, pady=5)

row_counter = 1

def show_plot(plot_function, variable=None):
    if variable:
        plot_function(variable)
    else:
        plot_function()

button1 = ttk.Button(frame, text="Frecuencia de Tiendas", command=lambda: show_plot(plot_frequency_shops))
button1.grid(row=row_counter, column=0, pady=5, sticky=tk.W+tk.E)
row_counter += 1

# Agregar botones para variables categóricas
categorical_variables = ['Country', 'ProductID', 'Gender', 'Size (US)', 'Discount', 'Year', 'Month']
for variable in categorical_variables:
    button = ttk.Button(frame, text=f'Frecuencia de {variable}', command=lambda v=variable: show_plot(plot_and_save_data, v))
    button.grid(row=row_counter, column=0, pady=5, sticky=tk.W+tk.E)
    row_counter += 1

button_corr = ttk.Button(frame, text="Matriz de Correlación", command=lambda: show_plot(plot_correlation_matrix))
button_corr.grid(row=row_counter, column=0, pady=5, sticky=tk.W+tk.E)
row_counter += 1

button_grouped = ttk.Button(frame, text="Datos Agrupados", command=lambda: show_plot(plot_grouped_data))
button_grouped.grid(row=row_counter, column=0, pady=5, sticky=tk.W+tk.E)

root.mainloop()

# Cerrar la conexión
cursor.close()
conn.close()
