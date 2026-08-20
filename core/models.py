from django.db import models


class TimeStampedModel(models.Model):
    """
    Classe base abstrata que fornece campos automáticos de auditoria temporal.
    
    Todas as entidades do sistema que herdarem desta classe terão automaticamente:
    - created_at: Data e hora exatas de criação do registro no banco de dados.
    - updated_at: Data e hora da última modificação efetuada no registro.
    """

    # Armazena a data/hora em que o registro foi inserido pela primeira vez
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    # Atualiza automaticamente a data/hora sempre que o registro for salvo/alterado
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        # Define que este modelo é abstrato (não cria tabela própria no banco de dados)
        abstract = True

