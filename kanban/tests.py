import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from kanban.models import KanbanTask, TaskStatus


class KanbanMoveViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="admin", password="secret123")
        self.task = KanbanTask.objects.create(
            title="Atualizar roteador",
            description="Aplicar nova configuracao.",
            status=TaskStatus.TODO,
            sort_order=0,
        )

    def test_move_endpoint_updates_task_status_and_sort_order(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("kanban:task-move", kwargs={"pk": self.task.pk}),
            data=json.dumps({"status": TaskStatus.IN_PROGRESS, "sort_order": 3}),
            content_type="application/json",
        )

        self.task.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.task.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(self.task.sort_order, 3)
