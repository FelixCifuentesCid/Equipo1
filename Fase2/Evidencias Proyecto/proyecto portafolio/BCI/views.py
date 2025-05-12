from django.shortcuts import render, redirect
from django.contrib import messages
import pandas as pd
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login



def login(request):
    context = {}
    return render(request, 'finantrack/login.html', context)


def categorizar(descripcion):
    descripcion = descripcion.lower()
    if 'supermercado' in descripcion or 'líder' in descripcion or 'jumbo' in descripcion or 'tottus' in descripcion:
        return 'Supermercado'
    if any(palabra in descripcion for palabra in ['farmacia', 'salcobrand', 'sb', ' ino ', 'cruz verde', 'clinica']):
        return 'Salud/Farmacia'
    if any(palabra in descripcion for palabra in ['uber', 'cabify', 'buses']):
        return 'Transporte'
    if any(palabra in descripcion for palabra in ['starbucks', 'domino','donalds', 'dg', 'carne', 'jireh', 'papa john']):
        return 'Comida'
    if any(palabra in descripcion for palabra in ['agua', 'enel', 'movistar', 'wom', 'telefonica', 'claro']):
        return 'Servicios Básicos'
    if any(palabra in descripcion for palabra in ['banco', 'cajero']):
        return 'Giro'
    if any(palabra in descripcion for palabra in ['crédito','hipotecario']):
        return 'Credito'
    if any(palabra in descripcion for palabra in ['transf']):
        return 'Transferencias'
    if 'komax' in descripcion:
        return 'Sueldo'
    return 'Otros'

def index(request):
    context = {}
    if request.method == 'POST' and 'archivo' in request.FILES:
        archivo = request.FILES['archivo']
        try:
            if archivo.name.endswith('.xlsx'):
                preview = pd.read_excel(archivo, engine='openpyxl', nrows=1, header=None) # Elimina separadores de miles
                if str(preview.iloc[0, 0]).strip().lower() == "fecha":
                    df = pd.read_excel(archivo, engine='openpyxl', skiprows=0, dtype=str)
                    print("Archivo detectado: Falabella")
                    print(df.head())
                else:
                    df = pd.read_excel(archivo, engine='openpyxl', skiprows=7, dtype=str)
                    print("Archivo detectado: BCI")
                    print(df.head())
            elif archivo.name.endswith('.xls'):
                df = pd.read_excel(archivo, engine='xlrd', skiprows=0, dtype=str)
            elif archivo.name.endswith('.csv'):
                df = pd.read_csv(archivo)
            else:
                messages.error(request, 'Formato no soportado. Sube un archivo .xls, .xlsx o .csv.')
                return redirect('index')

            # Limpiar nombres de columnas
            df.columns = df.columns.str.strip()
            df.columns = df.columns.str.replace(r'[^\w\s]', '', regex=True)  # Quita $ y símbolos
            df.columns = df.columns.str.replace(r'\s+', ' ', regex=True)  # Espacios múltiples
            df.columns = df.columns.str.lower().str.strip()

            # Renombrar columnas clave
            df.rename(columns={
                'fecha transacción': 'Fecha',
                'fecha': 'Fecha',
                'fecha contable': 'Fecha contable',
                'descripción': 'Descripción',
                'descripcion': 'Descripción',
                'cargo': 'Cargo',
                'abono': 'Abono'
            }, inplace=True)

            # Verificación mínima
            if 'Descripción' not in df.columns:
                raise Exception("Columna requerida no encontrada: 'Descripción'")
            if 'Cargo' not in df.columns:
                raise Exception("Columna requerida no encontrada: 'Cargo'")
            if 'Abono' not in df.columns:
                raise Exception("Columna requerida no encontrada: 'Abono'")

            # Limpiar y convertir montos
            for col in ['Cargo', 'Abono']:
                df[col] = (
                    df[col].astype(str)
                        .str.replace('.', '', regex=False)    # Elimina separadores de miles
                        .str.replace(',', '.', regex=False)   # Cambia coma decimal por punto
                        .str.replace(r'\s+', '', regex=True) 
                        .str.replace(r'[^\w\s]', '', regex=True) # Elimina espacios en blanco
                        .replace('nan', '0')                     # Vacíos a cero
                        .astype(float)                        # Convierte a float
                )

            # Procesar fechas si existe
            if 'Fecha' in df.columns:
                df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce', dayfirst=True)

            # Categorizar movimientos
            df['Categoría'] = df['Descripción'].apply(categorizar)

            # Agrupar gastos
            gastos = df[df['Cargo'] > 0].groupby('Categoría')['Cargo'].sum().sort_values(ascending=False).to_dict()
            abono = df[df['Abono'] > 0].groupby('Categoría')['Abono'].sum().sort_values(ascending=False).to_dict()

            context = {
                'datos': df.to_dict(orient='records'),
                'saldo_actual': df['Abono'].sum() - df['Cargo'].sum(),
                'total_abonos': df['Abono'].sum(),
                'total_cargos': df['Cargo'].sum(),
                'fechas': df['Fecha'].dt.strftime('%d-%m-%Y').tolist() if 'Fecha' in df.columns else [],
                'saldos': [],  # Puedes calcular saldos acumulados si lo deseas
                'gastos_categoria': gastos,
                'abonos_categoria': abono,
            }


            messages.success(request, '¡Cartola cargada exitosamente!')

        except Exception as e:
            messages.error(request, f'Ocurrió un error al procesar el archivo: {str(e)}')

    return render(request, 'finantrack/index.html', context)





def registro_usuario(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)  # Inicia sesión automáticamente
            return redirect('perfil_usuario')  # Redirige al perfil
    else:
        form = UserCreationForm()
    return render(request, 'finantrack/registro.html', {'form': form})
