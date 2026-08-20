from django.contrib import admin

from kanban.models import KanbanTask


@admin.register(KanbanTask)
class KanbanTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "priority", "assignee", "due_date")
    list_filter = ("status", "priority", "branch", "department")
    search_fields = ("title", "description", "assignee__full_name")
