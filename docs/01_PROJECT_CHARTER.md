# Project Charter

## Project Name
**MTKrita — Sticker Production Automation Machine**

## Vision
สร้างสายการผลิตอัตโนมัติที่สามารถเปลี่ยน Sticker Sheet ให้เป็นชุดสติ๊กเกอร์พร้อมใช้งานสำหรับ LINE Creators Market โดยมีคุณภาพสม่ำเสมอ ตรวจสอบได้ และลด human intervention ให้ต่ำที่สุด

## Problem Statement
งาน production ปัจจุบันมีขั้นตอนซ้ำ ได้แก่ การแยกเฟรม ตรวจขอบ ตรวจ transparency ปรับ scale/position export ตั้งชื่อ และ QA ทีละภาพ ซึ่งเหมาะกับ automation และมีความเสี่ยงต่อ human error

## Core Principles
1. Automation First
2. Deterministic Before AI
3. Non-destructive Processing
4. Explainable QA
5. Human-in-the-loop for uncertain cases
6. Config-driven Rules
7. Batch-ready Architecture
8. Reproducible Output
9. Production Logs are First-class Output
10. Never silently discard image content

## In Scope
- Static sticker sheet processing
- Grid/frame extraction
- Transparent and opaque input modes
- Foreground/background separation
- Smart trim / fit / alignment
- QA and safe auto-fix
- Batch export
- LINE export profiles
- Review queue

## Out of Scope for MVP
- Full general-purpose image editor
- AI image generation
- Animated sticker processing
- Automatic LINE submission
- OCR correctness as a blocking rule

## Success Definition
MVP succeeds when it can process one 5×2 sheet into 10 reliable frame outputs, preserve or create transparency safely, generate QA results, and export LINE-ready PNG assets without overwriting the original source.
