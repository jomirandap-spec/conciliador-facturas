
import { CommonModule } from '@angular/common';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectorRef, Component } from '@angular/core';
import { FormsModule } from '@angular/forms';

interface RegistroContable {
  fecha_contabilizacion: string;
  cuenta_contable: string;
  centro_costo: string;
  valor_debito: string;
  valor_credito: string;
  estado: string;
}

interface ResultadoFactura {
  id_factura: string;
  nit_proveedor: string;
  fecha_factura: string;
  concepto: string;
  base_gravable: number | null;
  tarifa_iva: number | null;
  valor_iva: number | null;
  iva_esperado: number | null;
  tarifa_retencion: number | null;
  valor_retencion: number | null;
  retencion_esperada: number | null;
  total_factura: number | null;
  total_esperado: number | null;
  registros_contables: RegistroContable[];
  estado: string;
  causas: string[];
}

interface RespuestaConciliacion {
  resumen: {
    total_facturas: number;
    correctas: number;
    inconsistencias: number;
  };
  resultados: ResultadoFactura[];
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {

  // Archivos seleccionados
  archivoFacturas: File | null = null;
  archivoContabilidad: File | null = null;

  // Datos recibidos desde Python
  respuesta: RespuestaConciliacion | null = null;

  // Estado de la pantalla
  cargando = false;
  error = '';
  filtro = 'Todas';
  busqueda = '';

  constructor(
  private http: HttpClient,
  private cdr: ChangeDetectorRef
  ) {}

  seleccionarFacturas(evento: Event): void {
    const input = evento.target as HTMLInputElement;

    this.archivoFacturas = input.files?.[0] ?? null;
    this.respuesta = null;
    this.error = '';
  }

  seleccionarContabilidad(evento: Event): void {
    const input = evento.target as HTMLInputElement;

    this.archivoContabilidad = input.files?.[0] ?? null;
    this.respuesta = null;
    this.error = '';
  }

  conciliar(): void {

    // Validar selección de archivos
    if (!this.archivoFacturas || !this.archivoContabilidad) {
      this.error = 'Debes seleccionar los dos archivos CSV.';
      return;
    }

    // Validar extensiones
    if (
      !this.archivoFacturas.name.toLowerCase().endsWith('.csv') ||
      !this.archivoContabilidad.name.toLowerCase().endsWith('.csv')
    ) {
      this.error = 'Los dos archivos deben tener extensión .csv.';
      return;
    }

    this.cargando = true;
    this.error = '';
    this.respuesta = null;

    // Crear el formulario que recibirá FastAPI
    const datos = new FormData();

    datos.append(
      'archivo_facturas',
      this.archivoFacturas
    );

    datos.append(
      'archivo_contabilidad',
      this.archivoContabilidad
    );

    // Enviar los archivos a Python
    this.http.post<RespuestaConciliacion>(
      'http://127.0.0.1:8000/conciliar',
      datos
    ).subscribe({
      next: (respuesta) => {
        this.respuesta = respuesta;
        this.cargando = false;
        this.cdr.detectChanges();
        this.filtro = 'Todas';
        this.busqueda = '';
      },

      error: (error: HttpErrorResponse) => {
        this.cargando = false;
        this.cdr.detectChanges();

        if (error.status === 0) {
          this.error =
            'No se pudo conectar con Python. ' +
            'Comprueba que FastAPI esté funcionando ' +
            'en http://127.0.0.1:8000.';
        } else {
          const detalle = error.error?.detail;

          this.error =
            typeof detalle === 'string'
              ? detalle
              : 'Ocurrió un error al procesar los archivos.';
        }
      }
    });
  }

  // Filtrar resultados por estado y por ID de factura
  get resultadosFiltrados(): ResultadoFactura[] {

    if (!this.respuesta) {
      return [];
    }

    return this.respuesta.resultados.filter((factura) => {

      const cumpleEstado =
        this.filtro === 'Todas' ||
        factura.estado === this.filtro;

      const cumpleBusqueda =
        factura.id_factura.toLowerCase().includes(
          this.busqueda.trim().toLowerCase()
        );

      return cumpleEstado && cumpleBusqueda;
    });
  }
}
