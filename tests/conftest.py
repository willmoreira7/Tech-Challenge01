"""
Fixtures compartilhadas para todos os testes.

Fixtures definidas aqui ficam disponíveis automaticamente
em todos os arquivos de teste.
"""

import pandas as pd
import pytest


@pytest.fixture
def empty_dataframe():
    """
    Fixture com DataFrame vazio para testar edge cases.
    """
    return pd.DataFrame()
