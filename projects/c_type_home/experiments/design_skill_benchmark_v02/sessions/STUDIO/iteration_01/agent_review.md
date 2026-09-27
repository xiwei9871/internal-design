# Iteration 01 red-team review

## What visually fails

The public-zone composition reads as a family seating group, but the dining edge is too compressed. The saved geometry report records two chair/table overlaps and only 15 mm on the dining-to-kitchen anchor. The diagonal rotations make the sofas feel dynamic, yet the block extents are not represented cleanly in the measurement result, so the CAD evidence is not robust enough for the next pass.

## What has no spatial reason

The side dining chairs are placed directly inside the table bounding box, which has no spatial reason beyond trying to make a four-seat table read quickly. The strong sofa rotations also add visual direction without improving the measured routes. The layout needs one clear hinge axis expressed by placement, while keeping furniture footprints verifiable.

## Does seating read as a group?

Yes. The 3-seat sofa, 2-seat sofa, and lounge chair form a loose conversation triangle along the living perimeter. The balcony opening remains visually legible and the center is mostly open.

## Is the room too empty or fragmented?

The living area is appropriately furniture-light for play and future assisted movement. The dining zone is fragmented by pulled-out chairs and needs a wider service-side strip so it reads as an extension of the kitchen rather than a pinch point.

## Dominant hierarchy

The hierarchy is kitchen/dining service edge -> family seating group -> open activity core -> north balcony. This is the intended calm hinge, but the first iteration overstates the hinge with rotations and understates it with the compressed dining approach.

## Required CAD changes

1. Move the dining table and its four chairs south as one group so the y=3300 kitchen approach is clear.
2. Move the two side chairs outward from the table ends to eliminate footprint overlap.
3. Remove the three furniture rotations so transformed bounding boxes pass and the hinge is carried by aligned placement.
4. Re-render and re-measure the saved DXF before judging the revision.
