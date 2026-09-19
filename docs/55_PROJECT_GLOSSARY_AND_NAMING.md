# MTKrita Project Glossary and Naming

## Status
SSOT — Terminology Baseline v1.0

## Purpose
ลดความกำกวมระหว่างทีม Product, Architecture, Development, QA และ Operations

## Core Terms
- **Sticker Sheet** — ไฟล์ภาพที่ประกอบด้วยหลาย sticker frames
- **Frame** — หน่วย sticker หนึ่งช่องที่ถูก split จาก sheet
- **Frame Border** — เส้นขอบ/กรอบของแต่ละ frame ซึ่งไม่ใช่ artwork
- **Frame Number / Sheet Metadata** — หมายเลขหรือข้อมูลกำกับ sheet ที่ไม่ใช่ sticker content
- **Meaningful Transparency** — alpha ที่บ่งชี้ว่าพื้นหลังถูกทำโปร่งใสแล้วจริง
- **Opaque Frame** — frame ที่ไม่มี meaningful transparency
- **Provider** — implementation ของ capability หลัง MTKrita-owned interface
- **Orchestrator** — Python control logic ที่กำหนดลำดับ/routing/policy
- **MainBoard** — control-plane composition root สำหรับ scheduling, workers, resources, events, state และ diagnostics
- **Worker** — isolated execution agent ที่รับ task แล้วคืน result/evidence
- **PathManager** — authority สำหรับ path/resource-location resolution
- **ResourceBroker** — authority สำหรับ shared mutable resources และ commit coordination
- **JobStore** — durable control-state store
- **ArtifactStore** — managed storage/commit layer สำหรับ artifacts
- **Task** — schedulable unit of work
- **Attempt** — execution instance ของ task เดียวกัน
- **Lease** — temporary authority ของ worker ต่อ task attempt
- **Checkpoint** — durable resumable boundary
- **REVIEW** — สถานะที่ต้องให้มนุษย์ตรวจเพราะ automation ไม่มั่นใจพอ
- **Golden Corpus** — test dataset ที่ได้รับอนุมัติสำหรับ regression/acceptance
- **SSOT** — Single Source of Truth ของโครงการ

## Naming Rules
- Requirement IDs: `PR-###`
- Mandatory functions: `MF-###`
- Use cases: `UC-###`
- Architecture decisions: `ADR-###`
- Stages: `S-##`
- Stable error codes: `DOMAIN.REASON`
- Job/task/attempt identifiers must be opaque stable IDs, not filenames

## Language Rule
เอกสารสามารถใช้ไทย/อังกฤษร่วมกันได้ แต่ technical identifiers, state names, interfaces, error codes และ config keys ใช้ English เพื่อความคงที่ใน code/test/logs.
