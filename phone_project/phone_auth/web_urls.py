from django.urls import path
from django.contrib.auth.views import LogoutView
from . import web_views

urlpatterns = [
    path('', web_views.index_view, name='index'),
    path('login/', web_views.login_view, name='login'),
    path('verify/', web_views.verify_code_view, name='verify_code'),
    path('dashboard/', web_views.dashboard_view, name='dashboard'),
    path('activate-invite/', web_views.activate_invite_view, name='activate_invite'),
    path('logout/',
         LogoutView.as_view(template_name='auth/logout.html', next_page='login', http_method_names=['get', 'post']),
         name='logout'),
]
