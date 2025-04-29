from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'mi_secreto'

# Variables globales
datos = []
saldo_actual = 0
total_abonos = 0
total_cargos = 0
fechas = []
saldos = []
gastos_categoria = {}

@app.route('/')
def home():
    return render_template('home.html',
                           datos=datos,
                           saldo_actual=saldo_actual,
                           total_abonos=total_abonos,
                           total_cargos=total_cargos,
                           fechas=fechas,
                           saldos=saldos,
                           gastos_categoria=gastos_categoria)

@app.route('/cargar_cartola', methods=['POST'])
def cargar_cartola():
    global datos, saldo_actual, total_abonos, total_cargos, fechas, saldos, gastos_categoria

    if 'archivo' not in request.files:
        flash('No se encontró ningún archivo.')
        return redirect(url_for('home'))

    archivo = request.files['archivo']

    if archivo.filename == '':
        flash('No seleccionaste ningún archivo.')
        return redirect(url_for('home'))

    if archivo:
        try:
            if archivo.filename.endswith('.xlsx'):
                df = pd.read_excel(archivo)
            elif archivo.filename.endswith('.csv'):
                df = pd.read_csv(archivo)
            else:
                flash('Formato no soportado. Sube un archivo .xlsx o .csv.')
                return redirect(url_for('home'))

            # Normalizar
            df.columns = df.columns.str.strip()
            for col in ['Cargo', 'Abono', 'Saldo']:
                if col in df.columns:
                    df[col] = df[col].replace(r'[\$,]', '', regex=True)
                    df[col] = df[col].replace(r'\s+', '', regex=True)
                    df[col] = df[col].replace('', '0')
                    df[col] = df[col].astype(float)

            if 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce', dayfirst=True)

            # Categorizar gastos
            df['Categoría'] = df['Descripcion'].apply(categorizar)

            # Agrupar gastos por categoría (solo cargos, no abonos)
            gastos = df[df['Cargo'] > 0].groupby('Categoría')['Cargo'].sum().sort_values(ascending=False).to_dict()

            # Actualizar variables globales
            datos = df.to_dict(orient='records')
            saldo_actual = df['Saldo'].iloc[-1] if not df.empty else 0
            total_abonos = df['Abono'].sum()
            total_cargos = df['Cargo'].sum()
            fechas = df['Fecha'].dt.strftime('%d-%m-%Y').tolist()
            saldos = df['Saldo'].tolist()
            gastos_categoria = gastos

            flash('¡Cartola cargada exitosamente!')
            return redirect(url_for('home'))

        except Exception as e:
            flash(f'Ocurrió un error al procesar el archivo: {str(e)}')
            return redirect(url_for('home'))

def categorizar(descripcion):
    descripcion = descripcion.lower()
    if 'supermercado' in descripcion or 'líder' in descripcion or 'jumbo' in descripcion:
        return 'Supermercado'
    if 'farmacia' in descripcion or 'salcobrand' in descripcion or 'cruz verde' in descripcion:
        return 'Salud/Farmacia'
    if 'uber' in descripcion or 'cabify' in descripcion:
        return 'Transporte'
    if 'restaurant' in descripcion or 'mc donalds' in descripcion or 'dominos' in descripcion:
        return 'Comida'
    if 'servicio' in descripcion or 'luz' in descripcion or 'agua' in descripcion:
        return 'Servicios Básicos'
    if 'banco' in descripcion or 'cajero' in descripcion:
        return 'Finanzas'
    return 'Otros'

if __name__ == '__main__':
    app.run(debug=True)
