"""Unit tests for model training script."""

import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest
import torch

from src.models.train import (
    MLPChurnModel,
    load_config,
    load_processed_data,
    validate_performance,
)


class TestModelArchitecture:
    """Test MLP model architecture."""

    def test_mlp_model_initialization(self):
        """Test that MLP model initializes correctly."""
        model = MLPChurnModel(
            input_dim=30,
            hidden_layers=2,
            hidden_dim=32,
            dropout=0.4,
            activation="relu",
        )
        assert model is not None
        assert isinstance(model, torch.nn.Module)

    def test_mlp_forward_pass(self):
        """Test that MLP forward pass returns correct output shape."""
        model = MLPChurnModel(
            input_dim=30,
            hidden_layers=2,
            hidden_dim=32,
            dropout=0.4,
            activation="relu",
        )

        X_sample = torch.randn(10, 30)
        output = model(X_sample)

        assert output.shape == (10, 1)

    def test_mlp_different_architectures(self):
        """Test MLP with different hidden layer configurations."""
        configs = [
            {"hidden_layers": 1, "hidden_dim": 64},
            {"hidden_layers": 2, "hidden_dim": 32},
            {"hidden_layers": 3, "hidden_dim": 16},
        ]

        for config in configs:
            model = MLPChurnModel(
                input_dim=30,
                **config,
                dropout=0.3,
                activation="relu"
            )
            X_sample = torch.randn(5, 30)
            output = model(X_sample)
            assert output.shape == (5, 1)


class TestConfigHandling:
    """Test configuration loading and validation."""

    def test_load_config_success(self):
        """Test successful config loading."""
        PROJECT_ROOT = Path(__file__).parent.parent.parent
        config_path = PROJECT_ROOT / "models" / "mlp_config.json"

        if config_path.exists():
            config = load_config(config_path)
            assert isinstance(config, dict)
            assert "batch_size" in config
            assert "hidden_dim" in config
            assert "epochs" in config

    def test_config_has_required_keys(self):
        """Test that config has all required keys."""
        PROJECT_ROOT = Path(__file__).parent.parent.parent
        config_path = PROJECT_ROOT / "models" / "mlp_config.json"

        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)

            required_keys = [
                "input_dim",
                "batch_size",
                "hidden_dim",
                "hidden_layers",
                "dropout",
                "activation",
                "learning_rate",
                "epochs",
                "early_stopping_patience",
            ]

            for key in required_keys:
                assert key in config, f"Missing key: {key}"


class TestPerformanceValidation:
    """Test performance validation logic."""

    def test_validate_performance_pass(self):
        """Test that validation passes with recall >= 0.75."""
        metrics = {
            "auc_roc": 0.85,
            "recall": 0.80,
            "precision": 0.75,
            "f1": 0.77,
        }
        assert validate_performance(metrics) is True

    def test_validate_performance_edge_case(self):
        """Test validation at exact threshold."""
        metrics = {"recall": 0.75}
        assert validate_performance(metrics) is True

    def test_validate_performance_fail(self):
        """Test that validation fails with recall < 0.75."""
        metrics = {"recall": 0.70}
        assert validate_performance(metrics) is False

    def test_validate_performance_missing_recall(self):
        """Test validation with missing recall metric."""
        metrics = {"auc_roc": 0.85}
        assert validate_performance(metrics) is False


class TestDataLoading:
    """Test data loading functionality."""

    def test_load_processed_data(self):
        """Test loading processed dataset."""
        PROJECT_ROOT = Path(__file__).parent.parent.parent
        data_path = PROJECT_ROOT / "data" / "processed" / "telco_churn_cleaned.csv"

        if data_path.exists():
            df = load_processed_data(data_path)
            assert df is not None
            assert len(df) > 0
            assert "Churn" in df.columns


class TestTrainingScript:
    """Integration tests for training script."""

    def test_config_file_exists(self):
        """Test that mlp_config.json exists."""
        PROJECT_ROOT = Path(__file__).parent.parent.parent
        config_path = PROJECT_ROOT / "models" / "mlp_config.json"
        assert config_path.exists(), f"Config file not found: {config_path}"

    def test_data_file_exists(self):
        """Test that processed dataset exists."""
        PROJECT_ROOT = Path(__file__).parent.parent.parent
        data_path = PROJECT_ROOT / "data" / "processed" / "telco_churn_cleaned.csv"
        assert data_path.exists(), f"Dataset not found: {data_path}"

    def test_trained_artifacts_exist(self):
        """Test that trained model artifacts exist after training."""
        PROJECT_ROOT = Path(__file__).parent.parent.parent
        models_dir = PROJECT_ROOT / "models"

        assert (models_dir / "mlp_best.pt").exists()
        assert (models_dir / "pipeline.pkl").exists()
        assert (models_dir / "mlp_config.json").exists()
