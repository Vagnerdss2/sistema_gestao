# Sistema de Gestao de TI

Aplicacao web interna para controle operacional de TI com foco em:

- compras de equipamentos;
- inventario e estoque;
- registro de servicos executados;
- quadro Kanban de tarefas.

## Stack

- Python 3.13+
- Django 5.2
- SQLite em desenvolvimento
- PostgreSQL em producao via variaveis de ambiente
- Templates Django com Tailwind CSS via CDN

## Modulos

- `organization`: filiais, setores, colaboradores, fornecedores e categorias
- `inventory`: itens de estoque/patrimonio e historico de movimentacoes
- `procurement`: ordens de compra com integracao automatica ao estoque
- `supportdesk`: ordens de servico e baixa de itens consumidos
- `kanban`: quadro de tarefas com drag and drop
- `core`: dashboard e componentes compartilhados

## Regras de negocio implementadas

- colaborador herda a filial do setor informado;
- servico associa setor/filial com base no usuario atendido;
- compra marcada como `Entregue` integra os itens ao estoque automaticamente;
- pecas consumidas em servicos geram baixa automatica no estoque;
- dashboard exibe alertas de estoque baixo, compras pendentes e tarefas atrasadas;
- tarefas do Kanban podem ser movidas entre colunas por drag and drop.

## Como rodar localmente

1. Crie e ative um ambiente virtual:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Instale as dependencias:

```powershell
python -m pip install -r requirements.txt
```

3. Execute as migracoes:

```powershell
python manage.py migrate
```

4. Crie um usuario administrador:

```powershell
python manage.py createsuperuser
```

5. Inicie o servidor:

```powershell
python manage.py runserver
```

6. Acesse:

- aplicacao: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- admin: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

## Variaveis de ambiente

Configuracoes suportadas:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

Se `POSTGRES_DB` nao estiver definido, a aplicacao usa SQLite.

## Fluxo recomendado de carga inicial

1. Cadastre filiais e setores.
2. Cadastre colaboradores.
3. Cadastre fornecedores e categorias.
4. Cadastre itens de estoque iniciais.
5. Registre compras e marque como `Entregue` para alimentar o inventario.
6. Registre servicos executados e consumos de pecas.
7. Organize tarefas operacionais no quadro Kanban.

## Testes

Execute:

```powershell
python manage.py test
```

Cobertura atual prioriza as regras mais criticas:

- sincronizacao de filial em colaborador;
- integracao compra -> estoque;
- baixa automatica em servicos;
- atualizacao de status/ordem no Kanban.

## Melhorias futuras

- paginacao e filtros avancados por periodo, filial e setor;
- exportacao CSV/PDF;
- RBAC por perfil operacional;
- auditoria detalhada de alteracoes criticas;
- API interna para integracoes futuras;
- substituicao do Tailwind via CDN por pipeline local para producao.
