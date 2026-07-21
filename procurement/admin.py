from django.contrib import admin

from procurement.models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("title", "branch", "supplier", "purchase_date", "status", "inventory_processed")
    list_filter = ("status", "branch", "purchase_date")
    search_fields = ("title", "supplier__legal_name")
    inlines = [PurchaseOrderItemInline]
