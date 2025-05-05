from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.http import JsonResponse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError

from .models import Subscriber, SubscriberGroup
from apps.subscriber.forms import SubscriberForm


class SubscriberListView(LoginRequiredMixin, ListView):
    """Lista subskrybentów"""
    model = Subscriber
    template_name = 'subscribers/subscriber_list.html'
    context_object_name = 'subscribers'
    paginate_by = 20

    def get_queryset(self):
        """Filtrowanie wyników"""
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')

        if search_query:
            queryset = queryset.filter(
                email__icontains=search_query
            ) | queryset.filter(
                first_name__icontains=search_query
            ) | queryset.filter(
                last_name__icontains=search_query
            )

        return queryset

    def get_context_data(self, **kwargs):
        """Dodatkowe dane kontekstowe"""
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class SubscriberDetailView(LoginRequiredMixin, DetailView):
    """Szczegóły subskrybenta"""
    model = Subscriber
    template_name = 'subscribers/subscriber_detail.html'
    context_object_name = 'subscriber'

    def get_context_data(self, **kwargs):
        """Dodatkowe dane kontekstowe"""
        context = super().get_context_data(**kwargs)
        context['partners'] = self.object.partnered_with.all()
        return context


class SubscriberCreateView(LoginRequiredMixin, CreateView):
    """Tworzenie nowego subskrybenta"""
    model = Subscriber
    form_class = SubscriberForm
    template_name = 'subscribers/subscriber_form.html'

    def get_success_url(self):
        return reverse('subscribers:subscriber_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, _(
            "Subskrybent został dodany pomyślnie."))
        return super().form_valid(form)


class SubscriberUpdateView(LoginRequiredMixin, UpdateView):
    """Edycja subskrybenta"""
    model = Subscriber
    form_class = SubscriberForm
    template_name = 'subscribers/subscriber_form.html'

    def get_success_url(self):
        return reverse('subscribers:subscriber_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, _("Subskrybent został zaktualizowany."))
        return super().form_valid(form)


class SubscriberDeleteView(LoginRequiredMixin, DeleteView):
    """Usunięcie subskrybenta"""
    model = Subscriber
    template_name = 'subscribers/subscriber_confirm_delete.html'
    success_url = reverse_lazy('subscribers:subscriber_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Subskrybent został usunięty."))
        return super().delete(request, *args, **kwargs)


class SubscriberLookupAPIView(LoginRequiredMixin, View):
    """
    API do wyszukiwania subskrybentów po adresie email (AJAX)
    """

    def get(self, request, *args, **kwargs):
        search = request.GET.get('search', '')
        page = int(request.GET.get('page', 1))
        limit = 10

        # Wyszukaj subskrybentów
        if search:
            subscribers = Subscriber.objects.filter(email__icontains=search)
        else:
            subscribers = Subscriber.objects.all()

        # Paginacja
        start = (page - 1) * limit
        end = page * limit

        # Przygotuj dane
        total = subscribers.count()
        results = []

        for subscriber in subscribers[start:end]:
            results.append({
                'id': subscriber.id,
                'email': subscriber.email,
                'first_name': subscriber.first_name,
                'last_name': subscriber.last_name
            })

        return JsonResponse({
            'results': results,
            'has_more': total > end
        })
