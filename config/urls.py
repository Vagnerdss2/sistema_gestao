"""
Roteamento principal de URLs do Sistema de Gestão de TI.

Mapeia as rotas de nível superior para cada aplicativo:
- Painel / Dashboard principal
- Autenticação de Usuários (Login / Logout)
- Módulo Administrativo Django (/admin/)
- Organização (Filiais, Setores, Colaboradores, Fornecedores, Categorias)
- Estoque e Inventário de Colaboradores (/estoque/)
- Atendimentos e Ordens de Serviço (/servicos/)
- Gestão de Tarefas Kanban (/kanban/)
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

from core.views import DashboardView

urlpatterns = [
    # Rota raiz: Painel de Indicadores (Dashboard operacional)
    path("", DashboardView.as_view(), name="dashboard"),

    # Autenticação de usuários
    path("accounts/", include("accounts.urls")),


    # Painel Administrativo padrão do Django
    path("admin/", admin.site.urls),

    # Módulos do Sistema de Gestão
    path("organizacao/", include("organization.urls")),  # Filiais, Setores, Colaboradores, Fornecedores, Categorias
    path("estoque/", include("inventory.urls")),          # Estoque geral e Inventário de colaboradores
    path("compras/", include("procurement.urls")),        # Módulo de compras (legado)
    path("servicos/", include("supportdesk.urls")),       # Ordens de serviço e atendimentos técnicos
    path("kanban/", include("kanban.urls")),              # Quadro visual de tarefas
]

# Em ambiente de desenvolvimento local, serve arquivos estáticos e de mídia (uploads)
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

