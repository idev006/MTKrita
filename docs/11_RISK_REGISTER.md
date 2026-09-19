# Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Opaque segmentation removes real artwork | High | confidence threshold + REVIEW |
| Sheet border touches artwork | High | hybrid extraction + no destructive erase |
| LINE requirements change | Medium | config-driven export profiles + release-time verification |
| Forking Krita creates maintenance burden | High | do not fork during MVP |
| Overuse of AI introduces nondeterminism | Medium | deterministic-first architecture |
| Anti-aliased edges become jagged | High | preserve semi-transparent alpha |
| Auto-scale harms visual consistency | Medium | occupancy thresholds + later set-level normalization |
| False PASS | High | conservative QA rules |
| Too many REVIEW results | Medium | tune thresholds against golden corpus |
| Dependency complexity | Medium | keep core stack minimal |
