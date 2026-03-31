"""
Tech Challenge - Pipeline ML End-to-End

Módulo principal do projeto de Machine Learning profissional.
Inclui: data loading, feature engineering, modelagem, treinamento e API.
"""

__version__ = "0.1.0"
__author__ = "Seu Nome"
__email__ = "seu.email@example.com"

from . import data, features, model, predict, train

__all__ = ["data", "features", "model", "predict", "train"]
