from django.conf.urls import patterns, include, url
from myuw_api.views import StudClasScheCurQuarView, UserScheduleBooks

urlpatterns = patterns('myuw_spi.views',
                       url(r'v1/schedule/current/$',
                           StudClasScheCurQuarView().run),
                       url(r'v1/books/current/$', UserScheduleBooks().run),
                  #    url(r'v1/search/(?P<query>.*)$', SearchView().run),
)
