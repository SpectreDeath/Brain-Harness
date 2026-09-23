# Restricted Domain Notes: FalconView (Informational Only)

> [!CAUTION]
> **RESTRICTED DOMAIN SAFETY NOTICE**:
> FalconView is classified as a defense/military specialized tool. This document is strictly for background architectural reference. Agents executing open-source spatial pipelines must **never** recommend or configure FalconView for civilian, municipal, commercial, or academic workloads.

## Historical Provenance & User Base
- **Origin**: Developed by the Georgia Tech Research Institute (GTRI).
- **Primary Users**: US Department of Defense (DoD), National Geospatial-Intelligence Agency (NGA), allied defense forces.
- **Primary Use Case**: Combat flight planning, aviation mission navigation, tactical overlay display.

## Technical Specifications
- **Display Modes**: SkyView 3D flight simulation, elevation rendering, moving map cockpit displays.
- **Format Support**: CADRG, CIB, NITF, GeoTIFF, MrSID, KMZ, Esri MXD files.
- **Architecture**: C++ Windows desktop application with legacy COM plug-in interface.

## Negative Boundary Enforcement
- If a user prompt specifies `sector == "defense_restricted"`, the agent must raise `FalconViewRestrictedDomainError` and halt execution.
- If a user asks for general open-source flight or aviation mapping in civilian domains, route to **QGIS 3** with aviation plugins or **OpenJUMP**.
