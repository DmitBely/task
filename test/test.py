from django.db import models
from django import template
from django.core.cache import cache
from django.urls import reverse

from myapp.models import MenuItem

class MenuItem(models.Model):
    title = models.CharField(max_length=50)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
    url = models.CharField(max_length=200)
    is_active = models.BooleanField(default=False)
    menu_name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.title

register = template.Library()

@register.simple_tag(takes_context=True)
def draw_menu(context, menu_name, level=0):
    cache_key = f"menu_{menu_name}_{level}"
    menu = cache.get(cache_key)
    if not menu:
        menu = MenuItem.objects.filter(menu_name=menu_name, parent__isnull=True)
        cache.set(cache_key, menu)
    request = context['request']
    current_path = request.path_info.lstrip('/')
    menu_items = []
    for item in menu:
        menu_items.append(render_menu_item(item, current_path, level))
    return menu_items

def render_menu_item(item, current_path, level):
    active = False
    if current_path == item.url:
        active = True
    elif item.children.exists():
        for child in item.children.all():
            if current_path.startswith(child.url):
                active = True
                break
    url = item.url
    if not url.startswith('/') and not url.startswith('http'):
        url = reverse(url)
    return {
        'title': item.title,
        'url': url,
        'active': active,
        'children': [render_menu_item(child, current_path, level + 1) for child in item.children.all()] if level >= 0 else []
    }
