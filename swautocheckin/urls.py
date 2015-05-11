from django.conf.urls import include, url
from django.contrib import admin
from swautocheckin import views

urlpatterns = [
    url(r'^$', views.email_view, name='email'),
    url(r'^passenger/(?P<passenger_uuid>[^/]+)/create-reservation$', views.reservation_view, name='reservation'),
    url(r'^reservation/(?P<reservation_uuid>[^/]+)/success$', views.success_view, name='success'),

    url(r'^admin/', include(admin.site.urls)),
]
