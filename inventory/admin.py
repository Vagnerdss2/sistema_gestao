from django.contrib import admin

from inventory.models import InventoryItem, StockMovement


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "branch", "status", "quantity", "minimum_quantity")
    list_filter = ("status", "branch", "category")
    search_fields = ("name", "serial_number", "asset_tag", "model", "brand")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("item", "movement_type", "quantity", "reference", "created_at")
    list_filter = ("movement_type", "created_at")
    search_fields = ("item__name", "reference")
