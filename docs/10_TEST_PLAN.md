# Test Plan

## Strategy
Use unit tests, golden-image tests and end-to-end tests.

## Golden Corpus

### Transparent Cases
1. perfect alpha
2. semi-transparent antialiased edge
3. RGBA but fully opaque
4. isolated alpha noise
5. artwork touching frame edge
6. caption near edge

### Opaque Cases
7. pure white background
8. solid color background
9. near-uniform gradient
10. shadowed background
11. complex background
12. foreground similar to background

### Sheet Geometry
13. exact 5×2
14. resized sheet
15. border-thickness variation
16. missing separator
17. extra outer margin

## Assertions
- frame count and order
- content preservation
- alpha correctness
- output dimensions
- deterministic result where expected
- expected QA state

## Regression Policy
Every fixed bug must add a regression fixture before merge.

## Safety Tests
Tests must verify that original input files are never overwritten by default and that uncertain segmentation cannot silently delete visible content.
