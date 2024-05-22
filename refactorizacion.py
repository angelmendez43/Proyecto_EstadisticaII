import pandas as pd
import pymysql
import matplotlib.pyplot as plt
import seaborn as sns
import math
import tkinter
from tkinter import ttk


# Conexión a la base de datos MySQL
def cargar_data():
    connection = pymysql.connect(
        host="tu_host", user="tu_usuario", password="tu_contraseña", database="tu_base_de_datos"
    )

    query = "SELECT * FROM shoes_dataset"
    df = pd.read_sql(query, connection)
    connection.close()

    # Procesamiento de datos
    # Convertir la columna 'Date' a tipo datetime
    df["Date"] = pd.to_datetime(df["Date"])

    # Extraer el año, mes y día de la columna 'Date'
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Day"] = df["Date"].dt.day

    # Convertir las columnas 'SalePrice' y 'UnitPrice' a tipo float, eliminando el símbolo de moneda
    df["SalePrice"] = df["SalePrice"].apply(lambda x: float(x[2:]))
    df["UnitPrice"] = df["UnitPrice"].apply(lambda x: float(x[2:]))

    return df


def filtros():
    filtered_df = df.copy()

    year = year_var.get()
    size = size_var.get()
    shop = shop_var.get()
    gender = gender_var.get()

    if year:
        filtered_df = filtered_df[filtered_df["Year"] == int(year)]
    if size:
        filtered_df = filtered_df[filtered_df["Size (US)"] == size]
    if shop:
        filtered_df = filtered_df[filtered_df["Shop"] == shop]
    if gender:
        filtered_df = filtered_df[filtered_df["Gender"] == gender]

    refrescar_graficas(filtered_df)


def refrescar_graficas(filtered_df):
    describe = filtered_df.describe()
    print(describe)

    # Gráfico de frecuencia de las tiendas
    frequency_shops = filtered_df["Shop"].value_counts().head(10)
    df_frequency_shops = pd.DataFrame({"shops": frequency_shops.index.tolist(), "quantity": frequency_shops.tolist()})
    sns.barplot(x="shops", y="quantity", data=df_frequency_shops)
    plt.title("Frecuencia de las Tiendas")
    plt.show()

    # Gráficos de frecuencia para variables categóricas
    for cat_variable in categorical_variables:
        frequency = filtered_df[cat_variable].value_counts()
        df_frequency = pd.DataFrame({cat_variable: frequency.index.tolist(), "quantity": frequency.tolist()})
        sns.barplot(x=cat_variable, y="quantity", data=df_frequency)
        plt.title(f"Frecuencia de {cat_variable}")
        plt.show()

    # Histogramas para variables numéricas
    for num_variable in numerical_variables:
        sns.histplot(filtered_df[num_variable], bins="auto")
        plt.title(f"Histograma de {num_variable}")
        plt.show()

    # Matriz de correlación
    corr = filtered_df.corr()
    sns.heatmap(corr, vmin=-1, vmax=1, center=0, cmap=sns.diverging_palette(20, 220, n=200), square=True)
    plt.title("Matriz de Correlación")
    plt.show()

    # Agrupamiento y cálculos estadísticos
    grouped = (
        filtered_df[
            (filtered_df["Year"] != 2014)
            & (filtered_df["Gender"] == "Male")
            & (filtered_df["Country"] == "United States")
        ]
        .groupby(["Size (US)", "Year", "Month"])
        .size()
        .unstack(level=0)
        .fillna(value=0)
    )

    means = []
    standard_errors = []
    for column in grouped.columns:
        means.append(grouped[column].mean())
        standard_errors.append(grouped[column].sem())

    d = {"means": means, "std_error": standard_errors}
    df_calculations = pd.DataFrame(data=d, index=grouped.columns)

    # Calcular el margen de error
    df_calculations["error_margin"] = df_calculations["std_error"].apply(lambda x: x * 2.07)
    # Calcular los márgenes inferiores y superiores
    df_calculations["low_margin"] = df_calculations.apply(lambda x: x["means"] - x["error_margin"], axis=1)
    df_calculations["up_margin"] = df_calculations.apply(lambda x: x["means"] + x["error_margin"], axis=1)
    # Redondear al alza los márgenes superiores
    df_calculations["math_round_up"] = df_calculations.apply(lambda x: math.ceil(x["up_margin"]), axis=1)

    print(df_calculations)


df = cargar_data()

# Definir las variables categóricas y numéricas
categorical_variables = ["Country", "ProductID", "Shop", "Gender", "Size (US)", "Discount", "Year", "Month"]
numerical_variables = ["UnitPrice", "SalePrice"]

root = tkinter.Tk()
root.title("Título")

year_var = tkinter.StringVar()
size_var = tkinter.StringVar()
shop_var = tkinter.StringVar()
gender_var = tkinter.StringVar()

ttk.Label(root, text="Año:").grid(row=0, column=0)
ttk.Entry(root, textvariable=year_var).grid(row=0, column=1)

ttk.Label(root, text="Talla (US):").grid(row=1, column=0)
ttk.Entry(root, textvariable=size_var).grid(row=1, column=1)

ttk.Label(root, text="Tienda:").grid(row=2, column=0)
ttk.Entry(root, textvariable=shop_var).grid(row=2, column=1)

ttk.Label(root, text="Género:").grid(row=3, column=0)
ttk.Entry(root, textvariable=gender_var).grid(row=3, column=1)

ttk.Button(root, text="Aplicar Filtros", command=filtros).grid(row=4, column=0, columnspan=2)

root.mainloop()
