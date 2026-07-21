from django.contrib import admin

from supportdesk.models import ServiceOrder, ServiceOrderItemUsage


class ServiceOrderItemUsageInline(admin.TabularInline):
    model = ServiceOrderItemUsage
    extra = 0


@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = ("title", "attended_user", "department", "branch", "technician", "service_datetime")
    list_filter = ("branch", "department", "status")
    search_fields = ("title", "short_description", "attended_user__full_name", "technician__full_name")
    inlines = [ServiceOrderItemUsageInline]
