from django import template
from django.utils.html import mark_safe

register = template.Library()


@register.filter(name='paginate_utils')
def paginate_utils(paginator, current_page, neighbors=10):
    #print('--> ', paginator)
    if paginator['num_pages'] > 2*neighbors:
        start_index = max(1, current_page-neighbors)
        end_index = min(paginator['num_pages'], current_page + neighbors)
        if end_index < start_index + 2*neighbors:
            end_index = start_index + 2*neighbors
        elif start_index > end_index - 2*neighbors:
            start_index = end_index - 2*neighbors
        if start_index < 1:
            end_index -= start_index
            start_index = 1
        elif end_index > paginator['num_pages']:
            start_index -= (end_index-paginator['num_pages'])
            end_index = paginator['num_pages']
        page_list = [f for f in range(start_index, end_index+1)]
        return page_list[:(2*neighbors + 1)]
    return paginator['get_page_range']

@register.filter(name='highlight_search')
def highlight_search(text, search):
    highlighted = text.replace(search, '<span class="highlight">{}</span>'.format(search))
    return mark_safe(highlighted)