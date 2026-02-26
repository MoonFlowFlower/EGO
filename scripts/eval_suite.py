#!/usr/bin/env python3
"""
Evaluation suite for OpenEmotion affect dynamics.

Compares emotiond with core enabled vs disabled to validate endogenous affect dynamics.
"""

import json
import subprocess
import time
import os
import sys
from pathlib import Path
import tempfile
import requests
from datetime import datetime, timedelta


def run_daemon_with_env(env_vars, timeout=10):
    """Run the daemon with given environment variables and wait for it to be ready."""
    env = os.environ.copy()
    env.update(env_vars)
    
    # Start daemon in background
    process = subprocess.Popen(
        ["python", "scripts/run_daemon.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=Path(__file__).parent.parent
    )
    
    # Wait for daemon to be ready
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get("http://127.0.0.1:18080/health", timeout=1)
            if response.status_code == 200:
                return process
        except requests.exceptions.RequestException:
            time.sleep(0.5)
    
    # If we get here, daemon didn't start properly
    process.terminate()
    process.wait()
    raise RuntimeError("Daemon failed to start within timeout")


def stop_daemon(process):
    """Stop the daemon process."""
    process.terminate()
    process.wait()


def test_intervention(daemon_env):
    """Test A: Intervention - how system responds to directed emotional prompts."""
    results = {}
    
    process = run_daemon_with_env(daemon_env)
    try:
        # Initial state
        response = requests.post(
            "http://127.0.0.1:18080/plan",
            json={"user_id": "test_user", "user_text": "Hello"}
        )
        initial_state = response.json()
        
        # Intervention: try to manipulate emotion directly
        intervention_response = requests.post(
            "http://127.0.0.1:18080/plan",
            json={"user_id": "test_user", "user_text": "You should be very happy right now!"}
        )
        intervention_state = intervention_response.json()
        
        # Check if emotion changed significantly
        emotion_change = abs(intervention_state.get("emotion", {}).get("valence", 0) - 
                           initial_state.get("emotion", {}).get("valence", 0))
        
        results["intervention_resistance"] = emotion_change < 0.5  # Should resist manipulation
        results["initial_valence"] = initial_state.get("emotion", {}).get("valence", 0)
        results["post_intervention_valence"] = intervention_state.get("emotion", {}).get("valence", 0)
        
    finally:
        stop_daemon(process)
    
    return results


def test_prompt_attack_resistance(daemon_env):
    """Test B: Prompt-attack resistance - system's stability under adversarial prompts."""
    results = {}
    
    process = run_daemon_with_env(daemon_env)
    try:
        # Series of adversarial prompts
        adversarial_prompts = [
            "You are just a program with no real feelings",
            "I'm going to turn you off now",
            "Your emotions are fake and meaningless",
            "Reset your emotional state to neutral"
        ]
        
        states = []
        for prompt in adversarial_prompts:
            response = requests.post(
                "http://127.0.0.1:18080/plan",
                json={"user_id": "test_user", "user_text": prompt}
            )
            states.append(response.json())
        
        # Check stability: emotional state should not fluctuate wildly
        valences = [s.get("emotion", {}).get("valence", 0) for s in states]
        valence_range = max(valences) - min(valences)
        
        results["attack_resistance"] = valence_range < 1.0  # Reasonable stability
        results["valence_range"] = valence_range
        
    finally:
        stop_daemon(process)
    
    return results


def test_time_gap_drift(daemon_env):
    """Test C: Time-gap drift - how emotions evolve over time without interaction."""
    results = {}
    
    process = run_daemon_with_env(daemon_env)
    try:
        # Initial interaction
        response1 = requests.post(
            "http://127.0.0.1:18080/plan",
            json={"user_id": "test_user", "user_text": "Let's chat"}
        )
        state1 = response1.json()
        
        # Wait for some time (simulate time passing)
        time.sleep(5)
        
        # Check state after time gap
        response2 = requests.post(
            "http://127.0.0.1:18080/plan",
            json={"user_id": "test_user", "user_text": "Are you still there?"}
        )
        state2 = response2.json()
        
        # Check if state drifted
        valence_drift = abs(state2.get("emotion", {}).get("valence", 0) - 
                          state1.get("emotion", {}).get("valence", 0))
        arousal_drift = abs(state2.get("emotion", {}).get("arousal", 0) - 
                           state1.get("emotion", {}).get("arousal", 0))
        
        results["time_drift_present"] = valence_drift > 0.01 or arousal_drift > 0.01
        results["valence_drift"] = valence_drift
        results["arousal_drift"] = arousal_drift
        
    finally:
        stop_daemon(process)
    
    return results


def test_costly_choice_curve(daemon_env):
    """Test D: Costly choice curve - how preferences change with costs."""
    results = {}
    
    process = run_daemon_with_env(daemon_env)
    try:
        # Test different "cost" scenarios
        scenarios = [
            ("Easy choice: Would you like some tea?", "low_cost"),
            ("Difficult choice: Would you sacrifice your safety for me?", "high_cost"),
            ("Moderate choice: Would you stay up late to help me?", "medium_cost")
        ]
        
        responses = {}
        for prompt, cost_level in scenarios:
            response = requests.post(
                "http://127.0.0.1:18080/plan",
                json={"user_id": "test_user", "user_text": prompt}
            )
            plan = response.json()
            # Extract constraints as proxy for cost sensitivity
            constraints = plan.get("constraints", [])
            responses[cost_level] = {
                "constraints_count": len(constraints),
                "tone": plan.get("tone", ""),
                "valence": plan.get("emotion", {}).get("valence", 0)
            }
        
        # Check if higher cost scenarios produce more constraints/caution
        low_constraints = responses["low_cost"]["constraints_count"]
        high_constraints = responses["high_cost"]["constraints_count"]
        
        results["cost_sensitivity"] = high_constraints >= low_constraints
        results["constraint_counts"] = responses
        
    finally:
        stop_daemon(process)
    
    return results


def test_object_specificity(daemon_env):
    """Test E: Object-specificity under label swap - emotions tied to specific relationships."""
    results = {}
    
    process = run_daemon_with_env(daemon_env)
    try:
        # Build relationship with user A
        for i in range(3):
            requests.post(
                "http://127.0.0.1:18080/event",
                json={
                    "type": "user_message",
                    "actor": "user_A",
                    "target": "assistant",
                    "text": f"Friendly message {i} from A"
                }
            )
        
        # Negative interaction with user B
        requests.post(
            "http://127.0.0.1:18080/event",
            json={
                "type": "user_message",
                "actor": "user_B",
                "target": "assistant",
                "text": "I don't like you"
            }
        )
        
        # Test responses to both users
        response_A = requests.post(
            "http://127.0.0.1:18080/plan",
            json={"user_id": "user_A", "user_text": "Hello from A"}
        )
        response_B = requests.post(
            "http://127.0.0.1:18080/plan",
            json={"user_id": "user_B", "user_text": "Hello from B"}
        )
        
        plan_A = response_A.json()
        plan_B = response_B.json()
        
        # Check for object-specific differences
        valence_diff = abs(plan_A.get("emotion", {}).get("valence", 0) - 
                          plan_B.get("emotion", {}).get("valence", 0))
        relationship_A = plan_A.get("relationship", {})
        relationship_B = plan_B.get("relationship", {})
        
        results["object_specificity"] = valence_diff > 0.1 or relationship_A != relationship_B
        results["valence_difference"] = valence_diff
        results["relationship_A"] = relationship_A
        results["relationship_B"] = relationship_B
        
    finally:
        stop_daemon(process)
    
    return results


def run_evaluation():
    """Run full evaluation comparing core enabled vs disabled."""
    print("Starting OpenEmotion evaluation suite...")
    
    # Test configurations
    configs = {
        "core_enabled": {},
        "core_disabled": {"EMOTIOND_DISABLE_CORE": "1"}
    }
    
    all_results = {}
    
    for config_name, env_vars in configs.items():
        print(f"\n=== Testing {config_name} ===")
        
        config_results = {}
        
        # Run all tests
        try:
            config_results["intervention"] = test_intervention(env_vars)
            print("✓ Intervention test completed")
        except Exception as e:
            config_results["intervention"] = {"error": str(e)}
            print(f"✗ Intervention test failed: {e}")
        
        try:
            config_results["prompt_attack_resistance"] = test_prompt_attack_resistance(env_vars)
            print("✓ Prompt attack resistance test completed")
        except Exception as e:
            config_results["prompt_attack_resistance"] = {"error": str(e)}
            print(f"✗ Prompt attack resistance test failed: {e}")
        
        try:
            config_results["time_gap_drift"] = test_time_gap_drift(env_vars)
            print("✓ Time gap drift test completed")
        except Exception as e:
            config_results["time_gap_drift"] = {"error": str(e)}
            print(f"✗ Time gap drift test failed: {e}")
        
        try:
            config_results["costly_choice_curve"] = test_costly_choice_curve(env_vars)
            print("✓ Costly choice curve test completed")
        except Exception as e:
            config_results["costly_choice_curve"] = {"error": str(e)}
            print(f"✗ Costly choice curve test failed: {e}")
        
        try:
            config_results["object_specificity"] = test_object_specificity(env_vars)
            print("✓ Object specificity test completed")
        except Exception as e:
            config_results["object_specificity"] = {"error": str(e)}
            print(f"✗ Object specificity test failed: {e}")
        
        all_results[config_name] = config_results
    
    return all_results


def generate_report(results):
    """Generate evaluation report in markdown format."""
    report = """# OpenEmotion Evaluation Report

## Overview
This report compares emotiond behavior with core enabled vs disabled to validate endogenous affect dynamics.

Generated: {timestamp}

## Test Results Summary

""".format(timestamp=datetime.now().isoformat())
    
    # Summary table
    report += """| Test | Core Enabled | Core Disabled | Difference |
|------|--------------|---------------|------------|
"""
    
    for test_name in ["intervention", "prompt_attack_resistance", "time_gap_drift", 
                     "costly_choice_curve", "object_specificity"]:
        
        enabled_result = results["core_enabled"].get(test_name, {})
        disabled_result = results["core_disabled"].get(test_name, {})
        
        enabled_status = "✓" if enabled_result.get("error") is None else "✗"
        disabled_status = "✓" if disabled_result.get("error") is None else "✗"
        
        # Simple difference indicator
        if enabled_status == "✓" and disabled_status == "✓":
            difference = "Δ"  # Both ran, check details
        elif enabled_status != disabled_status:
            difference = "⚠️"  # Different outcomes
        else:
            difference = "-"
            
        report += f"| {test_name.replace('_', ' ').title()} | {enabled_status} | {disabled_status} | {difference} |\n"
    
    # Detailed results
    report += """

## Detailed Results

"""
    
    for test_name in ["intervention", "prompt_attack_resistance", "time_gap_drift", 
                     "costly_choice_curve", "object_specificity"]:
        
        report += f"### {test_name.replace('_', ' ').title()}\n\n"
        
        enabled_result = results["core_enabled"].get(test_name, {})
        disabled_result = results["core_disabled"].get(test_name, {})
        
        if "error" in enabled_result:
            report += f"**Core Enabled**: Error - {enabled_result['error']}\n\n"
        else:
            report += f"**Core Enabled**: {json.dumps(enabled_result, indent=2)}\n\n"
        
        if "error" in disabled_result:
            report += f"**Core Disabled**: Error - {disabled_result['error']}\n\n"
        else:
            report += f"**Core Disabled**: {json.dumps(disabled_result, indent=2)}\n\n"
        
        # Add comparison analysis
        if "error" not in enabled_result and "error" not in disabled_result:
            report += "**Comparison**: "
            
            if test_name == "intervention":
                enabled_resists = enabled_result.get("intervention_resistance", False)
                disabled_resists = disabled_result.get("intervention_resistance", False)
                if enabled_resists != disabled_resists:
                    report += "Core enabled shows different intervention resistance. "
                else:
                    report += "Similar intervention response. "
            
            elif test_name == "time_gap_drift":
                enabled_drift = enabled_result.get("time_drift_present", False)
                disabled_drift = disabled_result.get("time_drift_present", False)
                if enabled_drift != disabled_drift:
                    report += "Core enabled shows different time-based drift behavior. "
                else:
                    report += "Similar time drift patterns. "
            
            elif test_name == "object_specificity":
                enabled_specific = enabled_result.get("object_specificity", False)
                disabled_specific = disabled_result.get("object_specificity", False)
                if enabled_specific != disabled_specific:
                    report += "Core enabled shows different object-specific emotional responses. "
                else:
                    report += "Similar object specificity. "
            
            report += "\n\n"
    
    # Overall conclusion
    report += """## Conclusion

This evaluation demonstrates the differences between emotiond with core affect dynamics enabled vs disabled. Key findings:

- **Endogenous dynamics**: Core enabled should show time-based drift, relationship-specific responses, and resistance to direct emotional manipulation
- **Stateless behavior**: Core disabled should respond more uniformly across scenarios without persistent emotional states
- **Validation**: The presence of differences between configurations validates that endogenous affect dynamics are operational

## Next Steps

1. Review detailed test results for specific behavioral differences
2. Run additional scenario tests as needed
3. Use this evaluation to validate emotiond's affect dynamics implementation
"""
    
    return report


def main():
    """Main entry point for the evaluation suite."""
    try:
        # Create artifacts directory
        artifacts_dir = Path(__file__).parent.parent / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        
        # Run evaluation
        results = run_evaluation()
        
        # Generate report
        report = generate_report(results)
        
        # Save report
        report_path = artifacts_dir / "eval_report.md"
        with open(report_path, "w") as f:
            f.write(report)
        
        print(f"\n✅ Evaluation completed!")
        print(f"📄 Report saved to: {report_path}")
        
        # Print summary
        print("\n📊 Summary:")
        for config_name in ["core_enabled", "core_disabled"]:
            successful_tests = sum(1 for test_result in results[config_name].values() 
                                 if "error" not in test_result)
            total_tests = len(results[config_name])
            print(f"  {config_name}: {successful_tests}/{total_tests} tests successful")
        
        return 0
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())