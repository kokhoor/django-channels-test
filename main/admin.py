from django.contrib import admin

from . import models

# Register your models here.
@admin.register(models.Room)
class RoomAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('room', 'timestamp', 'handle', 'message')
    ordering = ('room', '-id',)
    search_fields = ('handle',)
    list_filter = ('room',)
