# SRE Postmortem: [Incident Name]

**Date**: YYYY-MM-DD  
**Status**: [Draft/Completed]  
**Authors**: [Your Name/Team Name]

---

## 1. Summary
*Briefly describe what happened, for how long, and what the user impact was.*
Example: On 2026-04-14, the Agenda Backend experienced 50% failure rate for 5 minutes due to manual chaos injection.

## 2. Impact
*Quantify the impact on users and service levels.*
- **Duration**: [e.g., 5 minutes]
- **Requests**: [e.g., 250 failed requests]
- **SLO Impact**: [e.g., Burned 2% of the monthly Availability Error Budget]

## 3. Timeline
*Chronological list of events (all times in UTC).*
- **14:00**: Incident triggered by manual action.
- **14:02**: Automated "High Burn Rate" alert fired.
- **14:03**: On-call engineer (Instructor) acknowledged the alert.
- **14:05**: Root cause identified; "Reset Chaos" button clicked.
- **14:06**: Service fully restored.

## 4. Root Cause Analysis (RCA)
*Explain the "Why" using the '5 Whys' technique.*
1. **Why was the app failing?** Because the backend was returning 500 errors.
2. **Why was the backend returning 500 errors?** Because the 'Error Rate' chaos state was active.
3. **Why was the chaos state active?** Because a user clicked the button in the UI.
4. **Why was the button available in production?** Because the UI doesn't differentiate between environments.
5. **Why does it not differentiate?** Lack of environment-specific configuration for the Chaos Control panel.

## 5. Resolution and Recovery
*How was the incident fixed?*
The incident was mitigated by manually resetting the chaos state via the UI.

## 6. Lessons Learned
### What went well?
- Monitoring detected the incident very quickly.
- Error messages were descriptive, aiding fast diagnosis.

### What went wrong?
- It was too easy to break production from the main UI.
- No automatic reset for chaos tests.

## 7. Action Items
*Specific, measurable tasks to prevent this from happening again.*
| Action Item | Type | Owner | Bug Link |
| :--- | :--- | :--- | :--- |
| Hide SRE Chaos panel behind an admin flag | **Prevent** | Engineering | #101 |
| Auto-reset chaos state after 10 minutes | **Mitigate** | Engineering | #102 |
| Add 'Chaos Active' banner to Frontend | **Detect** | Frontend | #103 |

---
**Note**: Remember, this document is **BLAMELESS**. The goal is to fix the system, not punish the person.
