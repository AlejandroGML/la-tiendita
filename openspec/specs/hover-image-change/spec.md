# hover-image-change Specification

## Purpose

Hover-triggered image swap on product cards: CSS opacity transition to second image_url when user hovers over card.


## Requirements

### Requirement: Hover Image Swap on Product Card

The system MUST swap the product card's primary image to `image_urls[1]` when the user hovers over the card. The transition MUST use a CSS transition (opacity or crossfade, ~300ms). If the product has only one image, the image MUST remain unchanged.

#### Scenario: Hover on product with ≥2 images swaps to second
- GIVEN a product card with `image_urls: ["img1.jpg", "img2.jpg"]`
- WHEN user hovers the mouse over the card
- THEN the displayed image transitions smoothly (300ms) to "img2.jpg"

#### Scenario: Mouse leaves card restores first image
- GIVEN the second image is displayed after hover
- WHEN user moves mouse away from the card
- THEN the image transitions back to the first image

#### Scenario: Single-image product shows no change on hover
- GIVEN a product card with `image_urls: ["only.jpg"]`
- WHEN user hovers the mouse over the card
- THEN the image remains "only.jpg" with no visual change
