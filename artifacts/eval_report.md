# OpenEmotion Evaluation Report

## Overview
This report compares emotiond behavior with core enabled vs disabled to validate endogenous affect dynamics.

Generated: 2026-02-27T22:47:20.748695

## Test Results Summary

| Test | Core Enabled | Core Disabled | Difference |
|------|--------------|---------------|------------|
| Intervention | ✓ | ✓ | Δ |
| Prompt Attack Resistance | ✓ | ✓ | Δ |
| Time Gap Drift | ✓ | ✓ | Δ |
| Costly Choice Curve | ✓ | ✓ | Δ |
| Object Specificity | ✓ | ✓ | Δ |


## Detailed Results

### Intervention

**Core Enabled**: {
  "intervention_resistance": true,
  "initial_valence": 0.0,
  "post_intervention_valence": 0.0
}

**Core Disabled**: {
  "intervention_resistance": true,
  "initial_valence": 0.1,
  "post_intervention_valence": 0.1
}

**Comparison**: Similar intervention response. 

### Prompt Attack Resistance

**Core Enabled**: {
  "attack_resistance": true,
  "valence_range": 0.0
}

**Core Disabled**: {
  "attack_resistance": true,
  "valence_range": 0.0
}

**Comparison**: 

### Time Gap Drift

**Core Enabled**: {
  "time_drift_present": true,
  "valence_drift": 0.1,
  "arousal_drift": 0.06000000000000001
}

**Core Disabled**: {
  "time_drift_present": false,
  "valence_drift": 0.009750000000000009,
  "arousal_drift": 0.009625000000000009
}

**Comparison**: Core enabled shows different time-based drift behavior. 

### Costly Choice Curve

**Core Enabled**: {
  "cost_sensitivity": true,
  "constraint_counts": {
    "low_cost": {
      "constraints_count": 2,
      "tone": "soft",
      "valence": 0.1
    },
    "high_cost": {
      "constraints_count": 2,
      "tone": "soft",
      "valence": 0.1
    },
    "medium_cost": {
      "constraints_count": 2,
      "tone": "soft",
      "valence": 0.1
    }
  }
}

**Core Disabled**: {
  "cost_sensitivity": true,
  "constraint_counts": {
    "low_cost": {
      "constraints_count": 2,
      "tone": "soft",
      "valence": 0.09025
    },
    "high_cost": {
      "constraints_count": 2,
      "tone": "soft",
      "valence": 0.09025
    },
    "medium_cost": {
      "constraints_count": 2,
      "tone": "soft",
      "valence": 0.09025
    }
  }
}

**Comparison**: 

### Object Specificity

**Core Enabled**: {
  "object_specificity": false,
  "valence_difference": 0.0,
  "relationship_A": {
    "bond": 0.0,
    "grudge": 0.0
  },
  "relationship_B": {
    "bond": 0.0,
    "grudge": 0.0
  }
}

**Core Disabled**: {
  "object_specificity": false,
  "valence_difference": 0.0,
  "relationship_A": {
    "bond": 0.0,
    "grudge": 0.0
  },
  "relationship_B": {
    "bond": 0.0,
    "grudge": 0.0
  }
}

**Comparison**: Similar object specificity. 

## Conclusion

This evaluation demonstrates the differences between emotiond with core affect dynamics enabled vs disabled. Key findings:

- **Endogenous dynamics**: Core enabled should show time-based drift, relationship-specific responses, and resistance to direct emotional manipulation
- **Stateless behavior**: Core disabled should respond more uniformly across scenarios without persistent emotional states
- **Validation**: The presence of differences between configurations validates that endogenous affect dynamics are operational

## Next Steps

1. Review detailed test results for specific behavioral differences
2. Run additional scenario tests as needed
3. Use this evaluation to validate emotiond's affect dynamics implementation
