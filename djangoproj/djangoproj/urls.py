from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^docx_search_replace/start$',
       'djangoproj.docx_search_replace.views.start'),
    url(r'^docx_search_replace/configure_search_replace$',
       'djangoproj.docx_search_replace.views.configure_search_replace'),
)
