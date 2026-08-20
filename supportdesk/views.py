from django.db import transaction
from django.shortcuts import redirect

from core.views import AppDetailView, AppFormPageView, AppListView
from supportdesk.forms import ServiceOrderForm, ServiceOrderItemUsageFormSet
from supportdesk.models import ServiceOrder
from supportdesk.services import process_service_item_usages


class ServiceOrderListView(AppListView):
    model = ServiceOrder
    queryset = ServiceOrder.objects.select_related(
        "attended_user", "department", "branch", "technician"
    )
    page_title = "Servicos Executados"
    page_description = "Registro de atendimentos, manutencoes e consumos relacionados."
    create_url_name = "supportdesk:service-create"
    update_url_name = "supportdesk:service-update"
    detail_url_name = "supportdesk:service-detail"


class ServiceOrderCreateView(AppFormPageView):
    template_name = "supportdesk/service_form.html"
    page_title = "Nova Ordem de Servico"
    page_description = "Registre o atendimento e os itens envolvidos."
    cancel_url_name = "supportdesk:service-list"

    def get(self, request, *args, **kwargs):
        form = ServiceOrderForm()
        formset = ServiceOrderItemUsageFormSet()
        return self.render_to_response(self.get_context_data(form=form, formset=formset))

    def post(self, request, *args, **kwargs):
        form = ServiceOrderForm(request.POST)
        formset = ServiceOrderItemUsageFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                service_order = form.save()
                formset.instance = service_order
                formset.save()
                process_service_item_usages(service_order)
            return redirect("supportdesk:service-list")
        return self.render_to_response(self.get_context_data(form=form, formset=formset))


class ServiceOrderUpdateView(ServiceOrderCreateView):
    page_title = "Editar Ordem de Servico"
    page_description = "Atualize o atendimento e os itens vinculados."

    def get(self, request, *args, **kwargs):
        service_order = ServiceOrder.objects.get(pk=kwargs["pk"])
        form = ServiceOrderForm(instance=service_order)
        formset = ServiceOrderItemUsageFormSet(instance=service_order)
        return self.render_to_response(
            self.get_context_data(form=form, formset=formset, service_order=service_order)
        )

    def post(self, request, *args, **kwargs):
        service_order = ServiceOrder.objects.get(pk=kwargs["pk"])
        form = ServiceOrderForm(request.POST, instance=service_order)
        formset = ServiceOrderItemUsageFormSet(request.POST, instance=service_order)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                service_order = form.save()
                formset.instance = service_order
                formset.save()
                process_service_item_usages(service_order)
            return redirect("supportdesk:service-list")
        return self.render_to_response(
            self.get_context_data(form=form, formset=formset, service_order=service_order)
        )


class ServiceOrderDetailView(AppDetailView):
    model = ServiceOrder
    queryset = ServiceOrder.objects.select_related(
        "attended_user", "department", "branch", "technician"
    ).prefetch_related("item_usages__item")
    page_title = "Detalhes do Servico"
    list_url_name = "supportdesk:service-list"
    template_name = "supportdesk/service_detail.html"
