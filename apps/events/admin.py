from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "source", "published", "created_at")
    search_fields = ("type", "source")
    list_filter = ("published",)
    readonly_fields = ("created_at",)
