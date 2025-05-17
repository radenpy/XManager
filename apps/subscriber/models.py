from django.db import models
from django.urls import reverse
from apps.core.models import CoreModel
# Create your models here.


class Subscriber(CoreModel):
    email = models.EmailField(unique=True, verbose_name='E-mail')
    # relacja do partner. Mozna wybrać powiązanie z Partnerem. a jeśli partner nie istnieje w bazie to mozna wpisac ręcznie
    # jeśli partner istnieje, to i tak mozna wpisac recznie, ale powiazanie z partnerem zostaje zachowane.
    first_name = models.CharField(
        max_length=100, blank=True, verbose_name='First name')
    last_name = models.CharField(
        max_length=100, blank=True, verbose_name='Last name')
    common_name = models.CharField(
        max_length=100, blank=True, verbose_name='Common name')
    newsletter_consent = models.BooleanField(
        default=True, verbose_name='Email consent')
    group_affiliation = models.ManyToManyField(
        'SubscriberGroup', related_name='subscriber', blank=True, verbose_name='Group affiliation')

    def __str__(self):
        return f"{self.id} {self.email} {self.first_name} {self.last_name} {self.newsletter_consent}"

    def get_absolute_url(self):
        return reverse('subscriber_detail', kwargs={'pk': self.pk})

    class Meta:
        ordering = ['email']
        verbose_name = ('Subskrybent')
        verbose_name_plural = ('Subskrybenci')


class SubscriberGroup(CoreModel):
    group_name = models.CharField(max_length=100, verbose_name='Group name')

    def __str__(self):
        return self.group_name

    class Meta:
        verbose_name = ('Grupa subskrybenta')
        verbose_name_plural = ('Grupy subskrybentów')
