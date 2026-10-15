# Conciliación de facturas

## 1. Descripción del proyecto

Este proyecto es un prototipo de conciliación de facturas desarrollado como parte de una prueba técnica para el cargo de Analista III.

La aplicación permite cargar dos archivos CSV: uno con información de facturas y otro con registros contables. El sistema analiza las facturas, realiza validaciones básicas y muestra cuáles están correctas y cuáles presentan inconsistencias.

El objetivo es facilitar la revisión de información y ayudar a identificar posibles diferencias en los datos.

## 2. Tecnologías utilizadas

**Backend:**
- Python 3.14.7
- FastAPI
- pandas
- Uvicorn
- python-multipart

**Frontend:**
- Angular 22.2.3
- Angular CLI 22.2.2
- Node.js 24.22.0
- npm 11.19.1
- TypeScript

Las herramientas utilizadas son de libre acceso.

## 3. Estructura del proyecto

```text
conciliador-facturas-simple/
├── backend/
│   └── main.py
├── frontend/
├── pruebas/
│   ├── facturas.csv
│   └── contabilidad.csv
├── presentacion/
│   └── presentacion_prototipo.pdf
├── requirements.txt
├── README.md
└── .gitignore
```

Las carpetas `pruebas` y `presentacion` se incorporan como parte de la entrega final.

## 4. Requisitos previos

Para ejecutar el proyecto se necesita:

- Python 3.14.7
- Node.js 24.22.0
- npm 11.19.1
- Una terminal, por ejemplo PowerShell
- Un navegador web

Las versiones indicadas corresponden al entorno utilizado durante el desarrollo y las pruebas.

## 5. Instalación del backend

Abrir una terminal en la carpeta principal del proyecto.

Instalar las dependencias:

```powershell
py -m pip install -r requirements.txt
```

Iniciar el backend:

```powershell
py -m uvicorn main:app --app-dir backend --reload
```

El backend estará disponible en:

http://127.0.0.1:8000

También se puede consultar la documentación de la API en:

http://127.0.0.1:8000/docs

**Nota:** se utiliza el comando `py`. En otros sistemas puede ser necesario utilizar `python` o `python3`.

## 6. Instalación del frontend

Abrir una segunda terminal en la carpeta principal del proyecto.

Entrar a la carpeta del frontend:

```powershell
cd frontend
```

Instalar las dependencias:

```powershell
npm.cmd install
```

Iniciar Angular:

```powershell
npm.cmd start
```

Abrir en el navegador:

http://localhost:4200

**Nota:** se utiliza `npm.cmd` porque en el entorno Windows de desarrollo PowerShell restringía la ejecución directa de los scripts de npm. En otros entornos normalmente puede utilizarse `npm`.

## 7. Instrucciones de uso

1. Verificar que el backend y el frontend estén ejecutándose.
2. Abrir http://localhost:4200.
3. Seleccionar el archivo CSV de facturas.
4. Seleccionar el archivo CSV de contabilidad.
5. Presionar el botón para iniciar la conciliación.
6. Revisar el resumen de facturas correctas e inconsistentes.
7. Consultar los resultados y utilizar los filtros disponibles.

Los archivos deben tener encabezados con los nombres de columnas indicados a continuación.

### Archivo de facturas

```text
id_factura,nit_proveedor,fecha_factura,concepto,base_gravable,tarifa_iva,valor_iva,tarifa_retencion,valor_retencion,total_factura
```

### Archivo de contabilidad

```text
id_factura,fecha_contabilizacion,cuenta_contable,centro_costo,valor_debito,valor_credito,estado
```

El sistema admite archivos CSV separados por comas o punto y coma.

## 8. Validaciones implementadas

El backend revisa:

- Que los archivos contengan las columnas requeridas.
- Que cada factura tenga un identificador.
- Que no existan identificadores de factura duplicados dentro del archivo de facturas.
- Que exista al menos un registro contable asociado a la factura.
- Que al menos uno de los registros asociados tenga estado `Contabilizada`.
- Que los campos numéricos necesarios sean válidos.
- Que el IVA reportado coincida con el cálculo esperado.
- Que la retención reportada coincida con el cálculo esperado.
- Que el total reportado coincida con la base, el IVA y la retención reportados.

### Fórmulas utilizadas

**IVA esperado:**

`base_gravable × tarifa_iva`

**Retención esperada:**

`base_gravable × tarifa_retencion`

**Total esperado:**

`base_gravable + valor_iva - valor_retencion`

Las tarifas pueden estar expresadas como `0.19` o `19` para representar el 19 %.

Para las comparaciones se utiliza una tolerancia de hasta un peso, con el fin de admitir pequeñas diferencias de redondeo.

Si se encuentra una o varias diferencias, la factura se clasifica como `Con inconsistencia` y se muestran las causas. En caso contrario, se clasifica como `Correcta`.

## 9. Archivos de prueba y resultados esperados

Los archivos de prueba se incluyen en la carpeta `pruebas/` y contienen datos ficticios.

Para realizar la prueba:

1. Iniciar el backend y el frontend.
2. Cargar `pruebas/facturas.csv`.
3. Cargar `pruebas/contabilidad.csv`.
4. Ejecutar la conciliación.
5. Revisar los resultados mostrados en pantalla.

Durante las pruebas realizadas con el conjunto de datos de desarrollo se obtuvieron los siguientes resultados:

- Total de facturas: **50**
- Facturas correctas: **34**
- Facturas con inconsistencias: **16**

## 10. Decisiones técnicas y supuestos

- Se utilizó Python con FastAPI para implementar el servicio de conciliación.
- Se utilizó Angular para construir la interfaz web.
- Se utilizó pandas para leer y recorrer los datos de los CSV.
- Se utilizó `Decimal` para controlar la precisión de los cálculos monetarios.
- Las facturas se relacionan con los registros contables mediante `id_factura`.
- Una factura puede tener varios movimientos contables asociados.
- Los movimientos contables múltiples no se consideran automáticamente facturas duplicadas.
- Se admite una diferencia máxima de un peso en las comparaciones numéricas.
- El prototipo está orientado a demostrar el flujo principal, no a reemplazar un sistema contable de producción.

## 11. Limitaciones y funcionalidades no implementadas

- No se implementó autenticación ni gestión de usuarios.
- No se utiliza una base de datos; el procesamiento se realiza a partir de los archivos cargados.
- No se almacenan históricos de conciliación.
- No se implementó exportación de resultados.
- No se comprueba que los valores de débito y crédito coincidan con el total de la factura.
- No se validan todas las reglas tributarias aplicables a escenarios reales.
- La validación de archivos se concentra en la estructura y los datos necesarios para la conciliación básica.
- No se implementaron funcionalidades avanzadas de producción, como auditoría, control de acceso o procesamiento de grandes volúmenes.

## 12. Uso de inteligencia artificial generativa

**Se utilizó ChatGPT como herramienta de apoyo durante el desarrollo del prototipo, principalmente para la generación y organización de código, así como para la identificación y corrección de errores.**

Su utilización incluyó:

- **Backend:**  apoyo en la implementación de la lectura de archivos CSV, las validaciones, los cálculos y las respuestas de la API.
- **Frontend:** apoyo en la construcción de componentes, la carga de archivos, el consumo de la API, la visualización de resultados y los estilos de la interfaz.
- **Depuración:** apoyo para identificar y corregir problemas durante la ejecución y comunicación entre frontend y backend.

La solución fue ejecutada y probada manualmente durante el desarrollo. Se verificó la carga de archivos, la comunicación entre Angular y FastAPI, el procesamiento de los datos y la visualización de resultados.

El uso de inteligencia artificial se declara de manera explícita como parte de la transparencia del proceso de desarrollo.

## 13. Consideraciones sobre los datos

Los archivos de prueba entregados deben contener información ficticia. No se deben incluir credenciales, información real de proveedores ni datos contables sensibles.

## 14. Ejecución resumida

**Terminal 1 — Backend:**

```powershell
py -m pip install -r requirements.txt
py -m uvicorn main:app --app-dir backend --reload
```

**Terminal 2 — Frontend:**

```powershell
cd frontend
npm.cmd install
npm.cmd start
```

**Aplicación:**

http://localhost:4200