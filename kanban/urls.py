from django.urls import path

from kanban import views

app_name = "kanban"

urlpatterns = [
    path("", views.KanbanBoardView.as_view(), name="board"),
    path("nova/", views.KanbanTaskCreateView.as_view(), name="task-create"),
    path("<int:pk>/editar/", views.KanbanTaskUpdateView.as_view(), name="task-update"),
    path("<int:pk>/move/", views.MoveKanbanTaskView.as_view(), name="task-move"),
]
