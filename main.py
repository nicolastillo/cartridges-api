
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
        valor = valor.replace("mm", "").replace(",", ".").strip()
    try:
        return float(valor)
    except:
        return None

all_cartridges["PLATO_MM"] = all_cartridges.iloc[:, 11].apply(limpiar_medida)
all_cartridges["COMPRESORA_ARRIBA_MM"] = all_cartridges.iloc[:, 5].apply(limpiar_medida)
all_cartridges["COMPRESORA_ABAJO_MM"] = all_cartridges.iloc[:, 6].apply(limpiar_medida)

@app.get("/buscar-referencia")
def buscar_referencia(q: str = Query(..., description="Texto parcial de la referencia")):
    columna_ref = all_cartridges.columns[1]
    columnas_tecnicas = [
        columna_ref,
        all_cartridges.columns[0],
        all_cartridges.columns[2],
        all_cartridges.columns[3],
        all_cartridges.columns[4],
        all_cartridges.columns[5],
        all_cartridges.columns[6],
        all_cartridges.columns[11],
        all_cartridges.columns[8],
        all_cartridges.columns[9],
        all_cartridges.columns[7],
        all_cartridges.columns[21] if len(all_cartridges.columns) > 21 else None,
        all_cartridges.columns[13],
        all_cartridges.columns[14],
        all_cartridges.columns[15],
    ]
    columnas_tecnicas = [c for c in columnas_tecnicas if c is not None]

    exactos = all_cartridges[all_cartridges[columna_ref].astype(str).str.lower() == q.lower()]
    if len(exactos) == 1:
        df = exactos[columnas_tecnicas].copy()
    else:
        parciales = all_cartridges[all_cartridges[columna_ref].astype(str).str.contains(q, case=False, na=False)]
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
        all_cartridges.columns[1],
        all_cartridges.columns[0],
        all_cartridges.columns[2],
        all_cartridges.columns[3],
        all_cartridges.columns[4],
        all_cartridges.columns[5],
        all_cartridges.columns[6],
        all_cartridges.columns[11],
        all_cartridges.columns[8],
        all_cartridges.columns[9],
        all_cartridges.columns[7],
        all_cartridges.columns[21] if len(all_cartridges.columns) > 21 else None,
        all_cartridges.columns[13],
        all_cartridges.columns[14],
        all_cartridges.columns[15],
    ]
    columnas_tecnicas = [c for c in columnas_tecnicas if c is not None]

    df_filtrado = all_cartridges[
        (all_cartridges[columna].notna()) &
        (all_cartridges[columna] >= min) &
        (all_cartridges[columna] <= max)
    ]

    df_filtrado = df_filtrado[columnas_tecnicas].copy()
    df_filtrado = df_filtrado.replace([float("inf"), float("-inf")], None)
    df_filtrado = df_filtrado.where(pd.notnull(df_filtrado), None)

    return {"total": len(df_filtrado), "resultados": df_filtrado.to_dict(orient="records")}
