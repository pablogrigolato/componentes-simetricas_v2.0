import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time

st.set_page_config(
    page_title="Fasores Dinámicos y Componentes Simétricas",
    page_icon="⚡",
    layout="wide",
)

# ------------------------------------------------------------------
# Constantes
# ------------------------------------------------------------------
F_HZ = 50
OMEGA = 2 * np.pi * F_HZ
ALPHA = np.exp(1j * 2 * np.pi / 3)
COLOR_SEQ = {"pos": "#e69f00", "neg": "#9467bd", "hom": "#7f7f7f"}  # paleta amigable daltónicos
COLOR_FASE = {"A": "#d62728", "B": "#2ca02c", "C": "#1f77b4"}

# ------------------------------------------------------------------
# Funciones de cálculo (cacheadas: son puras y baratas, pero cachear
# evita recomputar si Streamlit re-renderiza por otros widgets)
# ------------------------------------------------------------------
def crear_fasor(mag: float, ang_deg: float, t: float) -> complex:
    ang_rad = np.deg2rad(ang_deg)
    return mag * np.exp(1j * (OMEGA * t + ang_rad))


def componentes_simetricas(VA, VB, VC):
    V0 = (VA + VB + VC) / 3
    V1 = (VA + ALPHA * VB + ALPHA**2 * VC) / 3
    V2 = (VA + ALPHA**2 * VB + ALPHA * VC) / 3
    return V0, V1, V2


@st.cache_data(show_spinner=False)
def onda(Vfasor: complex, t_array: np.ndarray) -> np.ndarray:
    return np.real(Vfasor * np.exp(1j * OMEGA * t_array))


DASH = {"-": "solid", "--": "dash", ":": "dot"}


def fasor_diagram(lim: float, title: str) -> go.Figure:
    """Crea una figura Plotly vacía con ejes/cuadrícula listos para agregar fasores."""
    fig = go.Figure()
    fig.add_hline(y=0, line_width=1, line_color="rgba(128,128,128,0.5)")
    fig.add_vline(x=0, line_width=1, line_color="rgba(128,128,128,0.5)")
    fig.update_layout(
        title=title,
        xaxis=dict(range=[-lim, lim], zeroline=False, showgrid=True, gridcolor="rgba(128,128,128,0.2)"),
        yaxis=dict(range=[-lim, lim], zeroline=False, showgrid=True, gridcolor="rgba(128,128,128,0.2)",
                   scaleanchor="x", scaleratio=1),
        showlegend=True,
        height=480,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def agregar_fasor(fig: go.Figure, V: complex, color: str, dash: str, label: str):
    """Agrega un fasor como línea con punta de flecha (annotation) y hover con magnitud/ángulo."""
    x1, y1 = float(V.real), float(V.imag)
    mag, ang = np.abs(V), np.angle(V, deg=True)
    fig.add_trace(go.Scatter(
        x=[0, x1], y=[0, y1],
        mode="lines",
        line=dict(color=color, dash=dash, width=2.5),
        name=label,
        hovertemplate=f"{label}<br>Mag: {mag:.2f}<br>Ang: {ang:.1f}°<extra></extra>",
    ))
    if mag > 1e-9:
        fig.add_annotation(
            x=x1, y=y1, ax=0.985 * x1, ay=0.985 * y1,
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=3, arrowsize=1.4, arrowwidth=2, arrowcolor=color,
        )


def dibujar_tres_fases(fig: go.Figure, base_vector, tipo, color, label_base):
    estilos = ["-", "--", ":"]
    if tipo == "pos":
        fases = [base_vector, base_vector * ALPHA**2, base_vector * ALPHA]
    elif tipo == "neg":
        fases = [base_vector, base_vector * ALPHA, base_vector * ALPHA**2]
    elif tipo == "hom":
        fases = [base_vector, base_vector, base_vector]
    else:
        fases = []

    for idx, V in enumerate(fases):
        etiqueta = f"{label_base} Fase {['A', 'B', 'C'][idx]}"
        agregar_fasor(fig, V, color=color, dash=DASH[estilos[idx]], label=etiqueta)


# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
st.sidebar.title("⚙️ Parámetros del sistema")


def _sync_from_slider(base_key):
    st.session_state[f"{base_key}_num"] = st.session_state[f"{base_key}_sld"]


def _sync_from_number(base_key):
    st.session_state[f"{base_key}_sld"] = st.session_state[f"{base_key}_num"]


def slider_con_numero(label, base_key, min_v, max_v, default, step=1, fmt=None):
    """Slider + input numérico sincronizados entre sí, para ajuste grueso y fino."""
    if f"{base_key}_sld" not in st.session_state:
        st.session_state[f"{base_key}_sld"] = default
    if f"{base_key}_num" not in st.session_state:
        st.session_state[f"{base_key}_num"] = default

    col_s, col_n = st.columns([3, 2])
    col_s.slider(label, min_v, max_v, key=f"{base_key}_sld", step=step,
                  on_change=_sync_from_slider, args=(base_key,), label_visibility="visible")
    col_n.number_input(" ", min_v, max_v, key=f"{base_key}_num", step=step, format=fmt,
                         on_change=_sync_from_number, args=(base_key,), label_visibility="collapsed")
    return st.session_state[f"{base_key}_sld"]


with st.sidebar.expander("Fase A", expanded=True):
    mag_A = slider_con_numero("Magnitud A", "mag_A", 0, 150, 100)
    ang_A = slider_con_numero("Ángulo A (°)", "ang_A", -180, 180, 0)

with st.sidebar.expander("Fase B", expanded=True):
    mag_B = slider_con_numero("Magnitud B", "mag_B", 0, 150, 90)
    ang_B = slider_con_numero("Ángulo B (°)", "ang_B", -180, 180, -120)

with st.sidebar.expander("Fase C", expanded=True):
    mag_C = slider_con_numero("Magnitud C", "mag_C", 0, 150, 110)
    ang_C = slider_con_numero("Ángulo C (°)", "ang_C", -180, 180, 120)

def _aplicar_valores(defaults: dict):
    for k, v in defaults.items():
        st.session_state[f"{k}_sld"] = v
        st.session_state[f"{k}_num"] = v


st.sidebar.markdown("---")

col_reset, col_bal = st.sidebar.columns(2)
col_reset.button(
    "↺ Reset", use_container_width=True,
    on_click=_aplicar_valores,
    args=({"mag_A": 100, "ang_A": 0, "mag_B": 90, "ang_B": -120, "mag_C": 110, "ang_C": 120},),
)
col_bal.button(
    "⚖ Balancear", use_container_width=True,
    on_click=_aplicar_valores,
    args=({"mag_A": 100, "ang_A": 0, "mag_B": 100, "ang_B": -120, "mag_C": 100, "ang_C": 120},),
)

st.sidebar.markdown("---")

if "t_ms" not in st.session_state:
    st.session_state.t_ms = 0.0

animar = st.sidebar.toggle("▶ Animar en el tiempo", value=False)
t_ms = st.sidebar.slider("🕒 Tiempo (ms)", 0.0, 40.0, st.session_state.t_ms, step=0.1, key="t_slider",
                          disabled=animar)
if not animar:
    st.session_state.t_ms = t_ms

escala_manual = st.sidebar.slider("📏 Escala fija (0 = auto)", 0, 300, 0)

st.sidebar.markdown("---")
st.sidebar.caption("Desarrollado para el análisis didáctico de componentes simétricas (Fortescue).")

# ------------------------------------------------------------------
# Cálculo
# ------------------------------------------------------------------
t = st.session_state.t_ms / 1000.0

VA = crear_fasor(mag_A, ang_A, t)
VB = crear_fasor(mag_B, ang_B, t)
VC = crear_fasor(mag_C, ang_C, t)
V0, V1, V2 = componentes_simetricas(VA, VB, VC)

if escala_manual > 0:
    lim = float(escala_manual)
else:
    max_mag = max(np.abs(VA), np.abs(VB), np.abs(VC), np.abs(V0), np.abs(V1), np.abs(V2), 1.0)
    lim = float(np.ceil(max_mag / 10.0) * 12.0)

# Grado de desbalance (NEMA / IEC): |V2|/|V1| * 100
desbalance_pct = (np.abs(V2) / np.abs(V1) * 100) if np.abs(V1) > 1e-9 else 0.0

# ------------------------------------------------------------------
# Encabezado
# ------------------------------------------------------------------
st.title("⚡ Fasores Dinámicos y Componentes Simétricas")
st.caption(
    "Visualización interactiva de un sistema trifásico desbalanceado y su descomposición "
    "en componentes de secuencia positiva, negativa y homopolar (método de Fortescue)."
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("|V₀| (homopolar)", f"{np.abs(V0):.2f}")
m2.metric("|V₁| (positiva)", f"{np.abs(V1):.2f}")
m3.metric("|V₂| (negativa)", f"{np.abs(V2):.2f}")
m4.metric("Grado de desbalance", f"{desbalance_pct:.1f} %",
          help="Relación |V₂|/|V₁| × 100, según la definición NEMA/IEC.")

st.markdown("")

# ------------------------------------------------------------------
# Layout principal
# ------------------------------------------------------------------
col1, col2 = st.columns(2)

T = 1 / F_HZ
t_array = np.linspace(0, 2 * T, 800)

with col1:
    fig1 = fasor_diagram(lim, "Sistema desbalanceado (fasores)")
    for nombre, V in zip(["A", "B", "C"], [VA, VB, VC]):
        agregar_fasor(fig1, V, color=COLOR_FASE[nombre], dash="solid", label=f"V{nombre}")
    st.plotly_chart(fig1, use_container_width=True, config={"displaylogo": False})

    fig1t = go.Figure()
    for nombre, V in zip(["A", "B", "C"], [VA, VB, VC]):
        fig1t.add_trace(go.Scatter(x=t_array * 1000, y=onda(V, t_array), mode="lines",
                                    line=dict(color=COLOR_FASE[nombre]), name=f"V{nombre}"))
    fig1t.add_vline(x=t * 1000, line_width=1, line_dash="dash", line_color="rgba(0,0,0,0.5)")
    fig1t.update_layout(title="Evolución temporal — sistema desbalanceado",
                         xaxis_title="Tiempo (ms)", yaxis_title="Amplitud",
                         height=300, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig1t, use_container_width=True, config={"displaylogo": False})

with col2:
    fig2 = fasor_diagram(lim, "Componentes simétricas (tres fases)")
    dibujar_tres_fases(fig2, V1, "pos", COLOR_SEQ["pos"], "V₁ Positiva")
    dibujar_tres_fases(fig2, V2, "neg", COLOR_SEQ["neg"], "V₂ Negativa")
    dibujar_tres_fases(fig2, V0, "hom", COLOR_SEQ["hom"], "V₀ Homopolar")
    st.plotly_chart(fig2, use_container_width=True, config={"displaylogo": False})

    fig2t = go.Figure()
    estilos = ["-", "--", ":"]
    sec = [
        ("V₁ Positiva", V1, "pos"),
        ("V₂ Negativa", V2, "neg"),
        ("V₀ Homopolar", V0, "hom"),
    ]
    for nombre, base, tipo in sec:
        color = COLOR_SEQ[tipo]
        if tipo == "pos":
            fases = [base, base * ALPHA**2, base * ALPHA]
        elif tipo == "neg":
            fases = [base, base * ALPHA, base * ALPHA**2]
        else:
            fases = [base, base, base]
        for i, V in enumerate(fases):
            fig2t.add_trace(go.Scatter(x=t_array * 1000, y=onda(V, t_array), mode="lines",
                                        line=dict(color=color, dash=DASH[estilos[i]]),
                                        name=f"{nombre} Fase {['A', 'B', 'C'][i]}"))
    fig2t.add_vline(x=t * 1000, line_width=1, line_dash="dash", line_color="rgba(0,0,0,0.5)")
    fig2t.update_layout(title="Evolución temporal — secuencias",
                         xaxis_title="Tiempo (ms)",
                         height=300, margin=dict(l=20, r=20, t=40, b=20),
                         legend=dict(font=dict(size=9)))
    st.plotly_chart(fig2t, use_container_width=True, config={"displaylogo": False})

# ------------------------------------------------------------------
# Valores instantáneos + tabla exportable
# ------------------------------------------------------------------
st.markdown("### 🧮 Valores instantáneos (fase A de cada secuencia)")
tabla = {
    "Componente": ["V₀ (homopolar)", "V₁ (positiva)", "V₂ (negativa)"],
    "Magnitud": [np.round(np.abs(V0), 3), np.round(np.abs(V1), 3), np.round(np.abs(V2), 3)],
    "Ángulo (°)": [np.round(np.angle(V0, deg=True), 2),
                   np.round(np.angle(V1, deg=True), 2),
                   np.round(np.angle(V2, deg=True), 2)],
    "Valor complejo": [f"{V0:.3f}", f"{V1:.3f}", f"{V2:.3f}"],
}
st.dataframe(tabla, use_container_width=True, hide_index=True)

with st.expander("ℹ️ ¿Cómo se calculan las componentes simétricas?"):
    st.latex(r"""
    \begin{bmatrix} V_0 \\ V_1 \\ V_2 \end{bmatrix}
    = \frac{1}{3}
    \begin{bmatrix} 1 & 1 & 1 \\ 1 & \alpha & \alpha^2 \\ 1 & \alpha^2 & \alpha \end{bmatrix}
    \begin{bmatrix} V_A \\ V_B \\ V_C \end{bmatrix}, \quad
    \alpha = e^{j2\pi/3}
    """)
    st.markdown(
        "El **grado de desbalance** se define como la relación entre la magnitud de la "
        "componente de secuencia negativa y la positiva, expresada en porcentaje."
    )

# ------------------------------------------------------------------
# Animación (avanza el tiempo automáticamente)
# ------------------------------------------------------------------
if animar:
    st.session_state.t_ms = (st.session_state.t_ms + 0.6) % 40.0
    time.sleep(0.05)
    st.rerun()
