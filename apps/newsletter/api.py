from django.http import JsonResponse
from apps.subscriber.models import Subscriber, SubscriberGroup


def get_subscribers(request):
    """API endpoint to return all subscribers"""
    subscribers = Subscriber.objects.all().values(
        'id', 'email', 'first_name', 'last_name', 'newsletter_consent'
    )
    return JsonResponse(list(subscribers), safe=False)


def get_subscriber_groups(request):
    """API endpoint to return all subscriber groups"""
    groups = SubscriberGroup.objects.all().values(
        'id', 'group_name'
    )
    # Add subscriber count to each group
    groups_with_count = []
    for group in groups:
        subscriber_count = SubscriberGroup.objects.get(
            id=group['id']).subscriber.count()
        group['subscriber_count'] = subscriber_count
        groups_with_count.append(group)

    return JsonResponse(groups_with_count, safe=False)


def get_group_subscribers(request, group_id):
    """API endpoint to return subscribers in a specific group"""
    try:
        group = SubscriberGroup.objects.get(id=group_id)
        subscribers = group.subscriber.all().values(
            'id', 'email', 'first_name', 'last_name', 'newsletter_consent'
        )
        return JsonResponse(list(subscribers), safe=False)
    except SubscriberGroup.DoesNotExist:
        return JsonResponse({'error': 'Group not found'}, status=404)


def get_subscribers_count(request):
    """API endpoint to return the total subscriber count"""
    count = Subscriber.objects.filter(newsletter_consent=True).count()
    return JsonResponse({'count': count})


def get_recipients_count(request):
    """API endpoint to calculate recipient counts based on selections"""
    group_ids = request.GET.getlist('group_ids', [])
    subscriber_ids = request.GET.getlist('subscriber_ids', [])
    excluded_ids = request.GET.getlist('excluded_ids', [])

    # Convert to integers
    group_ids = [int(id) for id in group_ids if id.isdigit()]
    subscriber_ids = [int(id) for id in subscriber_ids if id.isdigit()]
    excluded_ids = [int(id) for id in excluded_ids if id.isdigit()]

    # Get subscribers from groups
    group_subscribers = set()
    for group_id in group_ids:
        try:
            group = SubscriberGroup.objects.get(id=group_id)
            group_subscribers.update(
                group.subscriber.filter(
                    newsletter_consent=True).values_list('id', flat=True)
            )
        except SubscriberGroup.DoesNotExist:
            pass

    # Get direct subscribers
    direct_subscribers = set(subscriber_ids)

    # Calculate total unique subscribers (excluding excluded ones)
    total_subscribers = (group_subscribers.union(
        direct_subscribers)) - set(excluded_ids)

    return JsonResponse({
        'direct_count': len(direct_subscribers),
        'group_count': len(group_subscribers - set(excluded_ids)),
        'total_unique': len(total_subscribers)
    })
