"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from GeoLogis.views import  ListeArticlesView
from GeoLogis.views import ListeArticlesView, info_view


urlpatterns = [
    path('', ListeArticlesView.as_view(), name='home'),
    path('admin/', admin.site.urls),
    path('predictions/', include('predictions.urls')), 
    path('information/', info_view, name='info_key'),
    path('', include('users.urls')),
    path('api/market/', include('market.urls')),
    path('predictions/', include('predictions.urls')),
    path('api/geologis/', include('GeoLogis.urls')),
]

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'profil'
LOGOUT_REDIRECT_URL = 'home'
PASSWORD_CHANGE_REDIRECT_URL = 'profil'