"""ep_site URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from rest_framework.authtoken import views

admin.site.site_header = 'Energy Aggregator Admin'
admin.site.site_title = 'Energy Aggregator'
admin.site.index_title = 'Energy Aggregator Index'

admin.autodiscover()

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^api-token-auth/', views.obtain_auth_token),

    # url(r'^heatrank/', include('heatrank.urls', namespace="heatrank")),
    url(r'^api/', include('ep.urls.api', namespace='api')),

    # url(r'^accounts/', include('registration.backends.default.urls')),



    # @todo - this pattern swallows all other urls - fix
    url(r'^', include('ep.urls.web', namespace="web")),

    url(r'^apidocs/', include('rest_framework_docs.urls')),
]
