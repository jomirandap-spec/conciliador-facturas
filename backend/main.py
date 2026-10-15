
from io import StringIO
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware


# ==========================================
# 1. CONFIGURACIÓN DE LA APLICACIÓN
# ==========================================

app = FastAPI(title="Conciliador de Facturas")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Se permite una diferencia máxima de 1 peso
# para evitar problemas menores de redondeo.
TOLERANCIA = Decimal("1.00")


# ==========================================
# 2. COLUMNAS ESPERADAS EN LOS CSV
# ==========================================

# Las 10 columnas de facturas.csv
CAMPOS_FACTURAS = [
    "id_factura",
    "nit_proveedor",
    "fecha_factura",
    "concepto",
    "base_gravable",
    "tarifa_iva",
    "valor_iva",
    "tarifa_retencion",
    "valor_retencion",
    "total_factura",
]

# Las 7 columnas de contabilidad.csv
CAMPOS_CONTABILIDAD = [
    "id_factura",
    "fecha_contabilizacion",
    "cuenta_contable",
    "centro_costo",
    "valor_debito",
    "valor_credito",
    "estado",
]


# ==========================================
# 3. FUNCIONES PARA LEER Y VALIDAR ARCHIVOS
# ==========================================

def leer_csv(contenido, nombre_archivo):
    """
    Lee un CSV y detecta si está separado
    por comas o punto y coma.
    """

    if not contenido:
        raise ValueError(
            f"El archivo {nombre_archivo} está vacío."
        )

    # Intentar distintas codificaciones.
    texto = None

    for codificacion in ["utf-8-sig", "cp1252"]:
        try:
            texto = contenido.decode(codificacion)
            break
        except UnicodeDecodeError:
            continue

    if texto is None:
        raise ValueError(
            f"No se pudo interpretar el archivo {nombre_archivo}."
        )

    try:
        df = pd.read_csv(
            StringIO(texto),
            sep=None,
            engine="python",
            dtype=str,
            keep_default_na=False,
        )

        # Eliminar espacios innecesarios
        # en los nombres de las columnas.
        df.columns = df.columns.str.strip()

        if df.empty:
            raise ValueError(
                "El archivo no contiene registros."
            )

        if df.columns.duplicated().any():
            raise ValueError(
                "El archivo tiene columnas repetidas."
            )

        return df

    except Exception as error:
        raise ValueError(
            f"Error leyendo {nombre_archivo}: {error}"
        ) from error


def validar_columnas(df, columnas_esperadas, nombre):
    """
    Comprueba que el CSV tenga todas las columnas requeridas.
    """

    faltantes = [
        columna
        for columna in columnas_esperadas
        if columna not in df.columns
    ]

    if faltantes:
        raise ValueError(
            f"Al archivo {nombre} le faltan "
            f"estas columnas: {', '.join(faltantes)}"
        )


def convertir_numero(valor):
    """
    Convierte valores numéricos a Decimal.   
    """

    texto = str(valor).strip().replace(" ", "")

    if not texto:
        return None

    # Si usa coma y punto, el último separador
    # se interpreta como decimal.
    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "")
            texto = texto.replace(",", ".")
        else:
            texto = texto.replace(",", "")

    elif "," in texto:
        texto = texto.replace(",", ".")

    try:
        numero = Decimal(texto)

        if not numero.is_finite():
            return None

        return numero

    except InvalidOperation:
        return None


def convertir_tarifa(valor):
    
    tarifa = convertir_numero(valor)

    if tarifa is None:
        return None

    if tarifa > 1:
        tarifa = tarifa / Decimal("100")

    return tarifa


def redondear_pesos(valor):
    """
    Redondea los cálculos a dos decimales.
    """

    return valor.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def numero_respuesta(valor):
    """
    Convierte Decimal a un número
    que pueda enviarse en la respuesta JSON.
    """

    if valor is None:
        return None

    return float(valor)


# ==========================================
# 4. FUNCIÓN PRINCIPAL DE CONCILIACIÓN
# ==========================================

def conciliar(facturas, contabilidad):

    # Validar que estén las 10 y 7 columnas.
    validar_columnas(
        facturas,
        CAMPOS_FACTURAS,
        "facturas.csv",
    )

    validar_columnas(
        contabilidad,
        CAMPOS_CONTABILIDAD,
        "contabilidad.csv",
    )

    # Copias para no modificar los datos originales.
    facturas = facturas.copy()
    contabilidad = contabilidad.copy()

    # Normalizar los identificadores de factura.
    facturas["id_factura"] = (
        facturas["id_factura"].astype(str).str.strip()
    )

    contabilidad["id_factura"] = (
        contabilidad["id_factura"].astype(str).str.strip()
    )

    # Detectar identificadores duplicados
    # dentro del archivo de facturas.
    ids_duplicados = set(
        facturas.loc[
            (facturas["id_factura"] != "")
            & facturas["id_factura"].duplicated(keep=False),
            "id_factura",
        ]
    )

    # Agrupar registros contables por factura.
    # Una factura podría tener varios movimientos
    # contables, por lo que no se considera
    # automáticamente duplicados.
    registros_contables = {}

    for _, registro in contabilidad.iterrows():
        identificador = registro["id_factura"]

        if identificador:
            registros_contables.setdefault(
                identificador, []
            ).append(registro)

    resultados = []

    # Revisar las facturas una por una.
    for _, factura in facturas.iterrows():

        causas = []

        id_factura = factura["id_factura"]
        nit_proveedor = str(
            factura["nit_proveedor"]
        ).strip()

        fecha_factura = str(
            factura["fecha_factura"]
        ).strip()

        concepto = str(
            factura["concepto"]
        ).strip()

        # ----------------------------------
        # REGLA 1: Identificador obligatorio
        # ----------------------------------

        if not id_factura:
            causas.append(
                "La factura no tiene identificador."
            )

        # ----------------------------------
        # REGLA 2: Facturas duplicadas
        # ----------------------------------

        if id_factura in ids_duplicados:
            causas.append(
                "Factura duplicada en el archivo."
            )

        # ----------------------------------
        # REGLA 3: Existencia contable
        # ----------------------------------

        movimientos = registros_contables.get(
            id_factura, []
        )

        if not movimientos:
            causas.append(
                "La factura no tiene registro contable."
            )

        # ----------------------------------
        # REGLA 4: Estado contable
        # ----------------------------------

        estados_contables = [
            str(movimiento["estado"]).strip()
            for movimiento in movimientos
        ]

        # Regla complementaria:
        # comprobar si algún registro está
        # marcado como Contabilizada.
        if movimientos:
            esta_contabilizada = any(
                estado.lower() == "contabilizada"
                for estado in estados_contables
            )

            if not esta_contabilizada:
                causas.append(
                    "La factura no tiene un registro "
                    "con estado Contabilizada."
                )

        # ----------------------------------
        # REGLA 5: Convertir valores numéricos
        # ----------------------------------

        base = convertir_numero(
            factura["base_gravable"]
        )

        tarifa_iva = convertir_tarifa(
            factura["tarifa_iva"]
        )

        iva_reportado = convertir_numero(
            factura["valor_iva"]
        )

        tarifa_retencion = convertir_tarifa(
            factura["tarifa_retencion"]
        )

        retencion_reportada = convertir_numero(
            factura["valor_retencion"]
        )

        total_reportado = convertir_numero(
            factura["total_factura"]
        )

        valores = [
            base,
            tarifa_iva,
            iva_reportado,
            tarifa_retencion,
            retencion_reportada,
            total_reportado,
        ]

        datos_numericos_validos = all(
            valor is not None
            for valor in valores
        )

        iva_esperado = None
        retencion_esperada = None
        total_esperado = None

        if not datos_numericos_validos:
            causas.append(
                "La factura tiene campos "
                "numéricos vacíos o inválidos."
            )

        else:
            # ------------------------------
            # REGLA 6: Validar IVA
            # ------------------------------

            iva_esperado = redondear_pesos(
                base * tarifa_iva
            )

            diferencia_iva = abs(
                iva_reportado - iva_esperado
            )

            if diferencia_iva > TOLERANCIA:
                causas.append(
                    "El valor del IVA no coincide "
                    "con base_gravable x tarifa_iva."
                )

            # ------------------------------
            # REGLA 7: Validar retención
            # ------------------------------

            retencion_esperada = redondear_pesos(
                base * tarifa_retencion
            )

            diferencia_retencion = abs(
                retencion_reportada
                - retencion_esperada
            )

            if diferencia_retencion > TOLERANCIA:
                causas.append(
                    "El valor de la retención no "
                    "coincide con base_gravable "
                    "x tarifa_retencion."
                )

            # ------------------------------
            # REGLA 8: Validar total
            # ------------------------------

            total_esperado = redondear_pesos(
                base
                + iva_reportado
                - retencion_reportada
            )

            diferencia_total = abs(
                total_reportado - total_esperado
            )

            if diferencia_total > TOLERANCIA:
                causas.append(
                    "El total de la factura no "
                    "coincide con base + IVA "
                    "- retención."
                )

        # ----------------------------------
        # CLASIFICACIÓN FINAL
        # ----------------------------------

        estado_resultado = (
            "Con inconsistencia"
            if causas
            else "Correcta"
        )

        # Datos contables para mostrar en Angular.
        detalles_contables = []

        for movimiento in movimientos:
            detalles_contables.append({
                "fecha_contabilizacion": str(
                    movimiento["fecha_contabilizacion"]
                ).strip(),
                "cuenta_contable": str(
                    movimiento["cuenta_contable"]
                ).strip(),
                "centro_costo": str(
                    movimiento["centro_costo"]
                ).strip(),
                "valor_debito": str(
                    movimiento["valor_debito"]
                ).strip(),
                "valor_credito": str(
                    movimiento["valor_credito"]
                ).strip(),
                "estado": str(
                    movimiento["estado"]
                ).strip(),
            })

        # Guardar el resultado.
        resultados.append({
            "id_factura": id_factura,
            "nit_proveedor": nit_proveedor,
            "fecha_factura": fecha_factura,
            "concepto": concepto,
            "base_gravable": numero_respuesta(base),
            "tarifa_iva": numero_respuesta(tarifa_iva),
            "valor_iva": numero_respuesta(iva_reportado),
            "iva_esperado": numero_respuesta(iva_esperado),
            "tarifa_retencion": numero_respuesta(
                tarifa_retencion
            ),
            "valor_retencion": numero_respuesta(
                retencion_reportada
            ),
            "retencion_esperada": numero_respuesta(
                retencion_esperada
            ),
            "total_factura": numero_respuesta(
                total_reportado
            ),
            "total_esperado": numero_respuesta(
                total_esperado
            ),
            "registros_contables": detalles_contables,
            "estado": estado_resultado,
            "causas": causas,
        })

    # ======================================
    # 5. RESUMEN GENERAL
    # ======================================

    total_facturas = len(resultados)

    inconsistencias = sum(
        resultado["estado"] == "Con inconsistencia"
        for resultado in resultados
    )

    correctas = total_facturas - inconsistencias

    return {
        "resumen": {
            "total_facturas": total_facturas,
            "correctas": correctas,
            "inconsistencias": inconsistencias,
        },
        "resultados": resultados,
    }


# ==========================================
# 6. RUTAS DE LA API
# ==========================================

@app.get("/")
def inicio():
    return {
        "mensaje": "API del conciliador funcionando"
    }


@app.post("/conciliar")
async def procesar_archivos(
    archivo_facturas: UploadFile = File(...),
    archivo_contabilidad: UploadFile = File(...),
):

    # Comprobar extensión de los archivos.
    if (
        not archivo_facturas.filename
        or not archivo_facturas.filename.lower().endswith(".csv")
    ):
        raise HTTPException(
            status_code=400,
            detail="El archivo de facturas debe ser CSV.",
        )

    if (
        not archivo_contabilidad.filename
        or not archivo_contabilidad.filename.lower().endswith(".csv")
    ):
        raise HTTPException(
            status_code=400,
            detail="El archivo de contabilidad debe ser CSV.",
        )

    try:
        # Leer los archivos enviados por Angular.
        facturas = leer_csv(
            await archivo_facturas.read(),
            archivo_facturas.filename,
        )

        contabilidad = leer_csv(
            await archivo_contabilidad.read(),
            archivo_contabilidad.filename,
        )

        # Ejecutar conciliación.
        resultado = conciliar(
            facturas,
            contabilidad,
        )

        return resultado

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
