import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from kanban.forms import KanbanTaskForm
from kanban.models import KanbanTask, TaskStatus


class KanbanBoardView(LoginRequiredMixin, TemplateView):
    """
    Exibe o Quadro Kanban visual completo com colunas por status:
    - A Fazer (TODO)
    - Em Andamento (IN_PROGRESS)
    - Pendente / Aguardando (WAITING)
    - Concluído (DONE)
    
    Agrupa as tarefas otimizando consultas através de select_related nos relacionamentos.
    """
    template_name = "kanban/board.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = KanbanTask.objects.select_related(
            "assignee", "branch", "department", "linked_service_order", "linked_purchase_order"
        )
        context.update(
            {
                "page_title": "Quadro Kanban",
                "page_description": "Acompanhe tarefas por coluna e altere o status por arrastar e soltar.",
                "columns": [
                    {"key": TaskStatus.TODO, "label": "A Fazer"},
                    {"key": TaskStatus.IN_PROGRESS, "label": "Em Andamento"},
                    {"key": TaskStatus.WAITING, "label": "Pendente / Aguardando"},
                    {"key": TaskStatus.DONE, "label": "Concluido"},
                ],
                # Agrupa a lista de tarefas por cada coluna de status
                "tasks_by_status": {
                    status: list(tasks.filter(status=status).order_by("sort_order", "-created_at"))
                    for status, _label in TaskStatus.choices
                },
            }
        )
        return context


class KanbanTaskCreateView(LoginRequiredMixin, TemplateView):
    """Criação de um novo Card/Tarefa para o quadro Kanban."""
    template_name = "shared/object_form.html"
    page_title = "Nova Tarefa"
    page_description = "Crie um card para o quadro Kanban."

    def get(self, request, *args, **kwargs):
        return self.render_to_response(
            self.get_context_data(
                form=KanbanTaskForm(),
                page_title=self.page_title,
                page_description=self.page_description,
                submit_label="Salvar",
                cancel_url_name="kanban:board",
            )
        )

    def post(self, request, *args, **kwargs):
        form = KanbanTaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("kanban:board")
        return self.render_to_response(
            self.get_context_data(
                form=form,
                page_title=self.page_title,
                page_description=self.page_description,
                submit_label="Salvar",
                cancel_url_name="kanban:board",
            )
        )


class KanbanTaskUpdateView(KanbanTaskCreateView):
    """Edição das informações de uma Tarefa existente no Kanban."""
    page_title = "Editar Tarefa"
    page_description = "Atualize o card do Kanban."

    def get(self, request, *args, **kwargs):
        task = KanbanTask.objects.get(pk=kwargs["pk"])
        return self.render_to_response(
            self.get_context_data(
                form=KanbanTaskForm(instance=task),
                page_title=self.page_title,
                page_description=self.page_description,
                submit_label="Atualizar",
                cancel_url_name="kanban:board",
            )
        )

    def post(self, request, *args, **kwargs):
        task = KanbanTask.objects.get(pk=kwargs["pk"])
        form = KanbanTaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect("kanban:board")
        return self.render_to_response(
            self.get_context_data(
                form=form,
                page_title=self.page_title,
                page_description=self.page_description,
                submit_label="Atualizar",
                cancel_url_name="kanban:board",
            )
        )


class MoveKanbanTaskView(LoginRequiredMixin, View):
    """
    Endpoint JSON assíncrono acionado pelo recurso Drag-and-Drop (Arrastar e Soltar).
    
    Recebe o novo status e posição ordinal do card, atualizando o banco em tempo real.
    """

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode("utf-8"))
            status = payload["status"]
            sort_order = int(payload["sort_order"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return HttpResponseBadRequest("Payload invalido.")

        # Valida se o status recebido é um dos permitidos pela enumeração
        if status not in {choice for choice, _label in TaskStatus.choices}:
            return HttpResponseBadRequest("Status invalido.")

        task = KanbanTask.objects.get(pk=kwargs["pk"])
        task.status = status
        task.sort_order = sort_order
        task.save(update_fields=["status", "sort_order", "updated_at"])
        return JsonResponse({"ok": True})

