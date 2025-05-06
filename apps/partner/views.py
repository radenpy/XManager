from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Partner, PartnerEmail
from .forms import PartnerForm, PartnerEmailForm
from django_countries import countries


class PartnerListView(LoginRequiredMixin, ListView):
    """Lista partnerów"""
    model = Partner
    template_name = 'partner/partner_list.html'
    context_object_name = 'partners'
    paginate_by = 10
    ordering = ['name']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Pobierz wszystkie kraje
        all_countries = list(countries)

        # Przygotuj posortowaną listę krajów
        # 1. Polska na początku
        # 2. Najczęściej wybierane kraje EU posortowane alfabetycznie
        # 3. Pozostałe kraje posortowane alfabetycznie

        # Usuń Polskę z listy krajów
        poland = None
        for code, name in all_countries:
            if code == 'PL':
                poland = (code, name)
                break

        if poland:
            all_countries.remove(poland)

        # Najczęściej wybierane kraje UE
        frequently_used = [
            'DE', 'GB', 'FR', 'ES', 'IT', 'NL', 'BE', 'AT', 'CZ', 'SK', 'LT', 'LV', 'EE'
        ]

        freq_countries = []
        remaining_countries = []

        # Podziel kraje na "często używane" i "pozostałe"
        for code, name in all_countries:
            if code in frequently_used:
                freq_countries.append((code, name))
            else:
                remaining_countries.append((code, name))

        # Sortuj alfabetycznie
        freq_countries.sort(key=lambda x: x[1])  # Sortuj po nazwie kraju
        remaining_countries.sort(key=lambda x: x[1])  # Sortuj po nazwie kraju

        # Złóż listę z powrotem, zaczynając od Polski
        sorted_countries = []
        if poland:
            sorted_countries.append(poland)
        sorted_countries.extend(freq_countries)
        sorted_countries.extend(remaining_countries)

        context['countries'] = sorted_countries
        return context


class PartnerUpdateView(LoginRequiredMixin, UpdateView):
    """Edycja partnera"""
    model = Partner
    form_class = PartnerForm
    template_name = 'partner/partner_update.html'

    def get_success_url(self):
        return reverse('partner_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Dodaj listę krajów do kontekstu
        context['countries'] = list(countries)

        return context


class PartnerDeleteView(LoginRequiredMixin, DeleteView):
    """Usunięcie partnera"""
    model = Partner
    template_name = 'partner_confirm_delete.html'
    success_url = reverse_lazy('partner_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Partner został usunięty."))
        return super().delete(request, *args, **kwargs)
