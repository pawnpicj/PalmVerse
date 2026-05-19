# PalmVerse Improvement Plan

## Goal

Build PalmVerse as a practical MVP that feels like an AI palm scan, while avoiding the highest-risk requirement of fully automatic palm-line extraction from real-world phone photos.

The MVP direction is:

```text
Camera capture
-> backend hand detection / image preparation
-> suggested palm-line template
-> user adjusts draggable palm lines
-> system maps confirmed line features to reading IDs
-> result page with annotated palm image and readings
```

## Key Product Decision

Do not start with 100% automatic palm-line detection.

Palm-line extraction from arbitrary phone photos is sensitive to lighting, shadows, skin tone, camera blur, hand angle, background clutter, and fine crease visibility. The safer MVP is a hybrid workflow:

- AI/image processing prepares the palm image.
- The user confirms or adjusts the major lines.
- The app computes readings from confirmed line geometry.

This keeps the experience interactive, more reliable, and faster to ship.

## Architecture

```text
[Mobile Browser]
  |
  | Capture palm photo with react-webcam or browser media APIs
  v
[Next.js Frontend]
  |
  | POST image as FormData
  v
[FastAPI Backend]
  |
  | Phase 1: mock response
  | Phase 2: MediaPipe hand landmarks, crop, align, quality checks
  v
[Next.js Frontend]
  |
  | Show processed palm image and editable line overlay
  v
[User]
  |
  | Adjust draggable nodes and confirm
  v
[Palmistry Logic]
  |
  | Map geometry features to reading IDs
  v
[Result Screen]
```

## Phase 1: Foundation

Target: 3-5 days

Deliverables:

- Next.js frontend scaffold.
- Mobile-first capture screen.
- Camera preview using browser media APIs.
- Palm guide overlay.
- Capture still image from video.
- Send image to backend with `FormData`.
- FastAPI endpoint: `POST /api/v1/scan-palm`.
- Mock backend response with image placeholder, suggested palm-line template, and sample readings.
- Basic loading, success, and error states.

Success criteria:

- A user can open the app, capture a palm image, send it to the backend, and see a mock scan result.

## Phase 2: Palm Image Preparation

Target: 5-7 days

Deliverables:

- Add MediaPipe Hand Landmarker to backend.
- Detect 21 hand landmarks.
- Validate whether a hand is visible.
- Crop and normalize palm image.
- Add basic quality checks:
  - too dark
  - too bright
  - blurry
  - no hand found
- Return processed image and normalized coordinate space.

Success criteria:

- Backend can reliably detect a hand and return a prepared palm image for common phone photos.

## Phase 3: Interactive Palm Line Editor

Target: 7-10 days

Deliverables:

- Editable overlay for:
  - heart line
  - head line
  - life line
  - fate line
- Draggable nodes on each line.
- Distinct colors per line.
- Confirm button.
- Export confirmed line data as JSON.

Example:

```json
{
  "heart_line": {
    "points": [[120, 180], [210, 160], [320, 175]],
    "length": "medium",
    "curve": "soft",
    "ending_zone": "between_index_middle"
  }
}
```

Success criteria:

- A user can adjust the suggested lines to match their palm and confirm the final geometry.

## Phase 4: Palmistry Logic Engine

Target: 4-6 days

Deliverables:

- Compute features from confirmed line geometry:
  - length
  - curve
  - slope
  - starting zone
  - ending zone
- Map features to `type_id`.
- Store reading copy in JSON.
- Keep interpretation rules separate from display copy.

Success criteria:

- Confirmed geometry produces deterministic reading IDs and corresponding reading text.

## Phase 5: Result Experience

Target: 4-6 days

Deliverables:

- Result screen with annotated palm image.
- Reading cards grouped by palm line.
- Laser scan loading animation.
- Reset / scan again action.
- Save/share-ready result layout.
- Entertainment disclaimer.

Success criteria:

- The scan feels polished, readable, and mobile-friendly.

## Phase 6: Deployment And Testing

Target: 3-5 days

Deliverables:

- Deploy frontend to Vercel.
- Deploy backend to Render or Railway.
- Use HTTPS for camera access.
- Restrict CORS to the production frontend domain.
- Test on:
  - iOS Safari
  - Android Chrome
  - Desktop Chrome
- Test image conditions:
  - low light
  - bright light
  - tilted hand
  - close and far hand
  - cluttered background

Success criteria:

- Public demo works on real mobile devices over HTTPS.

## MVP Scope

Included:

- Camera capture.
- Upload to backend.
- Backend mock scan response.
- Palm guide overlay.
- Editable line template.
- JSON-based readings.
- Result screen.

Deferred:

- Fully automatic palm-line detection.
- Login.
- Payment.
- User history.
- Admin dashboard.
- Custom ML model.
- Multi-language support.
- Complex database schema.

## Implementation Order

1. Create docs and project scaffold.
2. Build frontend capture screen.
3. Build backend mock scan endpoint.
4. Connect frontend to backend.
5. Add mock line overlay and result view.
6. Add draggable editor.
7. Replace mock backend image preparation with MediaPipe.
