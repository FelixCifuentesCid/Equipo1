import pandas as pd

# 1. Cargar el archivo .xls
archivo = 'cartola.xls'  # <--- cambia esta ruta por la tuya
df = pd.read_excel(archivo)

# 2. Renombrar columnas (por si hay espacios o problemas)
df.columns = ['Fecha', 'Descripcion', 'Cargo', 'Abono', 'Saldo']

# 3. Limpiar datos: eliminar '$' y '.' en Cargo, Abono y Saldo, convertirlos a número
for col in ['Cargo', 'Abono', 'Saldo']:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace('$', '', regex=False)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)  # Por si usara comas para decimales
        .str.strip()
    )
    df[col] = pd.to_numeric(df[col], errors='coerce')  # Convierte a número

# 4. Convertir la columna Fecha a formato datetime
df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d-%m-%Y')

# 5. Mostrar primeras filas
print(df.head())
