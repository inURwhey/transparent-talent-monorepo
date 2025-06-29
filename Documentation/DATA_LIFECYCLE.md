# Transparent Talent: Data Lifecycle Management v1.0

## 1. Introduction & Core Principles

This document defines the official state machines and lifecycle for core data entities within the Transparent Talent system. The goal is to create a predictable, robust, and centralized source of truth for how data transitions between states, what triggers those transitions, and what side effects occur.

### Core Principles:
*   **Centralized Logic:** State transition logic should reside primarily in the backend service layer, not scattered across API endpoints or the frontend.
*   **Explicit States:** All possible states for an entity must be explicitly defined and documented.
*   **Controlled Transitions:** The valid transitions between states are strictly defined. Invalid state changes should be prevented by the system.
*   **Auditable Side Effects:** Actions that occur as a result of a state change (e.g., setting a timestamp, notifying a user) should be predictable and clear.

---

## 2. Entity: Tracked Job (`tracked_jobs`)

### 2.1. Overview
A `tracked_job` represents a user's interaction with a specific job posting (`jobs`). It is the central entity for tracking their application pipeline from initial interest to a final outcome.

### 2.2. Schema & Milestone Timestamps
To support a more robust lifecycle, the `tracked_jobs` table will be enhanced. The `status` column will be converted to a PostgreSQL `ENUM` type, and an optional `status_reason` text field will be added.

The following nullable `TIMESTAMPTZ` columns will be added to capture key process milestones:

*   `applied_at`: Records when the application was formally submitted.
*   `first_interview_at`: Records the date of the first interview, marking the start of the active interview phase.
*   `offer_received_at`: Records when the first offer was received, initiating negotiations.
*   `resolved_at`: Records when the application reached any terminal state, concluding the process.
*   `next_action_at`: A user-set timestamp for their next planned action (CRM functionality).

Furthermore, the following `TEXT` columns will be used for descriptive context:

*   `status_reason`: Stores context for a state, either system-generated (`EXPIRED`) or user-provided (`REJECTED`, `WITHDRAWN`).
*   `next_action_notes`: A user-set note describing the next planned action (CRM functionality).

### 2.3. State Definitions
The following are the official states for the `tracked_jobs.status` ENUM:

*   **`SAVED`**: The initial state when a user first tracks a job. The application has not been submitted.
*   **`APPLIED`**: The user has formally submitted their application to the company.
*   **`INTERVIEWING`**: The user is actively engaged in one or more rounds of interviews.
*   **`OFFER_NEGOTIATIONS`**: The user has received one or more formal offers and is evaluating/negotiating. Offer details are stored in the `job_offers` table.
*   **`OFFER_ACCEPTED`**: A **terminal "success" state**. The user has accepted an employment offer.
*   **`REJECTED`**: A **terminal "failure" state**. The company has declined to move forward, or the user has declined an offer.
*   **`WITHDRAWN`**: A **terminal "decision" state**. The user has voluntarily removed their application from consideration.
*   **`EXPIRED`**: A **terminal "system" state**. The application is considered inactive due to system rules.

### 2.4. State Transition Diagram

<!-- START MERMAID DIAGRAM BLOCK HERE -->
stateDiagram-v2
    direction LR
    [*] --> SAVED

    SAVED --> APPLIED
    APPLIED --> INTERVIEWING
    APPLIED --> REJECTED
    APPLIED --> WITHDRAWN

    INTERVIEWING --> OFFER_NEGOTIATIONS
    INTERVIEWING --> REJECTED
    INTERVIEWING --> WITHDRAWN
    
    OFFER_NEGOTIATIONS --> OFFER_ACCEPTED
    OFFER_NEGOTIATIONS --> REJECTED

    state terminal_states <<join>>
    
    SAVED --> WITHDRAWN
    SAVED --> EXPIRED
    APPLIED --> EXPIRED
    INTERVIEWING --> EXPIRED

    OFFER_ACCEPTED --> terminal_states
    REJECTED --> terminal_states
    WITHDRAWN --> terminal_states
    EXPIRED --> terminal_states

    terminal_states --> [*]
<!-- END MERMAID DIAGRAM BLOCK HERE -->

### 2.5. Transition Rules & Side Effects

| From State | To State | Trigger | Side Effects |
| :--- | :--- | :--- | :--- |
| (Any) | `SAVED` | User Submits URL | `created_at`=now, `updated_at`=now |
| `SAVED` | `APPLIED` | User Action | `updated_at`=now, **`applied_at`=now** |
| `APPLIED` | `INTERVIEWING`| User Action | `updated_at`=now, **`first_interview_at`=now (if null)** |
| `INTERVIEWING`|`OFFER_NEGOTIATIONS`| User Action | `updated_at`=now, **`offer_received_at`=now (if null)** |
| `INTERVIEWING`| `REJECTED` | User Action | `updated_at`=now, **`resolved_at`=now**, (Optional) `status_reason`=user input |
| `OFFER_NEGOTIATIONS`|`OFFER_ACCEPTED`| User Action | `updated_at`=now, **`resolved_at`=now** |
| `OFFER_NEGOTIATIONS`|`REJECTED` | User Action | `updated_at`=now, **`resolved_at`=now**, (Optional) `status_reason`=user input |
| (Any Active) | `WITHDRAWN` | User Action | `updated_at`=now, **`resolved_at`=now**, (Optional) `status_reason`=user input |
| (Any Active) | `EXPIRED` | System Event | `updated_at`=now, `status_reason`=set, **`resolved_at`=now** |
| `APPLIED` | `SAVED` | User Action (Undo) | `updated_at`=now, **`applied_at`=NULL** |

### 2.6. Implementation Plan

The definitions above will be implemented via the following sequence of tasks, which will be added to the backlog as distinct, actionable items:

1.  **DB Migration (Flash Task):**
    *   **Create `job_offers` Table:** Define and create a new table to store offer details (e.g., `tracked_job_id`, `salary`, `bonus`, `is_accepted`).
    *   **Create `tracked_job_status_enum`:** Create a PostgreSQL `ENUM` type with all defined states.
    *   **Alter `tracked_jobs` Table:**
        *   Drop the old `status` column.
        *   Add `status tracked_job_status_enum NOT NULL`.
        *   Add `status_reason TEXT NULL`.
        *   Add milestone timestamps: `applied_at`, `first_interview_at`, `offer_received_at`, `resolved_at`.
        *   Add CRM fields: `next_action_at TIMESTAMPTZ NULL`, `next_action_notes TEXT NULL`.
    *   A data migration script will be needed to map old statuses to new ENUMs.

2.  **Backend (Flash Tasks):**
    *   **`job_offers` API:** Create CRUD endpoints for managing offer details.
    *   **`TrackedJobService`:** Implement a service to manage state transitions and side effects (like setting timestamps).
    *   **Refactor `tracked_jobs` API:** Update existing endpoints to use the new service.

3.  **Frontend (Flash Tasks):**
    *   Update UI to use the new statuses and display milestone dates and CRM fields.
    *   **(Future) Build UI for `job_offers` management.**

4.  **Backlog Update:**
    *   Add **"Feature: Detailed Interview Stage Tracking"** with a requirement for email/calendar integration.
    *   Add **"Feature: AI-Assisted Offer Negotiation"** to leverage the data from the new `job_offers` table.
    *   Add **"BI: Platform-wide Hiring Funnel Analytics"** to leverage the new milestone timestamps.
    *   Add **"Feature: User-set Reminders & Next Action Notifications"** to leverage the new CRM fields.