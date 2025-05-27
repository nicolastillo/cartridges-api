
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

excel_path = "MEDIDAS_CARTRIDGES.xlsx"
excel_file = pd.ExcelFile(excel_path)

cartridges_turbochina = excel_file.parse("CARTRIDGES TURBOCHINA")
cartridges_zeki = excel_file.parse("CARTRIDGES ZEKI")
cartridges_originales = excel_file.parse("CARTRIDGES ORIGINALES")

all_cartridges = pd.concat([cartridges_turbochina, cartridges_zeki, cartridges_originales], ignore_index=True)

def limpiar_medida(valor):
    if isinstance(valor, str):
        valor = valor.lower().replace("mm", "").replace(",", ".").strip()
    try:
        return float(valor)
    except:
        return None

# Función segura para asignar columna limpia
def safe_assign(column_search, new_column):
    matches = [col for col in all_cartridges.columns if col.strip().upper() == column_search]
    if matches:
        all_cartridges[new_column] = all_cartridges[matches[0]].apply(limpiar_medida)

safe_assign("COMPRESORA ARRIBA", "COMPRESORA_ARRIBA_MM")
safe_assign("COMPRESORA ABAJO", "COMPRESORA_ABAJO_MM")
safe_assign("PLATO", "PLATO_MM")

@app.get("/buscar-referencia")
def buscar_referencia(q: str = Query(..., description="Texto parcial de la referencia")):
    col_ref = "REFERENCIA DTF"
    if col_ref not in all_cartridges.columns:
        return {"error": f"Columna '{col_ref}' no encontrada"}

    columnas_tecnicas = [
        "FABRICANTE ORIGEN", "REFERENCIA DTF", "MODELO", "CILINDRAJE", "MOTOR",
        "COMPRESORA ARRIBA", "COMPRESORA ABAJO", "ALABES COMPRESORA",
        "EJE ARRIBA", "EJE ABAJO", "ALABES EJE", "PLATO",
        "REFRIGERACIÓN POR AGUA", "GEOMETRÍA", "MATERIAL"
    ]
    columnas_tecnicas = [col for col in columnas_tecnicas if col in all_cartridges.columns]

    exactos = all_cartridges[all_cartridges[col_ref].astype(str).str.lower() == q.lower()]
    if len(exactos) == 1:
        df = exactos[columnas_tecnicas].copy()
    else:
        parciales = all_cartridges[all_cartridges[col_ref].astype(str).str.contains(q, case=False, na=False)]
        df = parciales[columnas_tecnicas].copy()

    df = df.replace([float("inf"), float("-inf")], None)
    df = df.where(pd.notnull(df), None)

    return {"total": len(df), "referencias": df.to_dict(orient="records")}

@app.get("/buscar-rango")
def buscar_rango(
    columna: str = Query(...),
    min: float = Query(...),
    max: float = Query(...)
):
    if columna not in all_cartridges.columns:
        return {"error": "Columna no válida"}

    columnas_tecnicas = [
        "FABRICANTE ORIGEN", "REFERENCIA DTF", "MODELO", "CILINDRAJE", "MOTOR",
        "COMPRESORA ARRIBA", "COMPRESORA ABAJO", "ALABES COMPRESORA",
        "EJE ARRIBA", "EJE ABAJO", "ALABES EJE", "PLATO",
        "REFRIGERACIÓN POR AGUA", "GEOMETRÍA", "MATERIAL"
    ]
    columnas_tecnicas = [col for col in columnas_tecnicas if col in all_cartridges.columns]

    df_filtrado = all_cartridges[
        (all_cartridges[columna].notna()) &
        (all_cartridges[columna] >= min) &
        (all_cartridges[columna] <= max)
    ]

    df_filtrado = df_filtrado[columnas_tecnicas].copy()
    df_filtrado = df_filtrado.replace([float("inf"), float("-inf")], None)
    df_filtrado = df_filtrado.where(pd.notnull(df_filtrado), None)

    return {"total": len(df_filtrado), "resultados": df_filtrado.to_dict(orient="records")}
