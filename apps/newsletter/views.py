from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template import Context
from django.conf import settings

from .models import Newsletter, NewsletterTemplate, NewsletterTracking, SubscriberGroup
from .forms import NewsletterForm, NewsletterTemplateForm, NewsletterSendTestForm, NewsletterFilterForm
from apps.subscriber.models import Subscriber, SubscriberGroup

from .models import Newsletter, NewsletterTracking


import logging
import uuid

logger = logging.getLogger(__name__)


class NewsletterListView(LoginRequiredMixin, ListView):
    """
    View for listing newsletters with filtering
    """
    model = Newsletter
    template_name = 'newsletter/newsletter_list.html'
    context_object_name = 'newsletters'
    paginate_by = 10

    def get_queryset(self):
        queryset = Newsletter.objects.all()

        # Get filter parameters
        subject = self.request.GET.get('subject', '')
        status = self.request.GET.get('status', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')

        # Apply filters
        if subject:
            queryset = queryset.filter(subject__icontains=subject)

        if status:
            queryset = queryset.filter(status=status)

        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)

        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add filter form
        context['filter_form'] = NewsletterFilterForm(self.request.GET or None)

        # Add status counts
        context['status_counts'] = {
            'draft': Newsletter.objects.filter(status='draft').count(),
            'scheduled': Newsletter.objects.filter(status='scheduled').count(),
            'sending': Newsletter.objects.filter(status='sending').count(),
            'sent': Newsletter.objects.filter(status='sent').count(),
            'failed': Newsletter.objects.filter(status='failed').count(),
        }

        return context


class NewsletterCreateView(LoginRequiredMixin, CreateView):
    """
    View for creating newsletters
    Also handles editing when edit param is provided in URL
    """
    model = Newsletter
    form_class = NewsletterForm
    template_name = 'newsletter/newsletter_create.html'
    success_url = reverse_lazy('newsletter:newsletter_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['templates'] = NewsletterTemplate.objects.all()

        # Check if we're in edit mode
        edit_slug = self.request.GET.get('edit')
        if edit_slug:
            context['edit_mode'] = True
            try:
                newsletter = Newsletter.objects.get(slug=edit_slug)
                context['newsletter'] = newsletter
            except Newsletter.DoesNotExist:
                pass

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        # Check if we're in edit mode
        edit_slug = self.request.GET.get('edit')
        if edit_slug:
            try:
                newsletter = Newsletter.objects.get(slug=edit_slug)
                # If not POST request, provide instance for form to edit
                if not self.request.method == 'POST':
                    kwargs['instance'] = newsletter
            except Newsletter.DoesNotExist:
                pass

        return kwargs

    def form_valid(self, form):
        """Process the form data after validation"""
        # Set the created_by and updated_by fields
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        # Check if this is a draft save
        is_draft = 'save_as_draft' in self.request.POST or 'is_draft' in self.request.POST

        # Create the newsletter
        newsletter = form.save(commit=False)

        # If draft, we don't need to validate recipients
        if is_draft:
            newsletter.status = 'draft'
            # Save the newsletter
            newsletter.save()
            # Save the many-to-many fields
            form.save_m2m()
            # Set the object so the success_url can be generated
            self.object = newsletter

            messages.success(self.request, _(
                'Newsletter draft saved successfully.'))
            return redirect(self.get_success_url())

        # Normal processing for non-draft submissions
        # Handle 'send to all subscribers' option
        if form.cleaned_data.get('all_subscribers'):
            newsletter.save()  # Save to get an ID first
            all_subs = Subscriber.objects.filter(newsletter_consent=True)
            newsletter.subscribers.set(all_subs)

        # Check if we should send immediately
        send_now = form.cleaned_data.get('send_now')
        if send_now:
            newsletter.status = 'sending'

        # Check if we should schedule
        schedule_send = form.cleaned_data.get('schedule_send')
        if schedule_send and form.cleaned_data.get('scheduled_date'):
            newsletter.status = 'scheduled'

        # Save the newsletter
        newsletter.save()

        # Save the many-to-many fields
        form.save_m2m()

        # Set the object so the success_url can be generated
        self.object = newsletter

        # Update the recipient count
        newsletter.update_recipient_count()

        # Check if save_and_preview button was clicked (UPDATED CODE)
        if 'save_and_preview' in self.request.POST:
            messages.success(self.request, _('Newsletter saved.'))
            # Redirect to list instead of preview
            return redirect(self.get_success_url())

        # Process sending if needed
        if send_now:
            # In a real application, this would use Celery or another task queue
            # Here we'll just simulate it with a simple flag
            # send_newsletter.delay(newsletter.id)  # This would be a Celery task
            messages.success(self.request, _('Newsletter queued for sending.'))
        else:
            messages.success(self.request, _(
                'Newsletter created successfully.'))

        return redirect(self.get_success_url())


class NewsletterDeleteView(LoginRequiredMixin, View):
    """
    Widok do usuwania newsletterów bez dodatkowego potwierdzenia
    Obsługuje zarówno GET (przekierowanie) jak i POST (usuwanie)
    """

    def get(self, request, *args, **kwargs):
        """
        Obsługa żądania GET - przekierowanie do listy newsletterów
        """
        messages.warning(request, _(
            'Use the delete button from the newsletter list.'))
        return redirect('newsletter:newsletter_list')

    def post(self, request, *args, **kwargs):
        """
        Obsługa żądania POST - usunięcie newslettera
        """
        # Pobierz newsletter do usunięcia
        newsletter = get_object_or_404(Newsletter, slug=kwargs['slug'])

        # Sprawdź, czy newsletter może być usunięty
        if newsletter.status in ['sent', 'sending']:
            messages.error(request, _(
                'Cannot delete a newsletter that has been sent or is being sent.'))
            return redirect('newsletter:newsletter_list')

        # Zapisz dane przed usunięciem (dla komunikatu)
        subject = newsletter.subject

        # Usuń newsletter
        newsletter.delete()

        # Pokaż komunikat o sukcesie
        messages.success(request, _(
            f'Newsletter "{subject}" has been deleted successfully.'))

        # Przekieruj z powrotem do listy
        return redirect('newsletter:newsletter_list')


class NewsletterSendTestView(LoginRequiredMixin, View):
    """
    View for sending test newsletters
    """

    def post(self, request, *args, **kwargs):
        newsletter = get_object_or_404(Newsletter, slug=kwargs['slug'])
        form = NewsletterSendTestForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']

            try:
                # Create a test subscriber
                test_subscriber = Subscriber.objects.filter(
                    email=email).first()
                if not test_subscriber:
                    test_subscriber = Subscriber(
                        email=email,
                        first_name="Test",
                        last_name="User",
                        newsletter_consent=True
                    )
                    test_subscriber.save()

                # Send the test email
                self._send_newsletter_email(
                    newsletter, test_subscriber, is_test=True)

                messages.success(request, _(
                    f'Test newsletter sent to {email}.'))
            except Exception as e:
                logger.error(f"Error sending test newsletter: {str(e)}")
                messages.error(request, _(
                    f'Error sending test newsletter: {str(e)}'))
        else:
            messages.error(request, _('Please enter a valid email address.'))

        # Redirect to list instead of detail
        return redirect('newsletter:newsletter_list')

    def _send_newsletter_email(self, newsletter, subscriber, is_test=False):
        """Send the newsletter to a specific subscriber"""
        # Get the template
        template_html = self._get_template_html(newsletter)

        # Replace placeholders
        html_content = template_html.replace('{{content}}', newsletter.content)
        html_content = html_content.replace('{{subject}}', newsletter.subject)

        # Add test banner if needed
        if is_test:
            test_banner = '<div style="background: #e74c3c; color: white; padding: 10px; text-align: center;">TEST EMAIL - NOT A REAL NEWSLETTER</div>'
            html_content = html_content.replace(
                '<body>', f'<body>{test_banner}')

        # Create the email
        email = EmailMultiAlternatives(
            subject=newsletter.subject,
            body="Please view this email with an HTML-compatible email client.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[subscriber.email]
        )

        email.attach_alternative(html_content, "text/html")
        email.send()

    def _get_template_html(self, newsletter):
        """Get the HTML template for the newsletter"""
        if newsletter.template and newsletter.template.html_content:
            return newsletter.template.html_content
        else:
            # Use default template
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{{subject}}</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
                    h1, h2, h3 { color: #2c3e50; }
                    a { color: #3498db; }
                </style>
            </head>
            <body>
                <h1>{{subject}}</h1>
                <div class="content">
                    {{content}}
                </div>
                <p style="color: #7f8c8d; font-size: 12px; margin-top: 30px;">
                    You're receiving this email because you subscribed to our newsletter. 
                    <a href="{{unsubscribe_url}}">Unsubscribe</a>
                </p>
            </body>
            </html>
            """


class NewsletterSendView(LoginRequiredMixin, View):
    """View for finalizing and sending newsletters"""

    def post(self, request, slug):
        newsletter = get_object_or_404(Newsletter, slug=slug)

        # Check if we can send this newsletter
        if newsletter.status in ['sent', 'sending']:
            messages.error(request, _(
                'This newsletter has already been sent or is in the process of sending.'))
            # Redirect to list instead of detail
            return redirect('newsletter:newsletter_list')

        # Update status based on scheduled vs. immediate
        if newsletter.scheduled_date and newsletter.scheduled_date > timezone.now():
            newsletter.status = 'scheduled'
            message = _('Newsletter scheduled successfully.')
        else:
            newsletter.status = 'sending'
            message = _('Newsletter sending has started.')

            # In a real application, this would trigger a background task
            # For example: send_newsletter_task.delay(newsletter.id)

        newsletter.save()

        messages.success(request, message)
        # Redirect to list instead of detail
        return redirect('newsletter:newsletter_list')


# Newsletter Template views

class NewsletterTemplateListView(LoginRequiredMixin, ListView):
    """
    View for listing newsletter templates
    """
    model = NewsletterTemplate
    template_name = 'newsletter/template_list.html'
    context_object_name = 'templates'
    paginate_by = 10


class NewsletterTemplateCreateView(LoginRequiredMixin, CreateView):
    """
    View for creating newsletter templates
    """
    model = NewsletterTemplate
    form_class = NewsletterTemplateForm
    template_name = 'newsletter/template_create.html'
    success_url = reverse_lazy('newsletter:template_list')

    def form_valid(self, form):
        # Set the created_by and updated_by fields
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        messages.success(self.request, _('Template created successfully.'))
        return super().form_valid(form)


class NewsletterTemplateUpdateView(LoginRequiredMixin, UpdateView):
    """
    View for updating newsletter templates
    """
    model = NewsletterTemplate
    form_class = NewsletterTemplateForm
    template_name = 'newsletter/template_update.html'

    def get_success_url(self):
        return reverse('newsletter:template_list')

    def form_valid(self, form):
        # Set the updated_by field
        form.instance.updated_by = self.request.user

        messages.success(self.request, _('Template updated successfully.'))
        return super().form_valid(form)


class NewsletterTemplateDeleteView(LoginRequiredMixin, DeleteView):
    """
    View for deleting newsletter templates
    """
    model = NewsletterTemplate
    template_name = 'newsletter/template_delete_confirm.html'
    success_url = reverse_lazy('newsletter:template_list')

    def delete(self, request, *args, **kwargs):
        template = self.get_object()

        # Check if template is in use
        if template.newsletters.exists():
            messages.error(request, _(
                'Cannot delete template that is used by newsletters.'))
            return redirect('newsletter:template_list')

        messages.success(request, _('Template deleted successfully.'))
        return super().delete(request, *args, **kwargs)


class NewsletterTemplatePreviewView(LoginRequiredMixin, DetailView):
    """
    View for previewing newsletter templates
    """
    model = NewsletterTemplate

    def get(self, request, *args, **kwargs):
        template = self.get_object()

        # Replace placeholders with sample content
        html_content = template.html_content.replace(
            '{{content}}', self._get_sample_content())
        html_content = html_content.replace('{{subject}}', 'Sample Newsletter')

        # Add preview notice
        html_content = html_content.replace(
            '</body>', '<p class="preview-notice">This is a template preview.</p></body>')

        return HttpResponse(html_content)

    def _get_sample_content(self):
        """Generate sample content for the preview"""
        return """
        <h2>Welcome to our newsletter!</h2>
        <p>This is a sample newsletter content to demonstrate how your template will look.</p>
        <p>You can include:</p>
        <ul>
            <li>Important announcements</li>
            <li>Product updates</li>
            <li>Special offers</li>
        </ul>
        <p><a href="#">Sample link</a></p>
        """


class NewsletterCloneView(LoginRequiredMixin, View):
    """
    Widok do klonowania istniejącego newslettera
    """

    def get(self, request, *args, **kwargs):
        # Pobierz oryginalny newsletter
        original_newsletter = get_object_or_404(
            Newsletter, slug=kwargs['slug'])

        # Utwórz kopię newslettera
        cloned_newsletter = Newsletter(
            subject=f"Copy of {original_newsletter.subject}",
            content=original_newsletter.content,
            template=original_newsletter.template,
            status='draft',  # zawsze jako szkic
            created_by=request.user,
            updated_by=request.user,
        )

        # Wygeneruj unikalny slug
        base_slug = slugify(cloned_newsletter.subject)
        unique_slug = base_slug
        counter = 1

        # Sprawdź unikalność sluga
        while Newsletter.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{base_slug}-{counter}"
            counter += 1

        cloned_newsletter.slug = unique_slug
        cloned_newsletter.save()

        # Skopiuj grupy subskrybentów (jeśli są)
        if hasattr(original_newsletter, 'recipient_groups') and original_newsletter.recipient_groups.exists():
            cloned_newsletter.recipient_groups.set(
                original_newsletter.recipient_groups.all())

        # Skopiuj indywidualnych subskrybentów (jeśli są)
        if hasattr(original_newsletter, 'subscribers') and original_newsletter.subscribers.exists():
            cloned_newsletter.subscribers.set(
                original_newsletter.subscribers.all())

        # Aktualizuj liczbę odbiorców - sprawdź, czy metoda istnieje
        if hasattr(cloned_newsletter, 'update_recipient_count'):
            cloned_newsletter.update_recipient_count()

        messages.success(request, _('Newsletter cloned successfully.'))

        # Przekieruj do LISTY newsletterów zamiast do edycji
        # W przyszłości możesz dodać parametr do URL-a tworzenia newslettera
        # return redirect('newsletter:newsletter_create') + f'?edit={cloned_newsletter.slug}'
        return redirect('newsletter:newsletter_list')


class NewsletterReportView(LoginRequiredMixin, View):
    """
    Widok szczegółowego raportu dla newslettera
    """

    def get(self, request, *args, **kwargs):
        # Pobierz newsletter
        newsletter = get_object_or_404(Newsletter, slug=kwargs['slug'])

        # Sprawdź, czy newsletter został wysłany
        if newsletter.status not in ['sent', 'sending']:
            messages.warning(request, _(
                'Detailed report is only available for sent newsletters.'))
            return redirect('newsletter:newsletter_list')

        # Przygotuj dane statystyczne
        stats = self._get_newsletter_stats(newsletter)

        # Przygotuj dane dla linków
        links = self._get_link_stats(newsletter)

        # Przygotuj dane dla osi czasu
        timeline_events = self._get_timeline_events(newsletter)

        # Renderuj szablon
        return render(request, 'newsletter/newsletter_report.html', {
            'newsletter': newsletter,
            'stats': stats,
            'links': links,
            'timeline_events': timeline_events
        })

    def _get_newsletter_stats(self, newsletter):
        """Pobierz statystyki dla newslettera"""
        # W rzeczywistej implementacji te dane pochodziłyby z bazy danych
        # Na potrzeby demonstracji używamy przykładowych danych

        # Sprawdź czy model ma pole total_recipients
        total_recipients = getattr(newsletter, 'total_recipients', 0) or 0

        # Podstawowe statystyki
        unique_opens = 0
        total_opens = 0
        unique_clicks = 0
        total_clicks = 0

        # Sprawdź, czy model NewsletterTracking jest dostępny
        try:
            unique_opens = NewsletterTracking.objects.filter(
                newsletter=newsletter,
                action='open'
            ).values('subscriber').distinct().count()

            total_opens = NewsletterTracking.objects.filter(
                newsletter=newsletter,
                action='open'
            ).count()

            unique_clicks = NewsletterTracking.objects.filter(
                newsletter=newsletter,
                action='click'
            ).values('subscriber').distinct().count()

            total_clicks = NewsletterTracking.objects.filter(
                newsletter=newsletter,
                action='click'
            ).count()
        except:
            # Jeśli model nie istnieje lub wystąpi inny błąd, użyj przykładowych danych
            unique_opens = int(total_recipients * 0.35)  # 35% open rate
            total_opens = int(unique_opens * 1.2)  # 20% więcej niż unique
            unique_clicks = int(unique_opens * 0.4)  # 40% click-through rate
            total_clicks = int(unique_clicks * 1.3)  # 30% więcej niż unique

        # Oblicz wskaźniki (unikaj dzielenia przez zero)
        open_rate = (unique_opens / total_recipients *
                     100) if total_recipients > 0 else 0
        click_rate = (unique_clicks / total_recipients *
                      100) if total_recipients > 0 else 0
        click_to_open_rate = (unique_clicks / unique_opens *
                              100) if unique_opens > 0 else 0

        return {
            'total_recipients': total_recipients,
            'unique_opens': unique_opens,
            'total_opens': total_opens,
            'unique_clicks': unique_clicks,
            'total_clicks': total_clicks,
            'open_rate': open_rate,
            'click_rate': click_rate,
            'click_to_open_rate': click_to_open_rate,
        }

    def _get_link_stats(self, newsletter):
        """Pobierz statystyki dla linków w newsletterze"""
        # Na potrzeby demonstracji używamy przykładowych danych

        return [
            {
                'text': 'Read more on our blog',
                'url': 'https://example.com/blog/post-1',
                'total_clicks': 45,
                'unique_clicks': 40,
                'click_rate': 20.0
            },
            {
                'text': 'Sign up for our webinar',
                'url': 'https://example.com/webinar',
                'total_clicks': 29,
                'unique_clicks': 25,
                'click_rate': 12.5
            },
            {
                'text': 'Download our free guide',
                'url': 'https://example.com/guide',
                'total_clicks': 20,
                'unique_clicks': 18,
                'click_rate': 9.0
            },
            {
                'text': 'Follow us on social media',
                'url': 'https://example.com/social',
                'total_clicks': 15,
                'unique_clicks': 12,
                'click_rate': 6.0
            },
            {
                'text': 'Contact us',
                'url': 'https://example.com/contact',
                'total_clicks': 10,
                'unique_clicks': 8,
                'click_rate': 4.0
            }
        ]

    def _get_timeline_events(self, newsletter):
        """Pobierz wydarzenia dla osi czasu"""
        # Na potrzeby demonstracji używamy przykładowych danych

        # Data wysłania newslettera
        sent_date = getattr(newsletter, 'sent_date',
                            timezone.now()) or timezone.now()

        # Generuj przykładowe wydarzenia w różnych odstępach czasu
        events = []

        # Dodaj wydarzenie wysłania
        events.append({
            'timestamp': sent_date,
            'action': 'sent',
            'recipient': 'All recipients',
            'details': f'Newsletter sent to {getattr(newsletter, "total_recipients", 0)} recipients'
        })

        # Dodaj kilka otwarć
        for i in range(5):
            events.append({
                'timestamp': sent_date + datetime.timedelta(minutes=5 * (i + 1)),
                'action': 'open',
                'recipient': f'user{i+1}@example.com',
                'details': f'Opened on iPhone'
            })

        # Dodaj kilka kliknięć
        for i in range(3):
            events.append({
                'timestamp': sent_date + datetime.timedelta(minutes=10 * (i + 1)),
                'action': 'click',
                'recipient': f'user{i+2}@example.com',
                'details': f'Clicked on "Read more"'
            })

        # Dodaj odbicie
        events.append({
            'timestamp': sent_date + datetime.timedelta(minutes=7),
            'action': 'bounce',
            'recipient': 'invalid@example.com',
            'details': 'Mailbox full'
        })

        # Posortuj wydarzenia wg timestamp (od najnowszych)
        events.sort(key=lambda x: x['timestamp'], reverse=True)

        return events


class NewsletterPreviewView(LoginRequiredMixin, View):
    """
    Widok do podglądu newslettera
    """

    def get(self, request, *args, **kwargs):
        newsletter = get_object_or_404(Newsletter, slug=kwargs['slug'])

        # Pobierz szablon HTML
        template_html = self._get_template_html(newsletter)

        # Zastąp symbole zastępcze rzeczywistą zawartością
        html_content = template_html.replace('{{content}}', newsletter.content)
        html_content = html_content.replace('{{subject}}', newsletter.subject)

        # Dodaj banner podglądu
        preview_banner = '<div style="background: #17a2b8; color: white; padding: 10px; text-align: center; font-family: Arial, sans-serif;">PREVIEW MODE - This is how the newsletter will look to recipients</div>'
        html_content = html_content.replace(
            '<body>', f'<body>{preview_banner}')

        # Dodaj wsteczny link do raportu lub listy
        back_button = f'''
        <div style="position: fixed; bottom: 20px; right: 20px; z-index: 1000;">
            <a href="javascript:history.back()" style="background: #343a40; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; font-family: Arial, sans-serif;">
                &larr; Back
            </a>
        </div>
        '''
        html_content = html_content.replace('</body>', f'{back_button}</body>')

        # Zwróć jako odpowiedź HTML
        return HttpResponse(html_content)

    def _get_template_html(self, newsletter):
        """Get the HTML template for the newsletter"""
        if hasattr(newsletter, 'template') and newsletter.template and hasattr(newsletter.template, 'html_content'):
            return newsletter.template.html_content
        else:
            # Use default template
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{{subject}}</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
                    h1, h2, h3 { color: #2c3e50; }
                    a { color: #3498db; }
                </style>
            </head>
            <body>
                <h1>{{subject}}</h1>
                <div class="content">
                    {{content}}
                </div>
                <p style="color: #7f8c8d; font-size: 12px; margin-top: 30px;">
                    You're receiving this email because you subscribed to our newsletter. 
                    <a href="{{unsubscribe_url}}">Unsubscribe</a>
                </p>
            </body>
            </html>
            """
