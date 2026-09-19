# Windows 11 Distribution Plan

## User Experience Target
ผู้ใช้ปลายทางต้องไม่ต้องติดตั้ง Python, OpenCV, Pillow, NumPy หรือกำหนด PATH ด้วยตนเอง

Preferred distribution:
1. `MTKrita-Setup-x64.exe` — normal installer
2. `MTKrita-Portable-x64.zip` — no-install testing/portable use
3. CLI executable/package for automation operators

## Packaging Strategy
Initial candidate:
- package Python runtime and dependencies with PyInstaller or Nuitka after comparative testing
- installer built using a maintained Windows installer tool such as Inno Setup/WiX candidate
- no mandatory Krita installation for core app

Final packager selection requires benchmark evidence for startup time, antivirus false positives, binary size, dependency compatibility and reproducible builds.

## Installation Requirements
- Windows 11 x64 baseline
- user-writable application data/log/config directory
- install under Program Files for installer distribution
- no administrator privilege for normal runtime unless OS policy requires it

## Installer Verification
Test on clean Windows environment:
- install
- launch
- process transparent sample
- process opaque sample
- export package
- uninstall
- reinstall/upgrade
- filenames containing Thai/Unicode characters
- Windows display scaling

## Code Signing
Production/public installer should be digitally signed to improve trust and reduce SmartScreen friction. Unsigned development builds may be used internally but must be clearly marked.

## Update Strategy
Do not implement auto-update in MVP. First releases may use GitHub Releases and explicit user-driven update. Future updater must verify package integrity/signature and support rollback policy.

## Data Locations
Keep application binary, user settings, logs and job outputs separate. Uninstall must not silently delete user-created output projects.

## Portable Build
Portable build must store temporary/cache data in predictable locations and avoid modifying global system configuration.

## Release Artifacts
Each release should publish:
- installer
- portable archive
- version/changelog
- SHA-256 checksums
- license notices
- known limitations
- test/release evidence summary

## Acceptance Criterion
A non-developer on Windows 11 should be able to install and process a sheet without installing development dependencies or using a terminal.