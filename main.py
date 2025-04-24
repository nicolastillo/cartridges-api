
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

app = FastAPI()

# CORS para permitir acceso desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar Excel al inicio
excel_path = "MEDIDAS_CARTRIDGES.xlsx"
excel_file = pd.ExcelFile(excel_path)

cartridges_turbochina = excel_file.parse('CARTRIDGES TURBOCHINA')
cartridges_zeki = excel_file.parse('CARTRIDGES ZEKI')
cartridges_originales = excel_file.parse('CARTRIDGES ORIGINALES')

all_cartridges = pd.concat([cartridges_turbochina, cartridges_zeki, cartridges_originales], ignore_index=True)

def limpiar_medida(valor):
    if isinstance(valor, str):
        valor = valor.replace('mm', '').replace(',', '.').strip()
    try:
        return float(valor)
    except:
        return None

# Crear columnas numéricas
all_cartridges['PLATO_MM'] = all_cartridges.iloc[:, 11].apply(limpiar_medida)
all_cartridges['COMPRESORA_ARRIBA_MM'] = all_cartridges.iloc[:, 5].apply(limpiar_medida)
all_cartridges['COMPRESORA_ABAJO_MM'] = all_cartridges.iloc[:, 6].apply(limpiar_medida)

@app.get("/buscar-referencia")
def buscar_referencia(q: str = Query(..., description="Texto parcial de la referencia")):
    columna_ref = all_cartridges.columns[1]
    columnas_tecnicas = [
        columna_ref,
        all_cartridges.columns[0],   # Fabricante
        all_cartridges.columns[2],   # Modelo
        all_cartridges.columns[3],   # Cilindraje
        all_cartridges.columns[4],   # Motor
        all_cartridges.columns[5],   # Compresora arriba
        all_cartridges.columns[6],   # Compresora abajo
        all_cartridges.columns[11],  # Plato
        all_cartridges.columns[8],   # Eje arriba
        all_cartridges.columns[9],   # Eje abajo
        all_cartridges.columns[7],   # Alabes compresora
        all_cartridges.columns[21] if len(all_cartridges.columns) > 21 else None,  # Alabes eje
        all_cartridges.columns[13],  # Refrigeración por agua
        all_cartridges.columns[14],  # Geometría variable
        all_cartridges.columns[15],  # Material
    ]

    # Eliminar cualquier columna que sea None
    columnas_tecnicas = [c for c in columnas_tecnicas if c is not None]

    coincidencias = all_cartridges[
        all_cartridges[columna_ref].astype(str).str.contains(q, case=False, na=False)
    ]

    # Limpiar antes de convertir a dict
    resultados = coincidencias[columnas_tecnicas].copy()
    resultados = resultados.replace([float("inf"), float("-inf")], None)
    resultados = resultados.where(pd.notnull(resultados), None)

    return {
        "total": len(resultados),
        "referencias": resultados.to_dict(orient="records")
    }
