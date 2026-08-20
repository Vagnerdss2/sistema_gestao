from django.core.exceptions import ValidationError
from django.db import models

from core.models import TimeStampedModel


class Branch(TimeStampedModel):
    """Representa uma filial da operacao."""

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
    """Setor que pode ser compartilhado entre varias filiais."""

    name = models.CharField("nome", max_length=120)
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
        return ", ".join(self.branches.order_by("code").values_list("code", flat=True))

    def __str__(self) -> str:
        return self.name


class Employee(TimeStampedModel):
    """Colaborador usado como solicitante, atendido e responsavel."""

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
            models.UniqueConstraint(
                fields=("email",),
                condition=~models.Q(email=None) & ~models.Q(email=""),
                name="unique_non_blank_employee_email",
            )
        ]

    def clean(self) -> None:
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
        if self.email == "":
            self.email = None
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.full_name


class Supplier(TimeStampedModel):
    """Fornecedor de equipamentos e servicos."""

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
    """Categoria base para classificacao dos itens."""

    name = models.CharField("nome", max_length=100, unique=True)
    description = models.TextField("descricao", blank=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "categoria de equipamento"
        verbose_name_plural = "categorias de equipamento"

    def __str__(self) -> str:
        return self.name
