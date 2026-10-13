# Plan: Redirect Traffic Environment to Main NetCam Vite App + Cleanup

## Goal
When user clicks "ENTER TRAFFIC DASHBOARD" on the organization selector page (`/organization`), redirect to the main NetCam Vite React app running at `http://127.0.0.1:5173` instead of the Next.js traffic dashboard. Also clean up all traffic-specific Next.js components that will become unused.

## Architecture Context
- **net_cam/** (Next.js): Entry point - login, org selector, CAMPUS dashboard - runs on port 3000
- **frontend/** (Vite + React): Main NetCam app (traffic intelligence) - runs on port 5173 (started via `./start-all.sh`)
- Both are separate applications

## Changes Required

### 1. Update Organization Selector (`/home/avrbt/DRISHTI/net_cam/app/organization/page.tsx`)
- Modify `handleSelectOrg` function
- When `org.type === "TRAFFIC"`, redirect to `http://127.0.0.1:5173` (full page redirect via `window.location.href`)
- Keep CAMPUS routing to `/campus/dashboard` (Next.js)

### 2. Cleanup: Remove Unused Traffic-Specific Next.js Files
Since traffic flow moves to Vite app, these net_cam traffic files become dead code:

#### App Routes (entire directories)
- `/home/avrbt/DRISHTI/net_cam/app/traffic/` — all 8 sub-pages (dashboard, alerts, cameras, evidence, network, reports, tracking, vehicles)

#### Domain Components
- `/home/avrbt/DRISHTI/net_cam/domains/traffic/` — entire directory
  - `components/VehicleTrackCard.tsx`
  - `components/VehicleRoute.tsx`
  - `components/VehicleSearch.tsx`
  - `types.ts`

#### Data Files
- `/home/avrbt/DRISHTI/net_cam/data/traffic/` — entire directory (6 files: alerts.ts, cameras.ts, evidence.ts, observations.ts, tracks.ts, vehicles.ts)

#### Shared Components (traffic-specific only)
- `/home/avrbt/DRISHTI/net_cam/components/layout/TrafficSidebar.tsx`
- `/home/avrbt/DRISHTI/net_cam/components/network/TrafficNetwork.tsx`
- `/home/avrbt/DRISHTI/net_cam/components/evidence/EvidenceCard.tsx` (check if campus uses it)
- `/home/avrbt/DRISHTI/net_cam/components/timeline/Timeline.tsx`, `TimelineItem.tsx` (check if campus uses)
- `/home/avrbt/DRISHTI/net_cam/components/tracking/TrackCard.tsx`, `TrackHeader.tsx` (check if campus uses)

#### Components Likely Shared (KEEP)
- `/home/avrbt/DRISHTI/net_cam/components/ui/` — StatCard, LoadingState, EmptyState, StatusBadge
- `/home/avrbt/DRISHTI/net_cam/components/camera/` — CameraCard, CameraGrid, CameraPreview
- `/home/avrbt/DRISHTI/net_cam/components/layout/CampusSidebar.tsx`, `OrganizationBadge.tsx`, `Topbar.tsx`
- `/home/avrbt/DRISHTI/net_cam/components/network/CampusNetwork.tsx`

### 3. Files to KEEP (Campus Flow + Shared)
- `/home/avrbt/DRISHTI/net_cam/app/page.tsx` (redirects to login)
- `/home/avrbt/DRISHTI/net_cam/app/login/page.tsx`
- `/home/avrbt/DRISHTI/net_cam/app/organization/page.tsx` (MODIFIED)
- `/home/avrbt/DRISHTI/net_cam/app/layout.tsx`
- `/home/avrbt/DRISHTI/net_cam/app/campus/` — entire directory
- `/home/avrbt/DRISHTI/net_cam/data/organizations.ts`
- `/home/avrbt/DRISHTI/net_cam/data/campus/` — entire directory
- `/home/avrbt/DRISHTI/net_cam/store/appStore.ts`
- `/home/avrbt/DRISHTI/net_cam/domains/campus/` — entire directory

## Implementation Details

### File: `/home/avrbt/DRISHTI/net_cam/app/organization/page.tsx`

```typescript
const handleSelectOrg = (org: Organization) => {
  setOrganization(org);
  if (org.type === "CAMPUS") {
    router.push("/campus/dashboard");
  } else {
    // TRAFFIC: Redirect to main NetCam Vite app
    window.location.href = "http://127.0.0.1:5173";
  }
};
```

Using `window.location.href` instead of `router.push()` because:
- Different origin (port 3000 → port 5173)
- Next.js router only works within the same Next.js app
- Full page navigation is required

## Validation Steps
1. Run `./start-all.sh` in DRISHTI root (starts backend:8000, ANPR:5000, frontend:5173)
2. Run `npm run dev` in `net_cam/` (starts Next.js on port 3000)
3. Navigate to `http://127.0.0.1:3000`
4. Login with any credentials
5. Click "Traffic Police Organization" card
6. Verify redirect to `http://127.0.0.1:5173` (main NetCam app loads)
7. Click "College Organization" card
8. Verify navigation to `/campus/dashboard` (Next.js campus dashboard still works)
9. Run `npm run build` in `net_cam/` to verify no broken imports from removed files

## Edge Cases
- Vite app not running: User sees "connection refused" - could add health check
- CORS: Not an issue since it's a full page redirect
- Session persistence: Next.js session won't carry over to Vite app (acceptable for demo)

## Out of Scope
- CAMPUS environment (keep as-is in Next.js)
- Shared authentication between Next.js and Vite app
- Iframe embedding (CORS complications)