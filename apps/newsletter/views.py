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
import datetime
import json
import re

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

        # Pobierz wartość opcji use_uuid z formularza
        use_uuid = form.cleaned_data.get('use_uuid', True)
        newsletter.use_uuid = use_uuid

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

        # Check if we're sending the newsletter directly
        send_newsletter = 'send_newsletter' in self.request.POST

        # Check if we should send immediately - WAŻNE: nie ustawiamy statusu 'sending' jeśli send_newsletter
        send_now = form.cleaned_data.get('send_now')
        if send_now and not send_newsletter:
            newsletter.status = 'sending'

        # Check if we should schedule
        schedule_send = form.cleaned_data.get('schedule_send')
        if schedule_send and form.cleaned_data.get('scheduled_date'):
            newsletter.status = 'scheduled'
            newsletter.scheduled_date = form.cleaned_data.get('scheduled_date')

        # Save the newsletter
        try:
            newsletter.save()
            # Save the many-to-many fields
            form.save_m2m()
        except Exception as e:
            logger.error(f"Error saving newsletter: {str(e)}")
            messages.error(self.request, _(
                f'Error saving newsletter: {str(e)}'))
            return self.form_invalid(form)

        # Set the object so the success_url can be generated
        self.object = newsletter

        # Update the recipient count
        try:
            newsletter.total_recipients = newsletter.get_recipient_count()
            newsletter.save(update_fields=['total_recipients'])
        except Exception as e:
            logger.warning(f"Could not update recipient count: {str(e)}")

        # Check if save_and_preview button was clicked
        if 'save_and_preview' in self.request.POST:
            messages.success(self.request, _('Newsletter saved.'))
            # Redirect to preview
            return redirect(reverse('newsletter:newsletter_preview', kwargs={'slug': newsletter.slug}))

        # Process sending if needed
        if send_newsletter:
            # WAŻNE: ustawiamy status na 'draft' przed przekierowaniem
            newsletter.status = 'draft'
            newsletter.save(update_fields=['status'])

            # Przekieruj do widoku wysyłki
            messages.success(self.request, _('Newsletter queued for sending.'))
            return redirect(reverse('newsletter:newsletter_send', kwargs={'slug': newsletter.slug}))
        elif send_now:
            # W przypadku gdy send_now jest ustawione, ale nie przez przycisk send_newsletter
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

    def _send_newsletter_email(self, newsletter, subscriber):
        """Send the newsletter to a specific subscriber"""
        # Get the template
        template_html = self._get_template_html(newsletter)

        # Replace placeholders
        html_content = template_html.replace('{{content}}', newsletter.content)
        html_content = html_content.replace('{{subject}}', newsletter.subject)

        # Add subscriber-specific placeholders
        full_name = f"{subscriber.first_name or ''} {subscriber.last_name or ''}".strip()
        html_content = html_content.replace('{{recipient_name}}', full_name)
        html_content = html_content.replace(
            '{{recipient_email}}', subscriber.email)

        # Add unsubscribe link - POPRAWIONA WERSJA
        try:
            site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
            unsubscribe_url = f"{site_url}/unsubscribe/{subscriber.id}/"
        except Exception as e:
            logger.warning(f"Error creating unsubscribe URL: {str(e)}")
            unsubscribe_url = "#unsubscribe"  # Fallback

        html_content = html_content.replace(
            '{{unsubscribe_url}}', unsubscribe_url)

        # Add tracking pixel if newsletter has tracking enabled - POPRAWIONA WERSJA
        if getattr(newsletter, 'add_tracking', True):
            tracking_id = str(uuid.uuid4())
            try:
                site_url = getattr(settings, 'SITE_URL',
                                   'http://127.0.0.1:8000')
                tracking_url = f"{site_url}/track/open/{tracking_id}/"
            except Exception as e:
                logger.warning(f"Error creating tracking URL: {str(e)}")
                tracking_url = "/track/open/{tracking_id}/"  # Względny URL

            tracking_pixel = f'<img src="{tracking_url}" style="width:1px;height:1px;display:none;" alt="" />'
            html_content = html_content.replace(
                '</body>', f'{tracking_pixel}</body>')

        # Create the email
        # Reszta metody bez zmian...
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

    def get(self, request, slug):
        """Handle GET requests for sending newsletters"""
        return self._process_send_request(request, slug)

    def post(self, request, slug):
        """Handle POST requests for sending newsletters"""
        return self._process_send_request(request, slug)

    def _process_send_request(self, request, slug):
        """Common logic for processing both GET and POST requests"""
        logger.info(f"Starting _process_send_request for newsletter {slug}")
        try:
            newsletter = get_object_or_404(Newsletter, slug=slug)
            logger.info(
                f"Found newsletter: {newsletter.id} - {newsletter.subject}")

            # Check if we can send this newsletter
            if newsletter.status in ['sent', 'sending']:
                logger.warning(
                    f"Newsletter {newsletter.id} already in status: {newsletter.status}")
                messages.error(request, _(
                    'This newsletter has already been sent or is in the process of sending.'))
                return redirect('newsletter:newsletter_list')

            # Update status based on scheduled vs. immediate
            if newsletter.scheduled_date and newsletter.scheduled_date > timezone.now():
                newsletter.status = 'scheduled'
                message = _('Newsletter scheduled successfully.')
                logger.info(
                    f"Newsletter {newsletter.id} scheduled for {newsletter.scheduled_date}")
            else:
                newsletter.status = 'sending'
                message = _('Newsletter sending has started.')
                logger.info(
                    f"Setting newsletter {newsletter.id} status to 'sending'")

                try:
                    logger.info(
                        f"About to call send_newsletter for {newsletter.id}")
                    recipients_count = self.send_newsletter(newsletter)
                    logger.info(
                        f"send_newsletter returned with {recipients_count} recipients")

                    # DODANA LINIA - pobierz świeży status newslettera
                    newsletter.refresh_from_db()
                    logger.info(
                        f"Newsletter status after sending: {newsletter.status}")

                    # Zaktualizuj komunikat w zależności od statusu
                    if newsletter.status == 'sent':
                        message = _('Newsletter sent successfully.')
                    elif newsletter.status == 'failed':
                        message = _('Newsletter sending failed.')

                except Exception as e:
                    logger.critical(
                        f"Exception during send_newsletter: {str(e)}", exc_info=True)
                    newsletter.status = 'failed'
                    message = _('Error sending newsletter: {}').format(str(e))

                # Zapisz tylko jeśli newsletter nadal jest w statusie 'sending'
                # (funkcja send_newsletter mogła już zaktualizować status)
                if newsletter.status == 'sending':
                    try:
                        newsletter.save()
                        logger.info(
                            f"Saved newsletter with status {newsletter.status}")
                    except Exception as e:
                        logger.critical(
                            f"Failed to save newsletter: {str(e)}", exc_info=True)
                else:
                    logger.info(
                        f"Not saving newsletter status as it's already set to {newsletter.status}")

            # Wyświetl odpowiedni komunikat
            if newsletter.status == 'failed':
                messages.error(request, message)
            else:
                messages.success(request, message)

            logger.info(f"Redirecting to newsletter list")
            return redirect('newsletter:newsletter_list')

        except Exception as e:
            logger.critical(
                f"Uncaught exception in _process_send_request: {str(e)}", exc_info=True)
            messages.error(request, _(
                'An unexpected error occurred: {}').format(str(e)))
            return redirect('newsletter:newsletter_list')

    def send_newsletter(self, newsletter):
        """Send the newsletter to all recipients with detailed error handling"""
        logger.info(
            f"Starting to send newsletter: {newsletter.subject} (ID: {newsletter.id})")

        try:
            # Pobierz wszystkich odbiorców
            direct_subscribers = set(
                newsletter.subscribers.filter(newsletter_consent=True))
            logger.info(f"Direct subscribers: {len(direct_subscribers)}")

            # Dodaj subskrybentów z grup
            group_subscribers = set()
            for group in newsletter.subscriber_groups.all():
                try:
                    subscribers = group.subscriber.filter(
                        newsletter_consent=True)
                    group_subscribers.update(subscribers)
                    logger.info(
                        f"Added {len(subscribers)} subscribers from group {group.id}")
                except Exception as e:
                    logger.error(
                        f"Error getting subscribers from group {group.id}: {str(e)}")

            # Połącz i usuń duplikaty
            all_recipients = list(direct_subscribers.union(group_subscribers))

            total_count = len(all_recipients)
            logger.info(
                f"Found {total_count} recipients for newsletter {newsletter.id}")

            # Ustaw całkowitą liczbę odbiorców
            newsletter.total_recipients = total_count
            newsletter.save(update_fields=['total_recipients'])
            logger.info(f"Updated total_recipients to {total_count}")

            # Sprawdź, czy w ogóle są jacyś odbiorcy
            if total_count == 0:
                logger.warning(
                    f"No recipients found for newsletter {newsletter.id}")
                newsletter.status = 'failed'
                newsletter.save(update_fields=['status'])
                return 0

            # Wyślij do każdego odbiorcy
            success_count = 0
            error_count = 0

            for index, subscriber in enumerate(all_recipients):
                logger.info(
                    f"Sending to {subscriber.email} ({index+1}/{total_count})")
                try:
                    self._send_newsletter_email(newsletter, subscriber)
                    success_count += 1
                    logger.info(f"Successfully sent to {subscriber.email}")

                    # Opcjonalnie: Zapisuj każdy sukces do bazy
                    # NewsletterTracking.objects.create(
                    #     newsletter=newsletter,
                    #     subscriber=subscriber,
                    #     action='sent',
                    #     timestamp=timezone.now()
                    # )

                except Exception as e:
                    error_count += 1
                    logger.error(
                        f"Error sending to {subscriber.email}: {str(e)}")

                    # Zapisz błąd do trackingu
                    try:
                        NewsletterTracking.objects.create(
                            newsletter=newsletter,
                            subscriber=subscriber,
                            action='error',
                            details=str(e)[:255]
                        )
                    except:
                        pass  # Ignoruj błędy zapisywania trackingu

            logger.info(
                f"Completed sending: {success_count} successful, {error_count} errors")

            # Aktualizuj status newslettera - BARDZO WAŻNE!
            try:
                # Pobierz świeżą instancję newslettera z bazy
                newsletter_fresh = Newsletter.objects.get(pk=newsletter.pk)

                if success_count > 0:
                    newsletter_fresh.status = 'sent'
                    newsletter_fresh.sent_date = timezone.now()
                    newsletter_fresh.save(
                        update_fields=['status', 'sent_date'])
                    logger.info(
                        f"Newsletter {newsletter.id} status updated to 'sent'")
                else:
                    newsletter_fresh.status = 'failed'
                    newsletter_fresh.save(update_fields=['status'])
                    logger.info(
                        f"Newsletter {newsletter.id} status updated to 'failed'")

            except Exception as e:
                logger.critical(
                    f"CRITICAL: Could not update newsletter status: {str(e)}")
                # Próbuj ponownie z pełnym zapisem
                try:
                    if success_count > 0:
                        newsletter.status = 'sent'
                        newsletter.sent_date = timezone.now()
                    else:
                        newsletter.status = 'failed'
                    newsletter.save()
                    logger.info(f"Newsletter status updated with full save")
                except Exception as e2:
                    logger.critical(
                        f"CRITICAL: Second attempt to update status failed: {str(e2)}")

            return success_count

        except Exception as e:
            logger.critical(f"Critical error in send_newsletter: {str(e)}")
            try:
                newsletter.status = 'failed'
                newsletter.save(update_fields=['status'])
            except:
                logger.critical(
                    "Could not update newsletter status to 'failed'")
            return 0

    def _send_newsletter_email(self, newsletter, subscriber):
        """Send the newsletter to a specific subscriber"""
        # Get the template
        template_html = self._get_template_html(newsletter)

        # Replace placeholders
        html_content = template_html.replace('{{content}}', newsletter.content)
        html_content = html_content.replace('{{subject}}', newsletter.subject)

        # Add subscriber-specific placeholders
        full_name = f"{subscriber.first_name or ''} {subscriber.last_name or ''}".strip()
        html_content = html_content.replace('{{recipient_name}}', full_name)
        html_content = html_content.replace(
            '{{recipient_email}}', subscriber.email)

        # Add unsubscribe link
        unsubscribe_url = f"{settings.SITE_URL}/unsubscribe/{subscriber.id}/"
        html_content = html_content.replace(
            '{{unsubscribe_url}}', unsubscribe_url)

        # Add tracking pixel if newsletter has tracking enabled
        if getattr(newsletter, 'add_tracking', True):
            tracking_id = str(uuid.uuid4())
            tracking_pixel = f'<img src="{settings.SITE_URL}/track/open/{tracking_id}/" style="width:1px;height:1px;display:none;" alt="" />'
            html_content = html_content.replace(
                '</body>', f'{tracking_pixel}</body>')

            # Create tracking record
            try:
                NewsletterTracking.objects.create(
                    newsletter=newsletter,
                    subscriber=subscriber,
                    action='sent',
                    tracking_id=tracking_id
                )
            except Exception as e:
                logger.warning(f"Could not create tracking record: {str(e)}")

            # Dodaj unikalne identyfikatory, jeśli opcja jest włączona
        if getattr(newsletter, 'use_uuid', True):
            message_id = str(uuid.uuid4())

            # Dodaj Message-ID do nagłówków wiadomości
            email_headers = {
                'Message-ID': f'<{message_id}@{settings.EMAIL_DOMAIN}>',
                'X-Entity-Ref-ID': message_id
            }
        else:
            email_headers = {}

        # Create the email
        email = EmailMultiAlternatives(
            subject=newsletter.subject,
            body="Please view this email with an HTML-compatible email client.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[subscriber.email]
        )

        # Add any attachments if newsletter has them
        if hasattr(newsletter, 'attachments') and newsletter.attachments.exists():
            for attachment in newsletter.attachments.all():
                email.attach(attachment.name, attachment.file.read(),
                             attachment.content_type)

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


# Newsletter Template views


def template_duplicate(request, pk):
    # Logika powielania szablonu
    original_template = get_object_or_404(Template, pk=pk)
    new_template = original_template
    new_template.pk = None  # Usunięcie klucza podstawowego, aby stworzyć kopię
    new_template.name = f"{original_template.name} (kopia)"
    new_template.save()

    messages.success(
        request, f"Utworzono kopię szablonu: {new_template.name}")
    return redirect('newsletter:template_list')


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
            # co najmniej 1, 35% open rate
            unique_opens = max(1, int(total_recipients * 0.35))
            # co najmniej 1, 20% więcej niż unique
            total_opens = max(1, int(unique_opens * 1.2))
            # co najmniej 1, 40% click-through rate
            unique_clicks = max(1, int(unique_opens * 0.4))
            # co najmniej 1, 30% więcej niż unique
            total_clicks = max(1, int(unique_clicks * 1.3))

        # Oblicz wskaźniki (unikaj dzielenia przez zero)
        open_rate = (unique_opens / total_recipients *
                     100) if total_recipients > 0 else 0
        click_rate = (unique_clicks / total_recipients *
                      100) if total_recipients > 0 else 0
        click_to_open_rate = (unique_clicks / unique_opens *
                              100) if unique_opens > 0 else 0

        # Oblicz średnią liczbę otwarć i kliknięć
        avg_opens_per_opener = total_opens / unique_opens if unique_opens > 0 else 0
        avg_clicks_per_clicker = total_clicks / \
            unique_clicks if unique_clicks > 0 else 0

        return {
            'total_recipients': total_recipients,
            'unique_opens': unique_opens,
            'total_opens': total_opens,
            'unique_clicks': unique_clicks,
            'total_clicks': total_clicks,
            'open_rate': open_rate,
            'click_rate': click_rate,
            'click_to_open_rate': click_to_open_rate,
            'avg_opens_per_opener': avg_opens_per_opener,
            'avg_clicks_per_clicker': avg_clicks_per_clicker
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


def reset_stuck_newsletters(request):
    """Reset newsletters stuck in 'sending' status"""
    if not request.user.is_staff:
        messages.error(request, _('Admin privileges required.'))
        return redirect('newsletter:newsletter_list')

    stuck_newsletters = Newsletter.objects.filter(status='sending')
    count = stuck_newsletters.count()

    # Ustaw status na 'failed' dla wszystkich zawieszonych newsletterów
    for newsletter in stuck_newsletters:
        newsletter.status = 'failed'
        newsletter.save(update_fields=['status'])

    messages.success(request, _(
        f'Reset {count} newsletters that were stuck in sending status.'))
    return redirect('newsletter:newsletter_list')
