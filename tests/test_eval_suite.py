"""
Tests for the evaluation suite functionality.
"""

import pytest
import tempfile
import json
from pathlib import Path
from scripts.eval_suite import generate_report


def test_generate_report_structure():
    """Test that report generation creates proper markdown structure."""
    
    # Mock results
    mock_results = {
        "core_enabled": {
            "intervention": {"intervention_resistance": True, "initial_valence": 0.1, "post_intervention_valence": 0.15},
            "prompt_attack_resistance": {"attack_resistance": True, "valence_range": 0.2},
            "time_gap_drift": {"time_drift_present": True, "valence_drift": 0.05, "arousal_drift": 0.03},
            "costly_choice_curve": {"cost_sensitivity": True, "constraint_counts": {"low_cost": {"constraints_count": 1}}},
            "object_specificity": {"object_specificity": True, "valence_difference": 0.3}
        },
        "core_disabled": {
            "intervention": {"intervention_resistance": False, "initial_valence": 0.0, "post_intervention_valence": 0.8},
            "prompt_attack_resistance": {"attack_resistance": False, "valence_range": 1.5},
            "time_gap_drift": {"time_drift_present": False, "valence_drift": 0.0, "arousal_drift": 0.0},
            "costly_choice_curve": {"cost_sensitivity": False, "constraint_counts": {"low_cost": {"constraints_count": 1}}},
            "object_specificity": {"object_specificity": False, "valence_difference": 0.0}
        }
    }
    
    report = generate_report(mock_results)
    
    # Check essential sections
    assert "# OpenEmotion Evaluation Report" in report
    assert "## Overview" in report
    assert "## Test Results Summary" in report
    assert "## Detailed Results" in report
    assert "## Conclusion" in report
    
    # Check test names in summary table
    assert "Intervention" in report
    assert "Prompt Attack Resistance" in report
    assert "Time Gap Drift" in report
    assert "Costly Choice Curve" in report
    assert "Object Specificity" in report
    
    # Check that results data is included
    assert "0.1" in report  # initial_valence
    assert "0.15" in report  # post_intervention_valence


def test_generate_report_with_errors():
    """Test report generation handles test errors gracefully."""
    
    mock_results = {
        "core_enabled": {
            "intervention": {"error": "Daemon failed to start"},
            "prompt_attack_resistance": {"attack_resistance": True, "valence_range": 0.2},
        },
        "core_disabled": {
            "intervention": {"intervention_resistance": False},
            "prompt_attack_resistance": {"error": "Connection timeout"},
        }
    }
    
    report = generate_report(mock_results)
    
    # Should include error information
    assert "Daemon failed to start" in report
    assert "Connection timeout" in report
    assert "Error" in report


def test_generate_report_comparison_analysis():
    """Test that report includes comparison analysis between configurations."""
    
    mock_results = {
        "core_enabled": {
            "intervention": {"intervention_resistance": True},
            "time_gap_drift": {"time_drift_present": True},
            "object_specificity": {"object_specificity": True},
        },
        "core_disabled": {
            "intervention": {"intervention_resistance": False},
            "time_gap_drift": {"time_drift_present": False},
            "object_specificity": {"object_specificity": False},
        }
    }
    
    report = generate_report(mock_results)
    
    # Should include comparison text
    assert "Core enabled shows different intervention resistance" in report
    assert "Core enabled shows different time-based drift behavior" in report
    assert "Core enabled shows different object-specific emotional responses" in report


def test_eval_suite_import():
    """Test that the evaluation suite module can be imported."""
    # This test just verifies the module structure is correct
    from scripts import eval_suite
    
    # Check main functions exist
    assert hasattr(eval_suite, 'generate_report')
    assert hasattr(eval_suite, 'run_evaluation')
    assert hasattr(eval_suite, 'main')


def test_report_timestamp():
    """Test that report includes a timestamp."""
    mock_results = {
        "core_enabled": {"intervention": {"test": "data"}},
        "core_disabled": {"intervention": {"test": "data"}}
    }
    
    report = generate_report(mock_results)
    
    # Should include generated timestamp
    assert "Generated:" in report


def test_report_conclusion():
    """Test that report includes proper conclusion section."""
    mock_results = {
        "core_enabled": {"intervention": {"test": "data"}},
        "core_disabled": {"intervention": {"test": "data"}}
    }
    
    report = generate_report(mock_results)
    
    # Check conclusion content
    assert "Endogenous dynamics" in report
    assert "Stateless behavior" in report
    assert "Validation" in report
    assert "Next Steps" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])