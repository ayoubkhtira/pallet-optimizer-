import streamlit as st
import streamlit.components.v1 as components 
import math
import pandas as pd
from io import BytesIO

# ==========================================
# 1. CONFIGURATION ET CONSTANTES
# ==========================================
st.set_page_config(
    page_title="Container Optimizer - Logistics Pro", 
    page_icon="🚢", 
    layout="wide"
)

# Dimensions techniques réelles
CONTAINER_TYPES = {
    "1 EVP (20' Standard)": {"L": 589.8, "W": 235.2, "H": 239.3, "MaxPayload": 28200, "Vol": 33.2},
    "2 EVP (40' Standard)": {"L": 1203.2, "W": 235.2, "H": 239.3, "MaxPayload": 26700, "Vol": 67.7},
    "2 EVP (40' High Cube)": {"L": 1203.2, "W": 235.2, "H": 269.8, "MaxPayload": 26500, "Vol": 76.4},
    "Personnaliser...": {"L": 0.0, "W": 0.0, "H": 0.0, "MaxPayload": 0.0, "Vol": 0.0}
}

# ==========================================
# 2. FRONT-END (STYLE CSS)
# ==========================================
def local_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
        .stApp { background-color: #f8f9fa; font-family: 'Poppins', sans-serif; }
        .metric-container {
            background-color: white; padding: 25px; border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center;
            border-bottom: 4px solid #e67e22;
        }
        .metric-value { font-size: 2.2rem; font-weight: 700; color: #2c3e50; margin: 0; }
        .metric-label { font-size: 0.8rem; color: #95a5a6; text-transform: uppercase; font-weight: 600; }
        
        /* Style du tableau récapitulatif */
        .recap-table {
            width: 100%; border-collapse: collapse; margin-top: 20px;
            background-color: white; border-radius: 10px; overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        .recap-table th { background-color: #2c3e50; color: white; padding: 12px; text-align: left; }
        .recap-table td { padding: 12px; border-bottom: 1px solid #eee; font-size: 0.9rem; }
        .highlight-orange { color: #e67e22; font-weight: bold; }
        </style>
        """,
        unsafe_allow_html=True
    )

local_css()

# ==========================================
# 3. ALGORITHME DE CALCUL MIXTE
# ==========================================
def professional_load_calc(cont_L, cont_W, cont_H, p_L, p_W, p_H, box_unit_weight, pallet_support_weight, b_per_p, max_load):
    if cont_L <= 0 or cont_W <= 0 or cont_H <= 0:
        return {"total_palettes": 0}
        
    p_long, p_short = max(p_L, p_W), min(p_L, p_W)
    
    # 1. Calcul Sens A (Principal)
    rows_main = int(cont_L / p_long)
    pals_per_row = int(cont_W / p_short)
    palettes_main = rows_main * pals_per_row
    
    # 2. Calcul Sens B (Optimisation fond de conteneur)
    rest_L = cont_L - (rows_main * p_long)
    palettes_rotated = 0
    if rest_L >= p_short:
        palettes_rotated = int(cont_W / p_long)

    stack_levels = int(cont_H / p_H) if p_H > 0 else 1
    total_sol = palettes_main + palettes_rotated
    p_total_weight = (b_per_p * box_unit_weight) + pallet_support_weight
    
    final_pals = total_sol * stack_levels
    if max_load > 0:
        final_pals = min(final_pals, int(max_load / p_total_weight))
        
    return {
        "palettes_sol": total_sol,
        "palettes_main_sol": palettes_main,
        "palettes_rotated_sol": palettes_rotated,
        "niveaux": stack_levels,
        "total_palettes": final_pals,
        "poids_total_brut": final_pals * p_total_weight,
        "utilisation_vol": ((p_L * p_W * p_H * final_pals) / (cont_L * cont_W * cont_H)) * 100 if cont_L > 0 else 0
    }

# ==========================================
# 4. SIDEBAR ET INPUTS
# ==========================================
with st.sidebar:
    st.header("⚙️ CONFIGURATION")
    p_L = st.number_input("Longueur Palette (cm)", value=120.0)
    p_W = st.number_input("Largeur Palette (cm)", value=80.0)
    p_H = st.number_input("Hauteur Palette (cm)", value=160.0)
    b_per_p = st.number_input("Box par Palette", value=40)
    w_box = st.number_input("Poids Box (kg)", value=12.5)
    w_pal = st.number_input("Poids Support (kg)", value=25.0)

# ==========================================
# 5. AFFICHAGE DES RÉSULTATS
# ==========================================
c_choice = st.selectbox("Type de Conteneur", list(CONTAINER_TYPES.keys()))
c_specs = CONTAINER_TYPES[c_choice]

res = professional_load_calc(c_specs['L'], c_specs['W'], c_specs['H'], p_L, p_W, p_H, w_box, w_pal, b_per_p, c_specs['MaxPayload'])

col1, col2, col3 = st.columns(3)
col1.markdown(f'<div class="metric-container"><p class="metric-label">Palettes Total</p><p class="metric-value">{res["total_palettes"]}</p></div>', unsafe_allow_html=True)
col2.markdown(f'<div class="metric-container"><p class="metric-label">Poids Brut (kg)</p><p class="metric-value">{res["poids_total_brut"]:,.0f}</p></div>', unsafe_allow_html=True)
col3.markdown(f'<div class="metric-container"><p class="metric-label">Volume Utile</p><p class="metric-value">{res["utilisation_vol"]:.1f}%</p></div>', unsafe_allow_html=True)

# ==========================================
# 6. TABLEAU RÉCAPITULATIF DES SENS DE POSE
# ==========================================
st.subheader("📋 Répartition par sens de chargement")



table_html = f"""
<table class="recap-table">
    <thead>
        <tr>
            <th>Orientation Palette</th>
            <th>Dimensions au sol</th>
            <th>Nombre au sol</th>
            <th>Total (avec niveaux)</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><b>Sens Principal</b> (Longitudinal)</td>
            <td>{max(p_L, p_W)} x {min(p_L, p_W)} cm</td>
            <td>{res['palettes_main_sol']}</td>
            <td><span class="highlight-orange">{res['palettes_main_sol'] * res['niveaux']}</span></td>
        </tr>
        <tr>
            <td><b>Sens Optimisé</b> (Rotation fond)</td>
            <td>{min(p_L, p_W)} x {max(p_L, p_W)} cm</td>
            <td>{res['palettes_rotated_sol']}</td>
            <td><span class="highlight-orange">{res['palettes_rotated_sol'] * res['niveaux']}</span></td>
        </tr>
        <tr style="background-color: #f8f9fa; font-weight: bold;">
            <td>TOTAL PAR CONTENEUR</td>
            <td>-</td>
            <td>{res['palettes_sol']}</td>
            <td>{res['total_palettes']}</td>
        </tr>
    </tbody>
</table>
"""
st.markdown(table_html, unsafe_allow_html=True)

st.info(f"💡 Ce plan utilise {res['niveaux']} niveau(x) de gerbage sur une hauteur de {c_specs['H']} cm.")
