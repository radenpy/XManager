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
        verbose_name = "Newsletter template"
        verbose_name_plural = "Newsletter templates"
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

    # Tracking
    tracking_id = models.UUIDField(
        default=uuid.uuid4, editable=False, verbose_name="Tracking ID")

    def __str__(self):
        return self.subject

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.subject)
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
    Aktualizuje liczbę odbiorców na podstawie grup i indywidualnych subskrybentów
    """
    count = 0

    # Zlicz odbiorców z grup (jeśli model ma taką relację)
    if hasattr(self, 'recipient_groups'):
        for group in self.recipient_groups.all():
            count += group.subscriber.count()

    # Dodaj indywidualnych odbiorców (jeśli model ma taką relację)
    if hasattr(self, 'subscribers'):
        # Pobierz wszystkie identyfikatory subskrybentów z grup
        group_subscriber_ids = []
        if hasattr(self, 'recipient_groups'):
            for group in self.recipient_groups.all():
                group_subscriber_ids.extend(
                    group.subscriber.values_list('id', flat=True)
                )

        # Policz indywidualnych subskrybentów, którzy nie są w grupach
        individual_subscribers = self.subscribers.exclude(
            id__in=group_subscriber_ids).count()
        count += individual_subscribers

    # Aktualizuj pole
    self.total_recipients = count
    self.save(update_fields=['total_recipients'])

    return count

    class Meta:
        verbose_name = "Newsletter"
        verbose_name_plural = "Newsletters"
        ordering = ['-created_at']


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

    def __str__(self):
        return f"{self.get_event_type_display()} by {self.subscriber.email} - {self.newsletter.subject}"

    class Meta:
        verbose_name = "Newsletter tracking"
        verbose_name_plural = "Newsletter tracking"
        ordering = ['-created_at']
