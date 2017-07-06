from django.conf.urls import url, include

from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'activities', views.ActivityViewSet, base_name='activity')
router.register(r'trimp', views.TrimpViewSet, base_name='trimp')

urlpatterns = [
    url(r'^control_panel/$', views.ControlPanelView.as_view(), name='control_panel'),
    url(r'^trimp/$', views.TrimpView.as_view(), name='render_trimp'),
    url(r'^list/$', views.ActivityList.as_view(), name='activity_list'),
    url(r'^upload/$', views.UploadView.as_view(), name='upload'),
    url(r'^activity/(?P<pk>[-\w]+)/$', views.ActivityDetail.as_view(), name='activity'),
    url(r'^recalculate/(?P<pk>[-\w]+)/$', views.RecalculateTRIMPView.as_view(), name='recalculate'),
    url(r'^activity_svg/(?P<pk>[-\w]+)\.svg$', views.ActivitySVG.as_view(), name='activity_svg'),
    url(r'^api/', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]