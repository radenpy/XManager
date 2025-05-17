from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from apps.core.models import CoreModel
from apps.subscriber.models import Subscriber, SubscriberGroup
import uuid


class NewsletterTemplate(CoreModel):
    """
    Model for newsletter templates that can be reused
    """
    name = models.CharField(max_length=100, verbose_name="Template name")
    description = models.TextField(
        blank=True, null=True, verbose_name="Description")
    html_content = models.TextField(verbose_name="HTML content")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Szablon newslettera"
        verbose_name_plural = "Szablony newsletterów"
        ordering = ['-created_at']


class Newsletter(CoreModel):
    """
    Model for newsletters to be sent to subscribers
    """
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )

    subject = models.CharField(max_length=255, verbose_name="Subject")
    slug = models.SlugField(max_length=255, unique=True,
                            blank=True, verbose_name="Slug")
    content = models.TextField(verbose_name="Content")
    template = models.ForeignKey(
        NewsletterTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="newsletters",
        verbose_name="Template"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Status"
    )
    scheduled_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Scheduled date"
    )
    sent_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Sent date"
    )

    # Target subscribers and groups
    subscribers = models.ManyToManyField(
        Subscriber,
        blank=True,
        related_name="received_newsletters",
        verbose_name="Subscribers"
    )
    subscriber_groups = models.ManyToManyField(
        SubscriberGroup,
        blank=True,
        related_name="received_newsletters",
        verbose_name="Subscriber groups"
    )

    # Statistics
    total_recipients = models.IntegerField(
        default=0, verbose_name="Total recipients")
    open_count = models.IntegerField(default=0, verbose_name="Open count")
    click_count = models.IntegerField(default=0, verbose_name="Click count")

    # ID
    use_uuid = models.BooleanField(
        default=True, verbose_name='Dodaj unikalne identyfikatory')

    # Tracking
    tracking_id = models.UUIDField(
        default=uuid.uuid4, editable=False, verbose_name="Tracking ID")

    def __str__(self):
        return self.subject

    def save(self, *args, **kwargs):
        if not self.slug:
            # Generuj podstawowy slug z tytułu
            base_slug = slugify(self.subject)
            slug = base_slug
            counter = 1

            # Sprawdź czy slug jest unikalny, jeśli nie, dodaj licznik
            while Newsletter.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('newsletter:newsletter_detail', kwargs={'slug': self.slug})

    def get_preview_url(self):
        return reverse('newsletter:newsletter_preview', kwargs={'slug': self.slug})

    def get_recipient_count(self):
        """
        Calculate the total number of recipients (unique subscribers)
        """
        # Direct subscribers
        direct_subscribers = set(self.subscribers.values_list('id', flat=True))

        # Subscribers from groups
        group_subscribers = set()
        for group in self.subscriber_groups.all():
            group_subscribers.update(
                group.subscriber.values_list('id', flat=True))

        # Combine and get unique count
        all_recipients = direct_subscribers.union(group_subscribers)
        return len(all_recipients)

    def update_recipient_count(self):
        """
        Updates the total number of recipients based on groups and individual subscribers
        """
        count = 0

        # Count recipients from groups
        for group in self.subscriber_groups.all():
            count += group.subscriber.count()

        # Add individual recipients who aren't already in groups
        group_subscriber_ids = []
        for group in self.subscriber_groups.all():
            group_subscriber_ids.extend(
                group.subscriber.values_list('id', flat=True)
            )

        individual_subscribers = self.subscribers.exclude(
            id__in=group_subscriber_ids).count()
        count += individual_subscribers

        # Update field
        self.total_recipients = count
        self.save(update_fields=['total_recipients'])

        return count


class NewsletterTracking(CoreModel):
    """
    Model for tracking newsletter events (opens, clicks)
    """
    EVENT_TYPES = (
        ('open', 'Open'),
        ('click', 'Click'),
    )

    newsletter = models.ForeignKey(
        Newsletter,
        on_delete=models.CASCADE,
        related_name="tracking_events",
        verbose_name="Newsletter"
    )
    subscriber = models.ForeignKey(
        Subscriber,
        on_delete=models.CASCADE,
        related_name="newsletter_events",
        verbose_name="Subscriber"
    )
    event_type = models.CharField(
        max_length=10,
        choices=EVENT_TYPES,
        verbose_name="Event type"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP address"
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name="User agent"
    )
    link_url = models.URLField(
        null=True,
        blank=True,
        verbose_name="Link URL"
    )

    # Dodaj to pole
    tracking_id = models.UUIDField(
        null=True, blank=True, verbose_name="Tracking ID")

    # Możesz też dodać pole action jako alias dla event_type lub jako oddzielne pole
    action = models.CharField(max_length=50, null=True,
                              blank=True, verbose_name="Action")

    def __str__(self):
        return f"{self.get_event_type_display()} by {self.subscriber.email} - {self.newsletter.subject}"

    class Meta:
        verbose_name = "Tracking newslettera"
        verbose_name_plural = "Tracking newsletterów"
        ordering = ['-created_at']
