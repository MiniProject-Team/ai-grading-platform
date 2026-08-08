"""
---------------------------------------------------------
Module    : paths.py
Project   : SmartHTR
Author    : Ayush Bire

Description:
    Defines all project directory paths.
---------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path


# ==========================================================
# Project Root
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ==========================================================
# Configuration
# ==========================================================

CONFIG_DIR = PROJECT_ROOT / "config"


# ==========================================================
# Models
# ==========================================================

MODELS_DIR = PROJECT_ROOT / "models"

PRETRAINED_MODELS_DIR = PROJECT_ROOT / "pretrained_models"


# ==========================================================
# Outputs
# ==========================================================

OUTPUTS_DIR = PROJECT_ROOT / "outputs"

RESULTS_DIR = OUTPUTS_DIR / "results"

DEBUG_DIR = OUTPUTS_DIR / "debug"


# ==========================================================
# Logs
# ==========================================================

LOGS_DIR = PROJECT_ROOT / "logs"


# ==========================================================
# Test Data
# ==========================================================

TEST_IMAGES_DIR = PROJECT_ROOT / "test_images"


# ==========================================================
# Tests
# ==========================================================

TESTS_DIR = PROJECT_ROOT / "tests"