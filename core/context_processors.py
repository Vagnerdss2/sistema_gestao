def navigation(_request):
    """
    Context Processor global que injeta os itens do menu lateral em todos os templates.
    
    Permite que o layout principal (base.html) construa a barra de navegação de forma
    centralizada e dinâmica, sem necessidade de repetição de código nas views.
    """

    return {
        "navigation_items": [
            {"label": "Dashboard", "url_name": "dashboard"},
            {"label": "Estoque", "url_name": "inventory:item-list"},
            {"label": "Inventário", "url_name": "inventory:inventory-list"},
            {"label": "Filiais", "url_name": "organization:branch-list"},
            {"label": "Setores", "url_name": "organization:department-list"},
            {"label": "Colaboradores", "url_name": "organization:employee-list"},
            {"label": "Fornecedores", "url_name": "organization:supplier-list"},
            {"label": "Categorias", "url_name": "organization:category-list"},
            {"label": "Serviços", "url_name": "supportdesk:service-list"},
            {"label": "Cadastro de Login", "url_name": "accounts:register"},
            {"label": "Kanban", "url_name": "kanban:board"},

        ]
    }

