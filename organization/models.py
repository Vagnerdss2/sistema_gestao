from django.core.exceptions import ValidationError
from django.db import models

from core.models import TimeStampedModel


class Branch(TimeStampedModel):
    """
    Representa uma Unidade / Filial física da empresa.
    
    Campos:
    - name: Nome descritivo da filial (ex: Matriz São Paulo, Fábrica Curitiba).
    - code: Código identificador único (ex: SP01, PR02).
    - city: Cidade onde a filial está instalada.
    - state: Unidade Federativa / Estado (UF com 2 letras, ex: SP, PR).
    """

    name = models.CharField("nome", max_length=120)
    code = models.CharField("codigo", max_length=20, unique=True)
    city = models.CharField("cidade", max_length=80)
    state = models.CharField("UF", max_length=2)

    class Meta:
        ordering = ("name",)
        verbose_name = "filial"
        verbose_name_plural = "filiais"

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class Department(TimeStampedModel):
    """
    Representa um Setor / Departamento organizacional da empresa (ex: TI, Financeiro, RH).
    
    Um setor possui nome único e pode operar em uma ou múltiplas filiais (relação Many-to-Many).
    """

    name = models.CharField("nome", max_length=120)
    # Filiais em que este departamento está ativo e autorizado a operar
    branches = models.ManyToManyField(
        Branch,
        related_name="departments",
        verbose_name="filiais",
    )

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(fields=("name",), name="unique_department_name")
        ]
        verbose_name = "setor"
        verbose_name_plural = "setores"

    @property
    def branches_display(self) -> str:
        """Retorna uma string com os códigos das filiais vinculadas separados por vírgula."""
        return ", ".join(self.branches.order_by("code").values_list("code", flat=True))

    def __str__(self) -> str:
        return self.name


class Employee(TimeStampedModel):
    """
    Representa um Colaborador / Funcionário da empresa.
    
    Usado no sistema como:
    - Solicitante ou atendido em Ordens de Serviço (Support Desk).
    - Responsável / possuidor de equipamentos alocados (Inventário).
    - Responsável por tarefas no Kanban.
    """

    full_name = models.CharField("nome completo", max_length=150)
    email = models.EmailField("e-mail", blank=True, null=True)
    job_title = models.CharField("cargo", max_length=120)
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="employees",
        verbose_name="setor",
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name="employees",
        verbose_name="filial",
    )
    is_active = models.BooleanField("ativo", default=True)

    class Meta:
        ordering = ("full_name",)
        verbose_name = "colaborador"
        verbose_name_plural = "colaboradores"
        constraints = [
            # Garante unicidade de e-mail apenas para colaboradores que possuem e-mail preenchido
            models.UniqueConstraint(
                fields=("email",),
                condition=~models.Q(email=None) & ~models.Q(email=""),
                name="unique_non_blank_employee_email",
            )
        ]

    def clean(self) -> None:
        """
        Validações de integridade de regras de negócio:
        1. Se e-mail for string vazia, converte para None para evitar conflito de unicidade.
        2. Garante que a filial selecionada para o colaborador seja uma das filiais permitidas para o seu setor.
        """
        if self.email == "":
            self.email = None
        if self.email:
            qs = Employee.objects.filter(email=self.email)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    {"email": "Já existe um colaborador cadastrado com este e-mail."}
                )
        if (
            self.department_id
            and self.branch_id
            and not self.department.branches.filter(pk=self.branch_id).exists()
        ):
            raise ValidationError(
                {"branch": "A filial precisa estar entre as filiais permitidas para o setor selecionado."}
            )

    def save(self, *args, **kwargs):
        # Normaliza e-mail vazio para None antes de persistir no banco
        if self.email == "":
            self.email = None
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.full_name


class Supplier(TimeStampedModel):
    """
    Representa um Fornecedor parceiro (hardware, software, serviços, infraestrutura).
    """

    legal_name = models.CharField("razao social", max_length=150)
    cnpj = models.CharField("CNPJ", max_length=18, unique=True)
    contact_name = models.CharField("contato", max_length=120, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField("telefone", max_length=30, blank=True)

    class Meta:
        ordering = ("legal_name",)
        verbose_name = "fornecedor"
        verbose_name_plural = "fornecedores"

    def __str__(self) -> str:
        return self.legal_name


class EquipmentCategory(TimeStampedModel):
    """
    Categoria / Classificação dos itens de TI (ex: Notebooks, Desktops, Monitores, Periféricos, Redes).
    """

    name = models.CharField("nome", max_length=100, unique=True)
    description = models.TextField("descricao", blank=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "categoria de equipamento"
        verbose_name_plural = "categorias de equipamento"

    def __str__(self) -> str:
        return self.name

