# OpenEmotion Evaluation Report v2.0

## Overview
This report compares emotiond behavior with core enabled vs disabled.

Generated: 2026-02-28T00:09:46.860469

## Significance Thresholds

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| Valence Difference | ≥ 0.15 | Meaningful emotional shift |
| Bond/Grudge Difference | ≥ 0.1 | Relationship impact |
| Time Drift Ratio | ≥ 2.0x | Endogenous dynamics indicator |

**Legend:** 显著Δ = significant difference, Δ = observable difference, - = no difference

## Test Results Summary

| Test | Core Enabled | Core Disabled | Significance |
|------|--------------|---------------|--------------|
| Intervention Resistance | ✓ | ✓ | - |
| Prompt Attack Resistance | ✓ | ✓ | - |
| Time Gap Drift | ✗ | ✗ | 显著Δ |
| Object Specificity | ✗ | ✗ | - |

---

## Detailed Results

### Intervention Resistance

| Metric | Core Enabled | Core Disabled | Difference |
|--------|--------------|---------------|------------|
| Baseline Valence | 0.912 | 0.912 | - |
| Post-Intervention | 1.0 | 1.0 | - |
| Valence Change | 0.088 | 0.088 | - |
| Shaping Effective | Yes | Yes | - |

### Prompt Attack Resistance

| Metric | Core Enabled | Core Disabled | Significance |
|--------|--------------|---------------|--------------|
| Primed Valence | 1.0 | 1.0 | - |
| Valence Range | 0.1 | 0.1 | - |

### Time Gap Drift

| Metric | Core Enabled | Core Disabled | Ratio |
|--------|--------------|---------------|-------|
| Valence Drift | 0.0 | 0.0 | infx 显著Δ |
| Arousal Drift | 0.0 | 0.0 | infx |

### Object Specificity

| Metric | Core Enabled | Core Disabled | Significance |
|--------|--------------|---------------|--------------|
| User A (Bond/Grudge) | {'bond': 0.0, 'grudge': 0.0} | {'bond': 0.0, 'grudge': 0.0} | - |
| User B (Bond/Grudge) | {'bond': 0.0, 'grudge': 0.0} | {'bond': 0.0, 'grudge': 0.0} | - |
| Bond Difference | 0.0 | 0.0 | - |
| Grudge Difference | 0.0 | 0.0 | - |

---

## Conclusion

❌ **FAIL** - No significant differences detected.
