from django import template

register = template.Library()


@register.filter
def get_range(value):
    """
    Zwraca zakres liczb od 0 do podanej wartości.
    Używane do renderowania wcięć w strukturze drzewiastej.
    """
    return range(value)


@register.filter
def subtract_from(value, arg):
    """
    Odejmuje value od arg.
    Używane do wyliczania odpowiedniej wagi czcionki.
    """
    return max(1, arg - value)
