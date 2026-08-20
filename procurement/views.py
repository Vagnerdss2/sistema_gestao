from django.db import transaction
from django.shortcuts import redirect

from core.views import AppDetailView, AppFormPageView, AppListView
from procurement.forms import PurchaseOrderForm, PurchaseOrderItemFormSet
from procurement.models import PurchaseOrder
from procurement.services import refresh_purchase_totals, sync_purchase_order_to_inventory


class PurchaseOrderListView(AppListView):
    model = PurchaseOrder
    queryset = PurchaseOrder.objects.select_related("branch", "supplier", "requester")
    page_title = "Compras"
    page_description = "Solicitacoes e ordens de compra com integracao ao estoque."
    create_url_name = "procurement:purchase-create"
    update_url_name = "procurement:purchase-update"
    detail_url_name = "procurement:purchase-detail"


class PurchaseOrderCreateView(AppFormPageView):
    template_name = "procurement/purchase_form.html"
    page_title = "Nova Compra"
    page_description = "Cadastre a ordem de compra e seus itens."
    cancel_url_name = "procurement:purchase-list"

    def get(self, request, *args, **kwargs):
        form = PurchaseOrderForm()
        formset = PurchaseOrderItemFormSet()
        return self.render_to_response(self.get_context_data(form=form, formset=formset))

    def post(self, request, *args, **kwargs):
        form = PurchaseOrderForm(request.POST, request.FILES)
        formset = PurchaseOrderItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                purchase_order = form.save()
                formset.instance = purchase_order
                formset.save()
                refresh_purchase_totals(purchase_order)
                sync_purchase_order_to_inventory(purchase_order)
            return redirect("procurement:purchase-list")
        return self.render_to_response(self.get_context_data(form=form, formset=formset))


class PurchaseOrderUpdateView(PurchaseOrderCreateView):
    page_title = "Editar Compra"
    page_description = "Atualize dados, itens e status da compra."

    def get(self, request, *args, **kwargs):
        purchase_order = PurchaseOrder.objects.get(pk=kwargs["pk"])
        form = PurchaseOrderForm(instance=purchase_order)
        formset = PurchaseOrderItemFormSet(instance=purchase_order)
        return self.render_to_response(
            self.get_context_data(form=form, formset=formset, purchase_order=purchase_order)
        )

    def post(self, request, *args, **kwargs):
        purchase_order = PurchaseOrder.objects.get(pk=kwargs["pk"])
        form = PurchaseOrderForm(request.POST, request.FILES, instance=purchase_order)
        formset = PurchaseOrderItemFormSet(request.POST, instance=purchase_order)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                purchase_order = form.save()
                formset.instance = purchase_order
                formset.save()
                refresh_purchase_totals(purchase_order)
                sync_purchase_order_to_inventory(purchase_order)
            return redirect("procurement:purchase-list")
        return self.render_to_response(
            self.get_context_data(form=form, formset=formset, purchase_order=purchase_order)
        )


class PurchaseOrderDetailView(AppDetailView):
    model = PurchaseOrder
    queryset = PurchaseOrder.objects.select_related("branch", "supplier", "requester").prefetch_related("items")
    page_title = "Detalhes da Compra"
    list_url_name = "procurement:purchase-list"
    template_name = "procurement/purchase_detail.html"
