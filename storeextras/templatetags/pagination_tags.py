from django import template

register = template.Library()

@register.simple_tag
def pagination_query(request, page_number, page_key="page"):
    params = request.GET.copy()
    page_key = page_key or "page"
    params[page_key] = page_number
    return params.urlencode()
