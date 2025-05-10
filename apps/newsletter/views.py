from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template import Template, Context
from django.conf import settings

from .models import Newsletter, NewsletterTemplate, NewsletterTracking
from .forms import NewsletterForm, NewsletterTemplateForm, NewsletterSendTestForm, NewsletterFilterForm
from apps.subscriber.models import Subscriber, SubscriberGroup

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


class NewsletterDetailView(LoginRequiredMixin, DetailView):
    """
    View for displaying newsletter details
    """
    model = Newsletter
    template_name = 'newsletter/newsletter_detail.html'
    context_object_name = 'newsletter'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add test form
        context['test_form'] = NewsletterSendTestForm()

        # Calculate recipient stats
        newsletter = self.get_object()

        # Direct subscribers
        direct_subscribers_count = newsletter.subscribers.count()

        # Group subscribers (with potential duplicates)
        group_subscribers = set()
        for group in newsletter.subscriber_groups.all():
            group_subscribers.update(
                group.subscriber.values_list('id', flat=True))

        # Total unique recipients
        all_recipients = set(
            newsletter.subscribers.values_list('id', flat=True))
        all_recipients.update(group_subscribers)
        total_unique = len(all_recipients)

        # Add stats to context
        context['stats'] = {
            'direct_subscribers': direct_subscribers_count,
            'group_subscribers': len(group_subscribers),
            'total_unique': total_unique,
            'open_rate': (newsletter.open_count / total_unique * 100) if total_unique > 0 else 0,
            'click_rate': (newsletter.click_count / total_unique * 100) if total_unique > 0 else 0,
        }

        return context


class NewsletterCreateView(LoginRequiredMixin, CreateView):
    """
    View for creating newsletters
    """
    model = Newsletter
    form_class = NewsletterForm
    template_name = 'newsletter/newsletter_create.html'
    success_url = reverse_lazy('newsletter:newsletter_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['templates'] = NewsletterTemplate.objects.all()
        return context

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

        # Check if save_and_preview button was clicked (NEW CODE)
        if 'save_and_preview' in self.request.POST:
            messages.success(self.request, _(
                'Newsletter saved. Here is the preview.'))
            return redirect('newsletter:newsletter_preview', slug=newsletter.slug)

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


class NewsletterUpdateView(LoginRequiredMixin, UpdateView):
    """
    View for updating newsletters
    """
    model = Newsletter
    form_class = NewsletterForm
    template_name = 'newsletter/newsletter_update.html'

    def get_success_url(self):
        return reverse('newsletter:newsletter_detail', kwargs={'slug': self.object.slug})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['templates'] = NewsletterTemplate.objects.all()
        return context

    def form_valid(self, form):
        """Process the form data after validation"""
        # Set the updated_by field
        form.instance.updated_by = self.request.user

        # Get the newsletter object
        newsletter = form.save(commit=False)

        # Handle 'send to all subscribers' option
        if form.cleaned_data.get('all_subscribers'):
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

        # Update the recipient count
        newsletter.update_recipient_count()

        # Process sending if needed
        if send_now:
            # In a real application, this would use Celery or another task queue
            # Here we'll just simulate it with a simple flag
            # send_newsletter.delay(newsletter.id)  # This would be a Celery task
            messages.success(self.request, _('Newsletter queued for sending.'))

        messages.success(self.request, _('Newsletter updated successfully.'))
        return redirect(self.get_success_url())


class NewsletterDeleteView(LoginRequiredMixin, DeleteView):
    """
    View for deleting newsletters
    """
    model = Newsletter
    template_name = 'newsletter/newsletter_delete_confirm.html'
    success_url = reverse_lazy('newsletter:newsletter_list')

    def delete(self, request, *args, **kwargs):
        """Delete the newsletter and show a success message"""
        newsletter = self.get_object()

        # Check if newsletter has been sent
        if newsletter.status in ['sent', 'sending']:
            messages.error(request, _(
                'Cannot delete a newsletter that has been sent or is being sent.'))
            return redirect('newsletter:newsletter_detail', slug=newsletter.slug)

        # Delete the newsletter
        newsletter.delete()

        messages.success(request, _('Newsletter deleted successfully.'))
        return redirect(self.success_url)


class NewsletterPreviewView(LoginRequiredMixin, DetailView):
    """
    View for previewing newsletters with confirmation options
    """
    model = Newsletter
    template_name = 'newsletter/newsletter_preview_confirm.html'
    context_object_name = 'newsletter'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        newsletter = self.get_object()

        # Calculate recipient stats
        direct_subscribers_count = newsletter.subscribers.count()

        # Group subscribers (with potential duplicates)
        group_subscribers = set()
        for group in newsletter.subscriber_groups.all():
            group_subscribers.update(
                group.subscriber.values_list('id', flat=True))

        # Total unique recipients
        all_recipients = set(
            newsletter.subscribers.values_list('id', flat=True))
        all_recipients.update(group_subscribers)
        total_unique = len(all_recipients)

        # Add stats to context
        context['stats'] = {
            'direct_subscribers': direct_subscribers_count,
            'group_subscribers': len(group_subscribers),
            'total_unique': total_unique,
        }

        # Get the HTML content - Fix the syntax here
        template_html = self._get_template_html(newsletter)
        html_content = template_html.replace('{{content}}', newsletter.content)
        html_content = html_content.replace('{{subject}}', newsletter.subject)
        context['newsletter_content'] = html_content

        return context

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
                    .preview-notice { background: #e74c3c; color: white; padding: 10px; text-align: center; }
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

        return redirect('newsletter:newsletter_detail', slug=newsletter.slug)

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
            return redirect('newsletter:newsletter_detail', slug=newsletter.slug)

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
        return redirect('newsletter:newsletter_detail', slug=newsletter.slug)


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
