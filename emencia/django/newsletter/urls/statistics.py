"""Urls for the emencia.django.newsletter statistics"""
from django.conf.urls import url
from emencia.django.newsletter.views.statistics import view_newsletter_statistics, view_newsletter_report, view_newsletter_charts, view_newsletter_density

# urlpatterns = ('emencia.django.newsletter.views.statistics',
urlpatterns = (url(r'^(?P<slug>[-\w]+)/$',
                           view_newsletter_statistics,
                           name='newsletter_newsletter_statistics'),
                       url(r'^report/(?P<slug>[-\w]+)/$',
                           view_newsletter_report,
                           name='newsletter_newsletter_report'),
                       url(r'^charts/(?P<slug>[-\w]+)/$',
                           view_newsletter_charts,
                           name='newsletter_newsletter_charts'),
                       url(r'^density/(?P<slug>[-\w]+)/$',
                           view_newsletter_density,
                           name='newsletter_newsletter_density'),
                       )
