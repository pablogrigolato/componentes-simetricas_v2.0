---
title: Fasores Dinámicos y Componentes Simétricas
emoji: ⚡
colorFrom: yellow
colorTo: purple
sdk: streamlit
sdk_version: "1.38.0"
app_file: app.py
pinned: false
---

# Fasores Dinámicos y Componentes Simétricas

Visualizador interactivo de un sistema trifásico desbalanceado y su
descomposición en componentes de secuencia (Fortescue): positiva,
negativa y homopolar.

## Funcionalidades

- Ajuste de magnitud y ángulo de cada fase (A, B, C).
- Animación temporal automática.
- Diagramas fasoriales y formas de onda, con descarga en PNG.
- Cálculo del grado de desbalance (norma NEMA/IEC, |V₂|/|V₁|).
- Tabla de valores instantáneos por componente de secuencia.

## Ejecutar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```
