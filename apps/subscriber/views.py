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


class SubscriberCreateView(LoginRequiredMixin, View):
    """API do tworzenia nowego subskrybenta (AJAX)"""

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        newsletter_consent = request.POST.get('newsletter_consent') == 'on'
        group_ids = request.POST.getlist('group_affiliation', [])

        if not email:
            return JsonResponse({
                'success': False,
                'message': "Email jest wymagany."
            })

        # Sprawdź czy subskrybent o takim emailu już istnieje
        if Subscriber.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'message': "Subskrybent o takim adresie email już istnieje."
            })

        # Stwórz nowego subskrybenta
        try:
            subscriber = Subscriber(
                email=email,
                first_name=first_name,
                last_name=last_name,
                newsletter_consent=newsletter_consent
            )
            subscriber.save()

            # Przypisz grupy
            if group_ids:
                groups = SubscriberGroup.objects.filter(id__in=group_ids)
                subscriber.group_affiliation.add(*groups)

            return JsonResponse({
                'success': True,
                'message': "Subskrybent został dodany pomyślnie.",
                'subscriber_id': subscriber.id,
                'subscriber_email': subscriber.email
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Wystąpił błąd: {str(e)}"
            })


class SubscriberUpdateView(LoginRequiredMixin, View):
    """API do aktualizacji subskrybenta (AJAX)"""

    def post(self, request, pk, *args, **kwargs):
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        newsletter_consent = request.POST.get('newsletter_consent') == 'on'
        group_ids = request.POST.getlist('group_affiliation', [])

        if not email:
            return JsonResponse({
                'success': False,
                'message': "Email jest wymagany."
            })

        # Sprawdź czy subskrybent istnieje
        try:
            subscriber = Subscriber.objects.get(id=pk)
        except Subscriber.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': "Subskrybent nie istnieje."
            })

        # Sprawdź czy email nie jest już zajęty przez innego subskrybenta
        if Subscriber.objects.filter(email=email).exclude(id=pk).exists():
            return JsonResponse({
                'success': False,
                'message': "Subskrybent o takim adresie email już istnieje."
            })

        # Aktualizuj subskrybenta
        try:
            subscriber.email = email
            subscriber.first_name = first_name
            subscriber.last_name = last_name
            subscriber.newsletter_consent = newsletter_consent
            subscriber.save()

            # Zaktualizuj grupy
            subscriber.group_affiliation.clear()
            if group_ids:
                groups = SubscriberGroup.objects.filter(id__in=group_ids)
                subscriber.group_affiliation.add(*groups)

            return JsonResponse({
                'success': True,
                'message': "Subskrybent został zaktualizowany pomyślnie."
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Wystąpił błąd: {str(e)}"
            })


class SubscriberDeleteView(LoginRequiredMixin, View):
    """API do usuwania subskrybenta (AJAX)"""

    def post(self, request, pk, *args, **kwargs):
        try:
            subscriber = Subscriber.objects.get(id=pk)
            email = subscriber.email
            subscriber.delete()

            return JsonResponse({
                'success': True,
                'message': f"Subskrybent '{email}' został usunięty pomyślnie."
            })
        except Subscriber.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': "Subskrybent nie istnieje."
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Wystąpił błąd: {str(e)}"
            })


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


class SubscriberGroupListView(LoginRequiredMixin, ListView):
    """Lista grup subskrybentów"""
    model = SubscriberGroup
    template_name = 'subscriber/group_list.html'
    context_object_name = 'groups'
    paginate_by = 20

    def get_queryset(self):
        """Filtrowanie wyników"""
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')

        if search_query:
            queryset = queryset.filter(group_name__icontains=search_query)

        return queryset

    def get_context_data(self, **kwargs):
        """Dodatkowe dane kontekstowe"""
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class SubscriberGroupCreateView(LoginRequiredMixin, View):
    """API do tworzenia nowej grupy subskrybentów (AJAX)"""

    def post(self, request, *args, **kwargs):
        group_name = request.POST.get('group_name')

        if not group_name:
            return JsonResponse({
                'success': False,
                'message': "Nazwa grupy jest wymagana."
            })

        # Sprawdź czy grupa o takiej nazwie już istnieje
        if SubscriberGroup.objects.filter(group_name=group_name).exists():
            return JsonResponse({
                'success': False,
                'message': "Grupa o takiej nazwie już istnieje."
            })

        # Stwórz nową grupę
        try:
            group = SubscriberGroup(group_name=group_name)
            group.save()

            return JsonResponse({
                'success': True,
                'message': "Grupa została dodana pomyślnie.",
                'group_id': group.id,
                'group_name': group.group_name
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Wystąpił błąd: {str(e)}"
            })


class SubscriberGroupUpdateView(LoginRequiredMixin, View):
    """API do aktualizacji grupy subskrybentów (AJAX)"""

    def post(self, request, *args, **kwargs):
        group_id = request.POST.get('group_id')
        group_name = request.POST.get('group_name')

        if not group_id or not group_name:
            return JsonResponse({
                'success': False,
                'message': "ID i nazwa grupy są wymagane."
            })

        # Sprawdź czy grupa istnieje
        try:
            group = SubscriberGroup.objects.get(id=group_id)
        except SubscriberGroup.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': "Grupa nie istnieje."
            })

        # Sprawdź czy nazwa nie jest już zajęta przez inną grupę
        if SubscriberGroup.objects.filter(group_name=group_name).exclude(id=group_id).exists():
            return JsonResponse({
                'success': False,
                'message': "Grupa o takiej nazwie już istnieje."
            })

        # Aktualizuj grupę
        try:
            group.group_name = group_name
            group.save()

            return JsonResponse({
                'success': True,
                'message': "Grupa została zaktualizowana pomyślnie."
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Wystąpił błąd: {str(e)}"
            })


class SubscriberGroupDeleteView(LoginRequiredMixin, View):
    """API do usuwania grupy subskrybentów (AJAX)"""

    def post(self, request, pk, *args, **kwargs):
        try:
            group = SubscriberGroup.objects.get(id=pk)
            group_name = group.group_name
            group.delete()

            return JsonResponse({
                'success': True,
                'message': f"Grupa '{group_name}' została usunięta pomyślnie."
            })
        except SubscriberGroup.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': "Grupa nie istnieje."
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Wystąpił błąd: {str(e)}"
            })


class SubscriberBulkGroupAssignView(LoginRequiredMixin, View):
    """API do hurtowego przypisywania subskrybentów do grup (AJAX)"""

    def post(self, request, *args, **kwargs):
        subscriber_ids = request.POST.getlist('subscriber_ids')
        group_ids = request.POST.getlist('group_ids')
        action = request.POST.get('action', 'add')  # 'add' lub 'remove'

        if not subscriber_ids or not group_ids:
            return JsonResponse({
                'success': False,
                'message': "Wymagane są zarówno ID subskrybentów jak i ID grup."
            })

        try:
            subscribers = Subscriber.objects.filter(id__in=subscriber_ids)
            groups = SubscriberGroup.objects.filter(id__in=group_ids)

            if not subscribers.exists() or not groups.exists():
                return JsonResponse({
                    'success': False,
                    'message': "Nie znaleziono wybranych subskrybentów lub grup."
                })

            # Operacja przypisania lub usunięcia
            for subscriber in subscribers:
                if action == 'add':
                    subscriber.group_affiliation.add(*groups)
                else:
                    subscriber.group_affiliation.remove(*groups)

            action_text = "przypisani do" if action == 'add' else "usunięci z"
            return JsonResponse({
                'success': True,
                'message': f"Subskrybenci zostali {action_text} wybranych grup pomyślnie."
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Wystąpił błąd: {str(e)}"
            })
