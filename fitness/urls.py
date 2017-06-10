from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^trimp/$', views.render_trimp, name='render_trimp'),
    url(r'^list/$', views.ActivityList.as_view(), name='activity_list'),
]