from django.conf.urls import include, url
from django.contrib import admin
from swautocheckin import views

urlpatterns = [
    url(r'^$', views.email_view, name='email'),
    url(r'^passenger/(?P<passenger_uuid>[^/]+)/create-reservation$', views.reservation_view, name='reservation'),
    url(r'^reservation/(?P<reservation_uuid>[^/]+)/success$', views.success_view, name='success'),

    url(r'^error$', views.force_error_view),
    url(r'^admin/', include(admin.site.urls)),
]

handler404 = 'swautocheckin.views.handler404'
handler500 = 'swautocheckin.views.handler500'