def navigation(_request):
    """Itens de navegacao principais compartilhados pelo layout."""

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
            {"label": "Kanban", "url_name": "kanban:board"},
        ]
    }
