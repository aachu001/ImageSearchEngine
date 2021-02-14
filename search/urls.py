from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('accounts/signup/', views.signup, name="signup"),
    path('accounts/login/', views.login_c, name="login"),  
    path("accounts/logout", views.logout_request, name= "logout"),
    path("accounts/profile", views.getProfileDetails, name= "profile"),
    path('activate/<uidb64>/<token>/',views.activate, name='activate'),
    path("password_reset", views.password_reset_request, name="password_reset"),
    path("password_change", views.change_password, name="password_change"),
    path("advsearch",views.advanced_search,name="advanced_search"),
    path("search",views.search,name="search"),
    path("indexData", views.indexData, name="indexData"),
    path("saveItem", views.saveHistory, name="saveItem"),
    path("removeItem", views.removeItemFromProfile, name="removeItem"),
    path("test",views.etest,name="test"),
    path("autocomplete",views.getAutocompleteList,name="autocomplete"),
]