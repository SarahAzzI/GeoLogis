import requests
import logging
import plotly.express as px
import plotly.offline as pyo
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)

FASTAPI_BASE_URL = "http://127.0.0.1:8001"

# ─────────────────────────────────────────
# Utilitaire
# ─────────────────────────────────────────

 
def fetch_fastapi(path, default=None):
    url = f"{FASTAPI_BASE_URL}{path}"
    logger.warning(f">>> Appel FastAPI : {url}")
    try:
        r = requests.get(url, timeout=5)
        logger.warning(f">>> Réponse [{r.status_code}] : {r.text[:200]}")
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning(f"FastAPI error [{path}]: {e}")
        return default


# ─────────────────────────────────────────
# API DRF
# ─────────────────────────────────────────

@api_view(["GET"])
def trends(request):
    return Response({
        "Lille": "hausse",
        "Paris": "stable",
        "Marseille": "baisse"
    })


# ─────────────────────────────────────────
# Page Market
# ─────────────────────────────────────────

@login_required(login_url='login')
def market_view(request):
    code_postal     = request.GET.get('code_postal', '').strip()
    annee_courante  = 2024

    # Valeurs par défaut
    communes        = []
    taux_moy        = None
    prix_m2         = 4820
    prix_m2_change  = 3.2
    prix_series     = [4350, 4600, 4750, 4820, 4950, 5100]
    prediction_2026 = None
    années          = ['2020', '2021', '2022', '2023', '2024', '2025']

    # ── 1. Données liées au code postal ──────────────────────────────────────
    if code_postal:

        # Communes
        communes_raw = fetch_fastapi(f"/api/v1/communes/by-postal/{code_postal}", [])
        if communes_raw:
            seen = set()
            for c in communes_raw:
                nom = c.get("nom_standard")
                if nom and nom not in seen:
                    communes.append({"nom": nom, "insee": c.get("code_insee")})
                    seen.add(nom)
            communes.sort(key=lambda x: x["nom"])

        # Taxe foncière moyenne
        taxe_data = fetch_fastapi(
            f"/taxe_fonciere/postal/{code_postal}/year/{annee_courante}", []
        )
        if taxe_data:
            taux_valides = [t.get("taux_global_tfb") for t in taxe_data if t.get("taux_global_tfb")]
            if taux_valides:
                taux_moy = round(sum(taux_valides) / len(taux_valides), 2)

        # Taux moyens (fallback si taxe_data vide)
        avg_rates = fetch_fastapi(
            f"/taxe_fonciere/analytics/average-rates/{annee_courante}?postal_code={code_postal}", {}
        )

        # Prédiction 2026
        prediction_2026 = fetch_fastapi(
            f"/predictions/2026/postal/{code_postal}", None
        )

        # Prix m² + historique via la première commune trouvée
        if communes:
            insee = communes[0]["insee"]
            trend = fetch_fastapi(f"/api/v1/real-estate/trend/{insee}", [])
            if trend:
                derniere       = trend[-1]
                avant          = trend[-2] if len(trend) > 1 else {}
                prix_m2        = round(derniere.get("valeur_fonciere_par_m2", prix_m2))
                prev           = avant.get("valeur_fonciere_par_m2", prix_m2)
                prix_m2_change = round(((prix_m2 - prev) / prev) * 100, 1) if prev else 3.2

                trend_map  = {str(t.get("annee")): t.get("valeur_fonciere_par_m2") for t in trend}
                fallback   = [4350, 4600, 4750, 4820, 4950, 5100]
                prix_series = [trend_map.get(a) or fallback[i] for i, a in enumerate(années)]

    else:
        avg_rates = fetch_fastapi(
            f"/taxe_fonciere/analytics/average-rates/{annee_courante}", {}
        )
        avg = fetch_fastapi(
            f"/api/v1/real-estate/analytics/average-by-year/{annee_courante}", {}
        )
        prix_m2 = round(avg.get("average_price_per_m2", prix_m2))

    # ── 2. Inflation ──────────────────────────────────────────────────────────
    inflation_now     = fetch_fastapi(f"/api/v1/inflation/by-year/{annee_courante}", {})
    inflation_prev    = fetch_fastapi(f"/api/v1/inflation/by-year/{annee_courante - 1}", {})
    inflation_history = fetch_fastapi("/api/v1/inflation/range/2020/2025", [])

    inflation        = inflation_now.get("taux_inflation", 2.1)
    inflation_p      = inflation_prev.get("taux_inflation", 4.9)
    inflation_change = round(inflation - inflation_p, 1)

    infl_map    = {str(r.get("annee")): r.get("taux_inflation", 0) for r in (inflation_history or [])}
    infl_series = [infl_map.get(a, 0) for a in années]

    # ── 3. Stats générales ────────────────────────────────────────────────────
    training_stats = fetch_fastapi("/training/stats", {})

    # ── 4. Graphiques Plotly ──────────────────────────────────────────────────

    # Prix m² — on ajoute la prédiction 2026 si dispo
    années_graph = années.copy()
    prix_graph   = prix_series.copy()
    if prediction_2026:
        pred_prix = prediction_2026.get("predicted_price_per_m2")
        if pred_prix:
            années_graph = années + ['2026']
            prix_graph   = prix_series + [round(pred_prix)]

    fig_prix = px.line(
        x=années_graph, y=prix_graph,
        labels={'x': 'Année', 'y': 'Prix (€/m²)'},
        color_discrete_sequence=['#7A5B3E']
    )
    # Marquer la prédiction en pointillés
    if prediction_2026 and prediction_2026.get("predicted_price_per_m2"):
        fig_prix.add_scatter(
            x=['2025', '2026'],
            y=[prix_series[-1], round(prediction_2026.get("predicted_price_per_m2"))],
            mode='lines',
            line=dict(dash='dash', color='#8CA5A5'),
            name='Prédiction 2026'
        )

    fig_taux = px.line(
        x=années,
        y=[infl_series, [1.0, 1.1, 2.5, 4.0, 3.65, 3.2]],
        labels={'x': 'Année', 'y': '%'},
        color_discrete_sequence=['#8CA5A5', '#7A5B3E']
    )
    fig_index = px.bar(
        x=années, y=[113, 114, 116, 118, 118.4, 119.2],
        labels={'x': 'Année', 'y': 'Index'},
        color_discrete_sequence=['#8CA5A5']
    )
    fig_pop = px.bar(
        x=années, y=[518, 519, 520, 521, 522, 523],
        labels={'x': 'Année', 'y': 'Population (k)'},
        color_discrete_sequence=['#DDCD9E']
    )

    # ── 5. Contexte template ──────────────────────────────────────────────────
    context = {
        'code_postal'    : code_postal,
        'communes'       : communes,
        'taux_tfb'       : taux_moy,
        'prediction_2026': prediction_2026,
        'api_connectee'  : bool(inflation_now),
        'data': {
            'prix_m2'         : prix_m2,
            'prix_m2_change'  : prix_m2_change,
            'index_batiment'  : training_stats.get("index_batiment", 118.4),
            'index_change'    : 1.8,
            'inflation'       : inflation,
            'inflation_change': inflation_change,
            'taux_bancaire'   : avg_rates.get("taux_global_th", 3.65),
            'taux_change'     : -0.2,
            'population'      : 522000,
            'pop_change'      : 0.9,
        },
        'graph_prix'  : pyo.plot(fig_prix,  output_type='div', include_plotlyjs='cdn'),
        'graph_taux'  : pyo.plot(fig_taux,  output_type='div', include_plotlyjs=False),
        'graph_index' : pyo.plot(fig_index, output_type='div', include_plotlyjs=False),
        'graph_pop'   : pyo.plot(fig_pop,   output_type='div', include_plotlyjs=False),
    }
    return render(request, 'market/market.html', context)