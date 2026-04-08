from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import plotly.express as px
import plotly.offline as pyo

@api_view(["GET"])
def trends(request):
    return Response({
        "Lille": "hausse",
        "Paris": "stable",
        "Marseille": "baisse"
    })




@login_required(login_url='login')
def market_view(request):
    années = ['2020', '2021', '2022', '2023', '2024', '2025']

    fig_prix = px.line(x=années, y=[4350, 4600, 4750, 4820, 4950, 5100],
                    labels={'x': 'Année', 'y': 'Prix (€)'},
                    color_discrete_sequence=['#7A5B3E'])

    fig_taux = px.line(x=années,
                    y=[[0.5, 1.6, 5.2, 4.9, 2.1, 1.8], [1.0, 1.1, 2.5, 4.0, 3.65, 3.2]],
                    labels={'x': 'Année', 'y': '%'},
                    color_discrete_sequence=['#8CA5A5', '#7A5B3E'])

    fig_index = px.bar(x=années, y=[113, 114, 116, 118, 118.4, 119.2],
                    labels={'x': 'Année', 'y': 'Index'},
                    color_discrete_sequence=['#8CA5A5'])

    fig_pop = px.bar(x=années, y=[518, 519, 520, 521, 522, 523],
                    labels={'x': 'Année', 'y': 'Population (k)'},
                    color_discrete_sequence=['#DDCD9E'])
    context = {
            'communes': ['Lyon', 'Bordeaux', 'Marseille', 'Nantes', 'Lille', 'Paris'],
            'data': {
                'prix_m2': 4820,
                'prix_m2_change': 3.2,
                'index_batiment': 118.4,
                'index_change': 1.8,
                'inflation': 2.1,
                'inflation_change': -0.3,
                'taux_bancaire': 3.65,
                'taux_change': -0.2,
                'population': 522000,
                'pop_change': 0.9,
            },
            'graph_prix': pyo.plot(fig_prix, output_type='div', include_plotlyjs='cdn'),
            'graph_taux': pyo.plot(fig_taux, output_type='div', include_plotlyjs=False),
            'graph_index': pyo.plot(fig_index, output_type='div', include_plotlyjs=False),
            'graph_pop': pyo.plot(fig_pop, output_type='div', include_plotlyjs=False),
        } 
    return render(request, 'market/market.html', context)