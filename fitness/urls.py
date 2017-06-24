from django.conf.urls import url, include

from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'activities', views.ActivityViewSet)

urlpatterns = [
    url(r'^control_panel/$', views.ControlPanelView.as_view(), name='control_panel'),
    url(r'^trimp/$', views.render_trimp, name='render_trimp'),
    url(r'^list/$', views.ActivityList.as_view(), name='activity_list'),
    url(r'^activity/(?P<pk>[-\w]+)/$', views.ActivityDetail.as_view(), name='activity'),
    url(r'^activity_svg/(?P<pk>[-\w]+)\.svg$', views.ActivitySVG.as_view(), name='activity_svg'),
    url(r'^api/', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]