from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import Newsletter, NewsletterTemplate
from apps.subscriber.models import Subscriber, SubscriberGroup


class NewsletterTemplateForm(forms.ModelForm):
    """
    Form for creating and editing newsletter templates
    """
    class Meta:
        model = NewsletterTemplate
        fields = ['name', 'description', 'html_content']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'html_content': forms.Textarea(attrs={'class': 'form-control html-editor', 'rows': 15}),
        }

    def clean_html_content(self):
        """
        Validate HTML content
        """
        html_content = self.cleaned_data.get('html_content')

        # Check if required placeholders are present
        required_placeholders = ['{{content}}']
        for placeholder in required_placeholders:
            if placeholder not in html_content:
                raise forms.ValidationError(
                    _("Template must contain the required placeholder: %(placeholder)s"),
                    params={'placeholder': placeholder}
                )

        # You can add more validation here

        return html_content


class NewsletterForm(forms.ModelForm):
    """
    Form for creating and editing newsletters
    """
    send_now = forms.BooleanField(
        required=False,
        label=_("Send immediately"),
        help_text=_(
            "If checked, the newsletter will be sent immediately after saving.")
    )

    all_subscribers = forms.BooleanField(
        required=False,
        label=_("Send to all subscribers"),
        help_text=_(
            "If checked, the newsletter will be sent to all subscribers.")
    )

    schedule_send = forms.BooleanField(
        required=False,
        label=_("Schedule sending"),
        help_text=_(
            "If checked, the newsletter will be scheduled for sending at the specified date and time.")
    )

    class Meta:
        model = Newsletter
        fields = [
            'subject', 'content', 'template',
            'subscribers', 'subscriber_groups',
            'scheduled_date', 'status'
        ]
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control content-editor', 'rows': 10}),
            'template': forms.Select(attrs={'class': 'form-control select2'}),
            'subscribers': forms.SelectMultiple(attrs={'class': 'form-control select2-multiple'}),
            'subscriber_groups': forms.SelectMultiple(attrs={'class': 'form-control select2-multiple'}),
            'scheduled_date': forms.DateTimeInput(attrs={
                'class': 'form-control datetimepicker',
                'type': 'datetime-local'
            }),
            'status': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make certain fields not required
        self.fields['subscribers'].required = False
        self.fields['subscriber_groups'].required = False
        self.fields['scheduled_date'].required = False

        # Set queryset for subscribers and groups
        self.fields['subscribers'].queryset = Subscriber.objects.filter(
            newsletter_consent=True
        ).order_by('email')

        self.fields['subscriber_groups'].queryset = SubscriberGroup.objects.all(
        ).order_by('group_name')

        # Add helpful text
        self.fields['template'].help_text = _(
            "Select a template for the newsletter. If none is selected, a default template will be used.")

        # Add placeholders
        self.fields['subject'].widget.attrs.update(
            {'placeholder': _('Enter newsletter subject')})
        self.fields['content'].widget.attrs.update(
            {'placeholder': _('Enter newsletter content')})

        # Only show scheduled_date if status is 'scheduled'
        if self.instance.status != 'scheduled':
            self.fields['scheduled_date'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        send_now = cleaned_data.get('send_now')
        all_subscribers = cleaned_data.get('all_subscribers')
        schedule_send = cleaned_data.get('schedule_send')
        scheduled_date = cleaned_data.get('scheduled_date')
        subscribers = cleaned_data.get('subscribers')
        subscriber_groups = cleaned_data.get('subscriber_groups')

        # Handle scheduling
        if schedule_send:
            if not scheduled_date:
                self.add_error('scheduled_date', _(
                    "Scheduled date is required when scheduling a newsletter."))
            elif scheduled_date <= timezone.now():
                self.add_error('scheduled_date', _(
                    "Scheduled date must be in the future."))
            cleaned_data['status'] = 'scheduled'

        # Handle immediate sending
        if send_now:
            cleaned_data['status'] = 'sending'

        # Check that recipients are selected
        if not all_subscribers and not subscribers and not subscriber_groups:
            self.add_error(None, _(
                "You must select at least one recipient or group, or choose to send to all subscribers."))

        return cleaned_data


class NewsletterSendTestForm(forms.Form):
    """
    Form for sending test newsletters
    """
    email = forms.EmailField(
        label=_("Test email address"),
        help_text=_("Enter an email address to send a test newsletter to."),
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )


class NewsletterFilterForm(forms.Form):
    """
    Form for filtering newsletters in the list view
    """
    STATUS_CHOICES = (
        ('', _('All statuses')),
    ) + Newsletter.STATUS_CHOICES

    subject = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': _('Search by subject')})
    )

    status = forms.ChoiceField(
        required=False,
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date',
            'placeholder': _('From date')
        })
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control datepicker',
            'type': 'date',
            'placeholder': _('To date')
        })
    )
