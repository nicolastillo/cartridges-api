
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
    # Usar columna 1 como referencia
    columna_ref = all_cartridges.columns[1]
    # Filtrar filas que contengan el texto buscado (sin importar mayúsculas/minúsculas)
    coincidencias = all_cartridges[
        all_cartridges[columna_ref].astype(str).str.contains(q, case=False, na=False)
    ]
    # Extraer solo los nombres de referencia
    refs = coincidencias[columna_ref].dropna().unique().tolist()
    return {"total": len(refs), "coincidencias": refs}
 
@app.get("/buscar-rango")
def buscar_rango(
    columna: str = Query(..., description="Nombre de la columna (ej: PLATO_MM, COMPRESORA_ARRIBA_MM)"),
    min: float = Query(..., description="Valor mínimo"),
    max: float = Query(..., description="Valor máximo")
):
    if columna not in all_cartridges.columns:
        return {"error": "Columna no válida"}

    df_filtrado = all_cartridges[
        (all_cartridges[columna].notna()) &
        (all_cartridges[columna] >= min) &
        (all_cartridges[columna] <= max)
    ]
    resultado = df_filtrado[[all_cartridges.columns[0], all_cartridges.columns[1], columna]].to_dict(orient="records")
    return {"total": len(resultado), "resultados": resultado}
