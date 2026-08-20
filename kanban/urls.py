"""
Rotas de URL do aplicativo Kanban (Quadro de Tarefas de TI).

- /kanban/ : Quadro visual com colunas e cards
- /kanban/nova/ : Criação de nova tarefa
- /kanban/<pk>/editar/ : Edição de tarefa existente
- /kanban/<pk>/move/ : Endpoint JSON de movimentação via Drag-and-Drop
"""

from django.urls import path

from kanban import views

app_name = "kanban"

urlpatterns = [
    path("", views.KanbanBoardView.as_view(), name="board"),
    path("nova/", views.KanbanTaskCreateView.as_view(), name="task-create"),
    path("<int:pk>/editar/", views.KanbanTaskUpdateView.as_view(), name="task-update"),
    path("<int:pk>/move/", views.MoveKanbanTaskView.as_view(), name="task-move"),
]

