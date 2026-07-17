import streamlit as st
import streamlit.components.v1 as components
import json

st.set_page_config(
    page_title="Fasores Dinámicos y Componentes Simétricas",
    page_icon="⚡",
    layout="wide",
)

# ------------------------------------------------------------------
# Constantes
# (El cálculo de fasores y componentes simétricas corre del lado del
#  navegador en JavaScript, dentro del componente HTML — ver más
#  abajo. Estas constantes sólo se usan para armar los widgets.)
# ------------------------------------------------------------------
F_HZ = 50
COLOR_SEQ = {"pos": "#e69f00", "neg": "#9467bd", "hom": "#7f7f7f"}  # paleta amigable daltónicos
COLOR_FASE = {"A": "#d62728", "B": "#2ca02c", "C": "#1f77b4"}


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
    col_n.number_input(f"{label} (valor exacto)", min_v, max_v, key=f"{base_key}_num", step=step, format=fmt,
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

escala_manual = st.sidebar.slider("📏 Escala fija (0 = auto)", 0, 300, 0)

st.sidebar.markdown("---")
st.sidebar.caption("Desarrollado para el análisis didáctico de componentes simétricas (Fortescue).")
st.sidebar.caption("▶ El control de animación está debajo de los gráficos.")

# ------------------------------------------------------------------
# Encabezado (estático, fuera del fragment)
# ------------------------------------------------------------------
st.title("⚡ Fasores Dinámicos y Componentes Simétricas")
st.caption(
    "Visualización interactiva de un sistema trifásico desbalanceado y su descomposición "
    "en componentes de secuencia positiva, negativa y homopolar (método de Fortescue)."
)


# ------------------------------------------------------------------
# Componente HTML/JS: toda la animación corre en el navegador con
# Plotly.js (requestAnimationFrame), sin comunicación con el servidor
# de Streamlit en cada frame. Esto elimina por completo el parpadeo
# que genera reconstruir el gráfico del lado del servidor.
# Los sliders de la izquierda (mag/ang/escala) sí generan un re-render
# normal de Streamlit, pero eso ocurre sólo cuando el usuario los
# mueve, no en cada frame de la animación.
# ------------------------------------------------------------------
params = dict(
    magA=mag_A, angA=ang_A, magB=mag_B, angB=ang_B, magC=mag_C, angC=ang_C,
    escalaManual=escala_manual, fHz=F_HZ,
    colorFase=COLOR_FASE, colorSeq=COLOR_SEQ,
)

HTML_TEMPLATE = r"""
<div id="app" style="font-family: 'Source Sans Pro', sans-serif; color: #fafafa;">
  <div id="metrics" style="display:flex; gap:14px; margin-bottom:6px; flex-wrap:wrap;"></div>
  <div style="display:flex; gap:16px; flex-wrap:wrap;">
    <div style="flex:1; min-width:340px;">
      <div id="fig1" style="width:100%; height:400px;"></div>
      <div id="fig1t" style="width:100%; height:240px;"></div>
    </div>
    <div style="flex:1; min-width:340px;">
      <div id="fig2" style="width:100%; height:400px;"></div>
      <div id="fig2t" style="width:100%; height:240px;"></div>
    </div>
  </div>
  <div style="margin:8px 0 10px; display:flex; align-items:center; gap:12px; flex-wrap:wrap;">
    <button id="playBtn" style="background:#2b2f38; color:#fafafa; border:1px solid #555; border-radius:6px; padding:6px 16px; cursor:pointer; font-size:14px;">▶ Animar</button>
    <input id="timeSlider" type="range" min="0" max="40" step="0.1" value="0" style="flex:1; min-width:160px;">
    <span id="timeLabel" style="min-width:70px; font-size:13px; color:#bbb;">0.0 ms</span>
    <label style="font-size:13px; color:#bbb; display:flex; align-items:center; gap:6px;">
      Velocidad
      <input id="speedSlider" type="range" min="0.02" max="1" step="0.02" value="0.12" style="width:100px;">
      <span id="speedLabel">0.12×</span>
    </label>
  </div>
  <div id="tabla" style="margin-top:2px;"></div>
</div>

<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<script>
const P = __PARAMS__;
const F_HZ = P.fHz;
const OMEGA = 2 * Math.PI * F_HZ;
const ALPHA = {re: Math.cos(2*Math.PI/3), im: Math.sin(2*Math.PI/3)};
const ALPHA2 = {re: Math.cos(4*Math.PI/3), im: Math.sin(4*Math.PI/3)};

function cMul(a, b) { return {re: a.re*b.re - a.im*b.im, im: a.re*b.im + a.im*b.re}; }
function cAdd(a, b) { return {re: a.re+b.re, im: a.im+b.im}; }
function cScale(a, s) { return {re: a.re*s, im: a.im*s}; }
function cAbs(a) { return Math.hypot(a.re, a.im); }
function cAngDeg(a) { return Math.atan2(a.im, a.re) * 180 / Math.PI; }

function crearFasor(mag, angDeg, tSec) {
  const angRad = angDeg * Math.PI / 180;
  const theta = OMEGA * tSec + angRad;
  return {re: mag * Math.cos(theta), im: mag * Math.sin(theta)};
}

function componentesSimetricas(VA, VB, VC) {
  const V0 = cScale(cAdd(cAdd(VA, VB), VC), 1/3);
  const V1 = cScale(cAdd(cAdd(VA, cMul(ALPHA, VB)), cMul(ALPHA2, VC)), 1/3);
  const V2 = cScale(cAdd(cAdd(VA, cMul(ALPHA2, VB)), cMul(ALPHA, VC)), 1/3);
  return [V0, V1, V2];
}

// Onda temporal física v(t) = mag·cos(ωt + ang), calculada desde el fasor
// ESTÁTICO (no el rotado por la animación). Así la forma de onda es fija y
// el marcador vertical en t_anim lee exactamente Re{fasor giratorio}.
function ondaEstatica(V0complex, tArrayMs) {
  const mag = cAbs(V0complex);
  const ang = Math.atan2(V0complex.im, V0complex.re);
  return tArrayMs.map(tms => mag * Math.cos(OMEGA * (tms/1000) + ang));
}

const T_ARRAY = [];
const T_PERIOD_MS = (1/F_HZ) * 1000;
for (let i = 0; i < 800; i++) { T_ARRAY.push(i * (2*T_PERIOD_MS) / 799); }

const AX_STYLE = {zeroline:false, showgrid:true, gridcolor:'rgba(128,128,128,0.25)', color:'#bbb'};
const BASE_LAYOUT = {
  paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
  font: {color:'#eee'}, showlegend:true,
  legend: {font:{size:10}},
  margin: {l:40, r:20, t:36, b:36},
};

function fasorTrace(V, color, dash, label) {
  return {
    x: [0, V.re], y: [0, V.im], mode:'lines', line:{color:color, dash:dash, width:2.5},
    name:label, hovertemplate:`${label}<br>Mag: ${cAbs(V).toFixed(2)}<br>Ang: ${cAngDeg(V).toFixed(1)}°<extra></extra>`
  };
}
function fasorAnnotation(V, color) {
  if (cAbs(V) < 1e-9) return null;
  return {
    x:V.re, y:V.im, ax:0.985*V.re, ay:0.985*V.im, xref:'x', yref:'y', axref:'x', ayref:'y',
    showarrow:true, arrowhead:3, arrowsize:1.3, arrowwidth:2, arrowcolor:color
  };
}

function tresFases(base, tipo, color, labelBase) {
  const estilos = ['solid','dash','dot'];
  let fases;
  if (tipo === 'pos') fases = [base, cMul(base, ALPHA2), cMul(base, ALPHA)];
  else if (tipo === 'neg') fases = [base, cMul(base, ALPHA), cMul(base, ALPHA2)];
  else fases = [base, base, base];
  const letras = ['A','B','C'];
  const traces = [], annots = [];
  fases.forEach((V, i) => {
    const label = `${labelBase} Fase ${letras[i]}`;
    traces.push(fasorTrace(V, color, estilos[i], label));
    const a = fasorAnnotation(V, color); if (a) annots.push(a);
  });
  return {traces, annots};
}

let plotsInitialized = false;

// ------------------------------------------------------------------
// Ondas temporales: son FIJAS durante la animación (una senoidal de
// 50 Hz no cambia de forma; sólo se mueve el marcador de tiempo).
// Se calculan una única vez desde los fasores estáticos (t = 0) y se
// dibujan con newPlot una sola vez; en cada frame sólo se reubica el
// marcador vertical con Plotly.relayout, que es muy barato.
// ------------------------------------------------------------------
const CF = P.colorFase, CS = P.colorSeq;
const VA_EST = crearFasor(P.magA, P.angA, 0);
const VB_EST = crearFasor(P.magB, P.angB, 0);
const VC_EST = crearFasor(P.magC, P.angC, 0);
const [S0, S1, S2] = componentesSimetricas(VA_EST, VB_EST, VC_EST);
const Y_WAVE = Math.max(cAbs(VA_EST), cAbs(VB_EST), cAbs(VC_EST), 1) * 1.2;

function markerShape(tMs) {
  return {type:'line', x0:tMs, x1:tMs, y0:-Y_WAVE, y1:Y_WAVE,
          line:{color:'rgba(255,255,255,0.5)', width:1, dash:'dash'}};
}

const FIG1T_TRACES = [
  {x:T_ARRAY, y:ondaEstatica(VA_EST, T_ARRAY), mode:'lines', line:{color:CF.A}, name:'VA'},
  {x:T_ARRAY, y:ondaEstatica(VB_EST, T_ARRAY), mode:'lines', line:{color:CF.B}, name:'VB'},
  {x:T_ARRAY, y:ondaEstatica(VC_EST, T_ARRAY), mode:'lines', line:{color:CF.C}, name:'VC'},
];

const FIG2T_TRACES = [];
{
  const estilos = ['solid','dash','dot'];
  const letras = ['A','B','C'];
  [['V₁ Positiva', S1, 'pos'], ['V₂ Negativa', S2, 'neg'], ['V₀ Homopolar', S0, 'hom']].forEach(([nombre, base, tipo]) => {
    const color = CS[tipo];
    let fases;
    if (tipo==='pos') fases=[base, cMul(base,ALPHA2), cMul(base,ALPHA)];
    else if (tipo==='neg') fases=[base, cMul(base,ALPHA), cMul(base,ALPHA2)];
    else fases=[base, base, base];
    fases.forEach((V,i) => {
      FIG2T_TRACES.push({x:T_ARRAY, y:ondaEstatica(V, T_ARRAY), mode:'lines',
                         line:{color:color, dash:estilos[i]}, name:`${nombre} Fase ${letras[i]}`});
    });
  });
}

const FIG1T_LAYOUT = Object.assign({}, BASE_LAYOUT, {
  title:{text:'Evolución temporal — desbalanceado', font:{size:13}},
  xaxis: Object.assign({}, AX_STYLE, {title:'Tiempo (ms)'}),
  yaxis: Object.assign({}, AX_STYLE, {title:'Amplitud'}),
  shapes:[markerShape(0)],
});
const FIG2T_LAYOUT = Object.assign({}, BASE_LAYOUT, {
  title:{text:'Evolución temporal — secuencias', font:{size:13}},
  xaxis: Object.assign({}, AX_STYLE, {title:'Tiempo (ms)'}),
  yaxis: AX_STYLE,
  legend: {font:{size:8}},
  shapes:[markerShape(0)],
});

function computeState(tMs) {
  const t = tMs / 1000;
  const VA = crearFasor(P.magA, P.angA, t);
  const VB = crearFasor(P.magB, P.angB, t);
  const VC = crearFasor(P.magC, P.angC, t);
  const [V0, V1, V2] = componentesSimetricas(VA, VB, VC);

  let lim;
  if (P.escalaManual > 0) { lim = P.escalaManual; }
  else {
    const maxMag = Math.max(cAbs(VA), cAbs(VB), cAbs(VC), cAbs(V0), cAbs(V1), cAbs(V2), 1.0);
    lim = Math.ceil(maxMag * 1.15 / 10.0) * 10.0;   // 15% de margen, redondeado a decenas
  }
  const desbalance = cAbs(V1) > 1e-9 ? (cAbs(V2)/cAbs(V1))*100 : 0;
  return {t, VA, VB, VC, V0, V1, V2, lim, desbalance};
}

function render(tMs) {
  const s = computeState(tMs);
  const cf = P.colorFase, cs = P.colorSeq;

  // --- métricas ---
  document.getElementById('metrics').innerHTML = `
    ${metricCard('|V₀| (homopolar)', s.V0)}
    ${metricCard('|V₁| (positiva)', s.V1)}
    ${metricCard('|V₂| (negativa)', s.V2)}
    ${metricCardPct('Grado de desbalance', s.desbalance)}
  `;

  // --- fig1: fasores desbalanceados ---
  const fig1traces = [
    fasorTrace(s.VA, cf.A, 'solid', 'VA'),
    fasorTrace(s.VB, cf.B, 'solid', 'VB'),
    fasorTrace(s.VC, cf.C, 'solid', 'VC'),
  ];
  const fig1annots = [s.VA, s.VB, s.VC].map((V,i)=>fasorAnnotation(V,[cf.A,cf.B,cf.C][i])).filter(a=>a);
  const axRange = [-s.lim, s.lim];
  const fig1layout = Object.assign({}, BASE_LAYOUT, {
    title:{text:'Sistema desbalanceado (fasores)', font:{size:14}},
    xaxis: Object.assign({}, AX_STYLE, {range:axRange}),
    yaxis: Object.assign({}, AX_STYLE, {range:axRange, scaleanchor:'x', scaleratio:1}),
    shapes:[
      {type:'line', x0:axRange[0], x1:axRange[1], y0:0, y1:0, line:{color:'rgba(128,128,128,0.5)', width:1}},
      {type:'line', x0:0, x1:0, y0:axRange[0], y1:axRange[1], line:{color:'rgba(128,128,128,0.5)', width:1}},
    ],
    annotations: fig1annots,
  });

  // --- fig2: componentes simétricas ---
  const seqPos = tresFases(s.V1, 'pos', cs.pos, 'V₁ Positiva');
  const seqNeg = tresFases(s.V2, 'neg', cs.neg, 'V₂ Negativa');
  const seqHom = tresFases(s.V0, 'hom', cs.hom, 'V₀ Homopolar');
  const fig2traces = [...seqPos.traces, ...seqNeg.traces, ...seqHom.traces];
  const fig2annots = [...seqPos.annots, ...seqNeg.annots, ...seqHom.annots];
  const fig2layout = Object.assign({}, BASE_LAYOUT, {
    title:{text:'Componentes simétricas (tres fases)', font:{size:14}},
    xaxis: Object.assign({}, AX_STYLE, {range:axRange}),
    yaxis: Object.assign({}, AX_STYLE, {range:axRange, scaleanchor:'x', scaleratio:1}),
    shapes: fig1layout.shapes,
    annotations: fig2annots,
    legend: {font:{size:8}},
  });

  const config = {displaylogo:false, responsive:true};

  if (!plotsInitialized) {
    Plotly.newPlot('fig1', fig1traces, fig1layout, config);
    Plotly.newPlot('fig2', fig2traces, fig2layout, config);
    // Las ondas temporales se dibujan UNA sola vez (son estáticas).
    Plotly.newPlot('fig1t', FIG1T_TRACES, FIG1T_LAYOUT, config);
    Plotly.newPlot('fig2t', FIG2T_TRACES, FIG2T_LAYOUT, config);
    plotsInitialized = true;
  } else {
    Plotly.react('fig1', fig1traces, fig1layout, config);
    Plotly.react('fig2', fig2traces, fig2layout, config);
  }

  // En cada frame sólo se mueve el marcador vertical de las ondas.
  Plotly.relayout('fig1t', {shapes:[markerShape(tMs)]});
  Plotly.relayout('fig2t', {shapes:[markerShape(tMs)]});

  // --- tabla ---
  document.getElementById('tabla').innerHTML = tablaHtml(s);

  document.getElementById('timeLabel').textContent = tMs.toFixed(1) + ' ms';
}

function metricCard(label, V) {
  return `<div style="background:#1c1f26; border:1px solid #333; border-radius:8px; padding:8px 14px; min-width:130px;">
    <div style="font-size:12px; color:#999;">${label}</div>
    <div style="font-size:22px; font-weight:600;">${cAbs(V).toFixed(2)}</div>
  </div>`;
}
function metricCardPct(label, val) {
  return `<div style="background:#1c1f26; border:1px solid #333; border-radius:8px; padding:8px 14px; min-width:130px;">
    <div style="font-size:12px; color:#999;">${label}</div>
    <div style="font-size:22px; font-weight:600;">${val.toFixed(1)} %</div>
  </div>`;
}
function tablaHtml(s) {
  const rows = [
    ['V₀ (homopolar)', s.V0], ['V₁ (positiva)', s.V1], ['V₂ (negativa)', s.V2]
  ];
  let body = rows.map(([nom, V]) => `
    <tr>
      <td style="padding:4px 10px;">${nom}</td>
      <td style="padding:4px 10px;">${cAbs(V).toFixed(3)}</td>
      <td style="padding:4px 10px;">${cAngDeg(V).toFixed(2)}</td>
      <td style="padding:4px 10px;">${V.re.toFixed(3)} ${V.im>=0?'+':'-'} ${Math.abs(V.im).toFixed(3)}j</td>
    </tr>`).join('');
  return `<table style="width:100%; border-collapse:collapse; font-size:13px;">
    <thead><tr style="color:#999; text-align:left; border-bottom:1px solid #333;">
      <th style="padding:4px 10px;">Componente</th><th style="padding:4px 10px;">Magnitud</th>
      <th style="padding:4px 10px;">Ángulo (°)</th><th style="padding:4px 10px;">Valor complejo</th>
    </tr></thead><tbody>${body}</tbody></table>`;
}

// --- control de animación (100% client-side, sin llamadas a Streamlit) ---
let animando = false, lastFrameTime = null, tMs = 0;
// "velocidad" = ms simulados por ms real. El valor efectivo lo fija el
// slider de velocidad (uiVal × 0.05); con el valor por defecto 0.12×
// resulta 0.006 → un ciclo completo de 40 ms tarda ≈ 6.7 s reales.
let velocidad = 0.12 * 0.05;
const playBtn = document.getElementById('playBtn');
const timeSlider = document.getElementById('timeSlider');
const speedSlider = document.getElementById('speedSlider');
const speedLabel = document.getElementById('speedLabel');

function frame(now) {
  if (!animando) return;
  if (lastFrameTime === null) lastFrameTime = now;
  const dtMs = now - lastFrameTime;
  lastFrameTime = now;
  tMs = (tMs + dtMs * velocidad) % 40;
  timeSlider.value = tMs;
  render(tMs);
  requestAnimationFrame(frame);
}

playBtn.addEventListener('click', () => {
  animando = !animando;
  playBtn.textContent = animando ? '⏸ Pausar' : '▶ Animar';
  timeSlider.disabled = animando;
  if (animando) { lastFrameTime = null; requestAnimationFrame(frame); }
});

timeSlider.addEventListener('input', () => {
  if (!animando) { tMs = parseFloat(timeSlider.value); render(tMs); }
});

speedSlider.addEventListener('input', () => {
  // el slider va de 0.02 a 1 (escala cómoda para el usuario); se remapea
  // a un rango de velocidad real mucho más lento para que se aprecie el giro.
  const uiVal = parseFloat(speedSlider.value);
  velocidad = uiVal * 0.05;
  speedLabel.textContent = uiVal.toFixed(2) + '×';
});
speedSlider.dispatchEvent(new Event('input'));

render(0);
</script>
"""

html_final = HTML_TEMPLATE.replace("__PARAMS__", json.dumps(params))
components.html(html_final, height=900, scrolling=True)

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
