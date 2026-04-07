"""
URL configuration for kadi_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path , include
from core import views as template_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('', template_views.login_view),
    path('login/', template_views.login_view),
    path('dashboard/', template_views.dashboard_view),
    path('admin-panel/', template_views.admin_dashboard_view),
    path('reports/', template_views.reports_view),
    path('manage/users/', template_views.users_management_view),
    path('manage/snacks/', template_views.snacks_management_view),
    path('history/', template_views.history_view),
    path('reconciliation/', template_views.reconciliation_view),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
