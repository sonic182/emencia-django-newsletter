"""ModelAdmin for Newsletter"""
from HTMLParser import HTMLParseError

from django.contrib import admin
from django.conf.urls.defaults import *
from django.utils.translation import ugettext as _
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.db.models import Q

from emencia.django.newsletter.models import Contact
from emencia.django.newsletter.models import Newsletter
from emencia.django.newsletter.mailer import Mailer
from emencia.django.newsletter.utils import get_webpage_content

class NewsletterAdmin(admin.ModelAdmin):
    date_hierarchy = 'creation_date'
    list_display = ('title', 'mailing_list', 'server', 'status',
                    'sending_date', 'creation_date', 'modification_date', 'historic_link')
    list_filter = ('mailing_list', 'server', 'status', 'sending_date',
                   'creation_date', 'modification_date')
    search_fields = ('title', 'content', 'header_sender', 'header_reply')
    filter_horizontal = ['test_contacts']
    fieldsets = ((None, {'fields': ('title', 'content',)}),
                 (_('Receivers'), {'fields': ('mailing_list', 'test_contacts',)}),
                 (_('Sending'), {'fields': ('sending_date', 'status',)}),
                 (_('Miscellaneous'), {'fields': ('server', 'header_sender',
                                                  'header_reply', 'slug'),
                                       'classes': ('collapse',)}),
                 )
    prepopulated_fields = {'slug': ('title',)}
    actions = ['send_mail_test', 'make_ready_to_send', 'make_cancel_sending']
    actions_on_top = False
    actions_on_bottom = True

    def get_actions(self, request):
        actions = super(NewsletterAdmin, self).get_actions(request)
        if not request.user.has_perm('newsletter.can_change_status'):
            del actions['make_ready_to_send']
            del actions['make_cancel_sending']
        return actions

    def formfield_for_choice_field(self, db_field, request, **kwargs):
       if db_field.name == 'status' and \
              not request.user.has_perm('newsletter.can_change_status'):           
           kwargs['choices'] = ((Newsletter.DRAFT, _('Default')),)
           return db_field.formfield(**kwargs)
       return super(NewsletterAdmin, self).formfield_for_choice_field(
           db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'test_contacts':
            kwargs['queryset'] = Contact.objects.filter(tester=True)
        return super(NewsletterAdmin, self).formfield_for_manytomany(
            db_field, request, **kwargs)

    def save_model(self, request, newsletter, form, change):
        if newsletter.content.startswith('http://'):
            try:
                newsletter.content = get_webpage_content(newsletter.content)
            except HTMLParseError:
                self.message_user(request, _('Unable to download HTML, due to errors within.'))

        if not request.user.has_perm('newsletter.can_change_status'):
            newsletter.status = form.initial.get('status', Newsletter.DRAFT)

        newsletter.save()

    def historic_link(self, newsletter):
        """Display link for historic"""
        return '<a href="%s">%s</a>' % (newsletter.get_historic_url(), _('View historic'))
    historic_link.allow_tags = True
    historic_link.short_description = _('Historic')

    def send_mail_test(self, request, queryset):
        """Send newsletter in test"""
        for newsletter in queryset:
            if newsletter.test_contacts.count():
                mailer = Mailer(newsletter, test=True)
                try:
                    mailer.run()
                except HTMLParseError:
                    self.message_user(request, _('Unable send newsletter, due to errors within HTML.'))
                    continue
                self.message_user(request, _('%s succesfully sent.') % newsletter)
            else:
                self.message_user(request, _('No test contacts assigned for %s.') % newsletter)
    send_mail_test.short_description = _('Send test email')

    def make_ready_to_send(self, request, queryset):
        """Make newsletter ready to send"""
        queryset = queryset.filter(status=Newsletter.DRAFT)
        for newsletter in queryset:
            newsletter.status = Newsletter.WAITING
            newsletter.save()
        self.message_user(request, _('%s newletters are ready to send') % queryset.count())
    make_ready_to_send.short_description = _('Make ready to send')

    def make_cancel_sending(self, request, queryset):
        """Cancel the sending of newsletters"""
        queryset = queryset.filter(Q(status=Newsletter.WAITING) |
                                   Q(status=Newsletter.SENDING))
        for newsletter in queryset:
            newsletter.status = Newsletter.CANCELED
            newsletter.save()
        self.message_user(request, _('%s newletters are cancelled') % queryset.count())
    make_cancel_sending.short_description = _('Cancel the sending')

    def historic(self, request, slug):
        """Display the historic of a newsletters"""
        opts = self.model._meta
        newsletter = get_object_or_404(Newsletter, slug=slug)

        context = {'title': _('Stats %s') % newsletter.__unicode__(),
                   'original': newsletter,
                   'opts': opts,
                   'object_id': newsletter.pk,
                   'root_path': self.admin_site.root_path,
                   'app_label': opts.app_label,}
        return render_to_response('newsletter/newsletter_historic.html',
                                  context,
                                  context_instance=RequestContext(request))

    def get_urls(self):
        urls = super(NewsletterAdmin, self).get_urls()
        my_urls = patterns('',
                           url(r'^historic/(?P<slug>[-\w]+)/$', self.historic,
                               name='newsletter_newsletter_historic'),)
        return my_urls + urls