# Transparent Talent: Product Backlog & Roadmap v1.10

## Unrefined Ideas & Brainstorming
*This section is an inbox for raw ideas. During a "Session Summary" they will be refined, scored, and moved into the prioritized backlog below.*
Phase 1 (Current): User-driven, on-demand analysis. One user submits one job, we run one expensive analysis. This is what we have just hardened.
Phase 2 (Medium-Term): A two-stage system.
Lightweight Pre-Screening: A "gross" calculation (likely a fast, cheaper SQL query or a very simple model) runs across many user:job pairs to find promising candidates.
Detailed Analysis: The full, expensive AI analysis (like we have now) is only triggered for the high-potential pairs identified in the pre-screening.
Phase 3 (Long-Term): ML-driven clustering. Users and jobs are grouped by similarity. Analyses are run on cluster-to-cluster matches, creating massive efficiency and uncovering non-obvious opportunities.

fetch users recommended jobs from all platforms by all notification channels (especially email?) and add them to tracked jobs.

URLs for job boards expire over time, and we should have an explicit means of taking this into account for backfills.

job applications expire (after 30 days?). i remember having this feature before (maybe it's a status in tracked_jobs, or an implication for the front-end via applied_at)  but seem to have lost the explicitness along the way.
---

## Tier 1: Foundational Infrastructure (Highest Priority)
| Feature | Reach | Impact | Confidence | Effort (months) | RICE Score | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Maintenance: Data Integrity Pass** | 1 | 2 | 100% | 0.25 | **8.0** | **To Do** |


## Tier 2: Core User Experience & Differentiation
| Feature | Reach | Impact | Confidence | Effort (months) | RICE Score | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Feature: Define & Verify New User Account Flow** | 1000 | 3 | 100% | 0.5 | **6000** | **To Do** |
| **Feature: User Profile Onboarding & Data Input** | 1000 | 3 | 100% | 0.75 | **4000** | **To Do** |
| **Backend: Automated App Expiration** | 1000 | 1 | 100% | 0.25 | **4000** | **To Do** |
| **UI: Transparent Relevance Scorecard** | 1000 | 3 | 100% | 1.0 | **3000** | **To Do** |
| **UI/UX: 'Jobs for You' Module Restoration** | 1000 | 3 | 90% | 0.75 | **3600** | **To Do** |
| **Feature: Bulk Job Submission (CSV/URLs)** | 500 | 3 | 90% | 1.0 | **1350** | **To Do** |
| **Feature: User Feedback Loop** | 1000 | 3 | 100% | 2.5 | **1200** | **To Do** |


## Tier 3: AI & System Intelligence (Mid-Term)
| Feature | Reach | Impact | Confidence | Effort (months) | RICE Score | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Feature: Instant Analysis for Known Jobs**| 1000 | 2 | 100% | 0.5 | **4000** | **To Do** |
| **Automation: Full API Job Analysis**| 1000 | 3 | 90% | 2.0 | **1350** | **To Do** |
| **Feature: Proactive Anomaly Detection**| 1000 | 3 | 90% | 2.5 | **1080** | **To Do** |
| **Documentation: Codify Industry Standards in Protocols** | 1 | 3 | 90% | 0.25 | **10.8** | **To Do** |
| **Feature: "User News" Sourcing** | 1000 | 2 | 90% | 2.0 | **900** | **To Do** |
| **AI: Multi-Model Verification**| 1000 | 2 | 90% | 2.0 | **900** | **To Do** |
| **Feature: Verifiable Outcomes**| 1000 | 3 | 80% | 3.0 | **800** | **To Do** |
| **Backend: Automated News Sourcing** | 1000 | 1 | 90% | 2.0 | **450** | **To Do** |
| **Backend: System-Wide Staleness Logic** | 1000 | 1 | 100% | 0.5 | **2000** | **To Do** |
| **Feature: "Transparent Rejection"**| 1000 | 3 | 80% | 2.0 | **1200** | **To Do** |
| **Feature: Browser Extension** | 500 | 2 | 80% | 3.0 | **267** | **To Do** |
| **AI: Full Data Leverage Mandate** | 1 | 3 | 90% | 1.0 | **2.7** | **To Do** |
| **AI: Automated Prompt QA System** | 1 | 3 | 80% | 3.0 | **0.8** | **To Do** |
| **Backend: DB-Driven AI Protocols** | 1 | 2 | 100% | 0.5 | **4.0** | **To Do** |

## Tier 4: Future Vision & Long-Term bets
| Feature | Reach | Impact | Confidence | Effort (months) | RICE Score | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Infra: Background Jobs w/ Redis** | 1000 | 2 | 100% | 1.5 | **1333** | **To Do** |
| **Platform: Business Certification** | 5000 | 3 | 50% | 6.0 | **1250** | **To Do** |
| **Platform: System-Wide Analysis from User Submissions**| 1000 | 3 | 80% | 4.0 | **600** | **To Do** |
| **Platform: System-Wide Relevance Calc**| 1000 | 3 | 90% | 6.0 | **450** | **To Do** |
| **Revenue: "Bring Your Own Key" (BYOK) Model** | 200 | 1 | 70% | 0.5 | **280** | **To Do** |
| **Platform: Data Access for Biz** | 1000 | 3 | 50% | 6.0 | **250** | **To Do** |
| **BI: ML User/Company Clustering** | 10 | 3 | 80% | 4.0 | **6.0** | **To Do** |

---

## Completed Features & Bugfixes
*This section lists all completed features and bugfixes, categorized by the release version they were delivered in, in reverse chronological order.*

### [v0.12.0] - 2025-06-29
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Bugfix: New Account Dashboard Error** | T2 | 12000 |
| **UI/UX: Context-Aware "Get Started" Button** | T2 | 4000 |
| **UI/UX: Header "Transparent Talent" Link to Homepage** | UI/UX Polish | N/A |

### [v0.11.0] - 2025-06-28
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **UI/UX: Job Tracker Pagination** | T2 | 4000 |

### [v0.10.0] - 2025-06-28
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **UI/UX: Auto-set 'Date Applied' on Status Change** | T2 | 8000 |

### [v0.9.0] - 2025-06-28
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Deployment: Production Domain** | T2 | 4000 |

### [v0.8.0] - 2025-06-28
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Architecture: Data Contract Standardization** | T1 | 24.0 |

### [v0.7.0] - 2025-06-28
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **UI: Tabular Job Tracker** | T2 | 4000 |

### [v0.6.0] - 2025-06-28
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Feature: User Job Submission** | T2 | 6000 |

### [v0.5.0] - 2025-06-28
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Feature: Logged Out Experience** | T2 | 8000 |

### [v0.4.0] - 2025-06-28
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Bugfix: Resolve Production Authentication** | T1 | 12000 |

### [v0.3.0] - 2025-06-27
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Security: Implement User Authentication** | T1 | 6000 |

### [v0.2.0] - 2025-06-26
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Architecture: Monorepo Setup** | T1 | 12.0 |
| **Deployment: Deploy Frontend** | T1 | 12000 |

### [v0.1.0] - 2025-06-26
| Feature/Bugfix | Original Tier | RICE Score |
| :--- | :--- | :--- |
| **Initial Backend API (v1)** | T1 | N/A |
| **Job Tracker Functionality** | T1 | N/A |
| **Initial Frontend Dashboard (v1)** | T1 | N/A |
| **Comprehensive Data Migration** | T1 | N/A |
| **Upgraded Database** | T1 | N/A |
| **Enhanced Business Logic** | T1 | N/A |