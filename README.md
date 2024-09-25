# Aplicación de Cálculo de Comisiones

Esta aplicación ha sido desarrollada para **BATSEJ OPEN FINANCE S.A**, con el objetivo de automatizar el cálculo y cobro de comisiones basadas en las peticiones realizadas por las empresas contratantes. Proporciona una interfaz sencilla para gestionar condiciones, calcular comisiones y exportar los resultados a Excel. La totalidad de la aplicación está en inglés para generalizar su uso, pero las descripciones de las funciones están en español para entender su funcionalidad.

## Tabla de Contenidos
- [Requisitos Previos](#requisitos-previos)
- [Instalación](#instalación)
- [Uso de la Aplicación](#uso-de-la-aplicación)
  - [Seleccionar la Base de Datos](#seleccionar-la-base-de-datos)
  - [Gestionar Condiciones](#gestionar-condiciones)
  - [Calcular Comisiones](#calcular-comisiones)
  - [Exportar Reporte a Excel](#exportar-reporte-a-excel)
  - [Enviar Correo](#enviar-correo)
- [Contribuciones](#contribuciones)
- [Licencia](#licencia)
- [Documentación Adicional](#documentación-adicional)

## Requisitos Previos

Antes de ejecutar la aplicación, asegúrate de tener instalado:

- Python 3.x
- Las dependencias del proyecto (ver sección [Instalación](#instalación)).

## Instalación

1. Clona este repositorio en tu máquina local:
    ```bash
    git clone https://github.com/usuario/nombre-repositorio.git
    ```

2. Instala las dependencias necesarias con el siguiente comando:
    ```bash
    pip install -r requirements.txt
    ```

## Uso de la Aplicación

### Iniciar la Aplicación

Para iniciar la aplicación, ejecuta el archivo `run.py` desde la terminal:

```bash
python run.py
