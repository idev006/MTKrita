# MTKrita Maintenance and Extension Guide

## Status
SSOT — Maintainability Baseline v1.0

## Purpose
กำหนดวิธีเพิ่ม/เปลี่ยน provider, stage, config, storage และ runtime behavior โดยไม่ทำลาย architecture contracts

## Add a New Provider
1. identify existing provider interface
2. implement contract without leaking concrete engine types
3. register provider ID in composition/registry
4. add TOML selection/config schema
5. add provider-specific tests + contract tests
6. update versions/evidence output
7. add ADR only if interface/architecture changes

## Add a New Pipeline Stage
Requires SSOT requirement/use-case/workflow update, stage contract, state/error/recovery behavior, test plan and traceability before implementation.

## Change a Stage Contract
Treat as breaking until proven otherwise. Update interface spec, dependent modules, manifest/evidence schema, migration note and regression suite.

## Add a Shared Resource
Workers must not access it directly. Add ResourceBroker-mediated contract, ownership/lifecycle rules, concurrency policy and recovery behavior.

## Change Path Layout
PathManager is the only authority. Update path schema and migration/cleanup behavior; consumers continue to use refs rather than raw paths.

## Change Configuration
TOML schema versioning is mandatory for breaking changes. Unknown critical keys fail closed. Effective config hash remains reproducible evidence.

## Dependency Upgrade
Review license, behavior changes, image-quality regression, Windows packaging impact, deterministic behavior and golden corpus before acceptance.

## Maintenance Principle
Prefer compatibility-preserving adapters over broad rewrites. New capability must not bypass SSOT, interfaces, ResourceBroker, PathManager, state machine or diagnostics policy.
