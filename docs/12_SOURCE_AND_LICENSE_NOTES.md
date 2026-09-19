# Source and License Notes

## Krita
- Open-source under GPL v3.
- Source may be modified.
- Distribution of modified GPL binaries requires corresponding source obligations.
- Planned role in MTKrita: optional manual-review/editor integration, not the core MVP engine.

Official: https://krita.org/en/about/license/

## OpenCV
- OpenCV 4.5.0+ is distributed under Apache License 2.0.
- Planned role: core computer-vision and image-analysis library.

Official: https://opencv.org/license/

## ImageMagick
- Optional processing/export backend.
- License must be reviewed before distribution choices are finalized.

Official: https://imagemagick.org/script/license.php

## LINE Creators Market
Production rules must be revalidated against official LINE documentation before a release is declared submission-ready.

Official guideline entry point: https://creator.line.me/en/guideline/

## Licensing Architecture Principle
Keep GPL-dependent/editor integration boundaries explicit. Avoid copying GPL application code into an independently licensed core unintentionally. Perform a dedicated license review before public or commercial distribution.
