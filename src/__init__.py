"""
Tech Challenge - Pipeline ML End-to-End

Módulo principal do projeto de Machine Learning profissional.
Inclui: data loading, feature engineering, modelagem, treinamento e API.
"""

__version__ = "0.1.0"
__author__ = "Grupo de Estudo de Machine Learning"
__email__ = "rm370908@fiap.com.br"

from . import data, features, model, predict, train

__all__ = ["data", "features", "model", "predict", "train"]
