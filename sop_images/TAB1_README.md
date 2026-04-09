# BDT Tab 1: 사이클데이터 (Cycle Data) UI Layout Diagram

## Overview

This professional annotated UI layout diagram visualizes the **Cycle Data Analysis Tab** of the Battery Data Tool (BDT), a PyQt6-based desktop application for battery testing and characterization.

**File**: `tab1_cycle.png`  
**Size**: 16 × 11 inches @ 180 DPI (High-resolution PNG)  
**Created**: 2026-04-09

---

## Layout Architecture

### LEFT PANEL (~30% width) - Input Controls & Options

The left side contains all user input controls organized in a scrollable panel:

#### 1. **Path Input (경로 입력)** — Top section
- **Checkboxes**:
  - Cycle Path: Load cycle data from cycler logs
  - Link Processing: Enable linking between related cycles
  - ECT Path: Include ECT (Environmental Chamber Test) data
  
- **Configuration Table** (5 rows × 7 columns):
  - Column headers: Test Name | Path | Channel | Capacity | Cycle | Raw Mode | Total Cycles
  - Displays imported cycle test metadata
  - Allows manual editing of path mappings
  
- **Buttons**:
  - 📁 Load Path: Open file dialog to import path configuration file
  - 💾 Save Path: Export current configuration to JSON/CSV

#### 2. **Analysis Options (분석 옵션)** — Middle section
- **DCIR Method Selection** (Radio buttons):
  - Normal DCIR (Rss steady-state resistance)
  - Pulse DCIR (from HPPC pulse extraction)
  - MK DCIR (Mark Keaton's proprietary formula) — **Default**
  
- **Graph Display Parameters**:
  - Y-max: 1.10 (maximum capacity retention)
  - Y-min: 0.65 (minimum capacity retention)
  - X-range: auto (automatic cycle range calculation)
  - DCIR scale: 1.0 (multiplier for resistance display)
  
- **Analysis Mode** (Radio buttons):
  - Individual (개별): Analyze each cycle/cell separately
  - Overall (통합): Aggregate analysis across all cells/cycles — **Default**
  
- **Buttons**:
  - ▶ **Cycle Analysis** (Green success button): Execute cycle data analysis
  - 🔄 **Reset**: Clear all results and reset tab state

#### 3. **Profile Options (프로필 옵션)** — Bottom section
- **View Mode** (Radio buttons):
  - Cycle merged (사이클 통합): Overlay all cycles on single plot — **Default**
  - Cell merged (셀 통합): Overlay all cells on single plot
  - All merged (전체 통합): Overlay all cycles + all cells
  
- **Data Scope Configuration**:
  - Scope selector: Cycle | Charge | Discharge (full-cycle / charge-only / discharge-only) — **Cycle default**
  - Continuity mode: Overlay (overplot) | Continuous (stack/sequential) — **Continuous default**
  - X-axis: SOC (State of Charge %) | Time (minutes) — **Time default**
  
- **Data Filtering**:
  - Include Rest: Toggle rest period inclusion in analysis
  - dQ/dV Analysis: Enable differential capacity computation
  
- **Buttons**:
  - ▶ **Profile Analysis**: Generate voltage/capacity profile plots
  - ⚡ **DCIR**: Compute and display DCIR evolution
  - 🔄 **Tab Reset**: Clear profile results

---

### RIGHT PANEL (~70% width) - Result Visualization

The right side displays analysis output in a tabbed plot area:

#### Result Plot Tab Widget
- **Default Display**: Cycle Life Analysis Plots showing:
  - **Capacity Retention Curve**: Declining capacity (%) vs. cycle number
  - Y-axis: Capacity ratio (0.65 → 1.10)
  - X-axis: Cycle number (0 → 500+)
  - Color: Teal curve with data point markers
  
- **Multiple Plot Types** (available via sub-tabs):
  - Cycle life graph (capacity fade)
  - DCIR evolution (internal resistance trend)
  - Voltage profile map (V vs. SOC/Time)
  - dQ/dV peaks (differential capacity peaks)
  - Multi-cell comparison overlays
  
- **Interactive Features**:
  - matplotlib toolbar for zoom, pan, save
  - Hover tooltips with data point values
  - Right-click context menu for plot export

---

## Workflow Annotations

The diagram includes **4-step numbered workflow** with orange callout arrows:

### ① **Load Cycle Path Files**
- User clicks "📁 Load Path" button
- File dialog opens to select cycler data directory
- BDT auto-detects cycler type (Toyo CSV vs. PNE binary)
- Path table populates with test metadata

### ② **Select DCIR Method & Options**
- User chooses DCIR calculation method (Normal/Pulse/MK)
- Sets graph parameters (Y-max, Y-min, DCIR scale)
- Selects analysis scope (Individual or Overall)
- Configures display preferences

### ③ **Execute Cycle Analysis**
- User clicks **"▶ Cycle Analysis"** button (main action)
- Backend processes cycle data:
  - Capacity ratio calculation
  - DCIR computation from voltage pulses
  - Trend analysis (polynomial/exponential fitting)
  - Data quality validation
- Progress bar shows processing status

### ④ **View Plots in RIGHT Panel**
- Analysis results display automatically in right panel
- User can:
  - Switch between plot types (tabs)
  - Adjust view mode (Cycle/Cell/All merged)
  - Configure X-axis (SOC vs. Time)
  - Export plots as PNG/PDF

---

## Color Scheme & Design Principles

| Element | Color | Hex Code | Purpose |
|---------|-------|----------|---------|
| Background | Light Warm | #F8F7F5 | Reduce eye strain, professional appearance |
| Header Text | Navy Blue | #1B2A4A | Main titles, section dividers |
| Sub-headers | Teal | #2C6E8A | Group box titles, field labels |
| Buttons (Standard) | Light Blue | #E8F4F8 | Reset, utility buttons |
| Buttons (Confirm) | Green | #27AE60 | Main action buttons (Analysis, Profile) |
| Workflow Arrows | Orange | #E67E22 | Step callouts, important flows |
| Borders | Light Gray | #BDC3C7 | Widget outlines, table grids |
| Text | Dark Gray | #2C3E50 | Body text, labels |

**Design Rationale**:
- Navy + Teal palette: Professional, data-engineering appropriate
- Warm background: Reduces visual fatigue during long analysis sessions
- Orange accents: Draws attention to workflow steps
- Rounded corners: Modern, approachable (PyQt6 friendly)

---

## Widget Technology Stack

All UI elements are **native PyQt6 components**:

| Widget Type | Examples | PyQt6 Class |
|-------------|----------|------------|
| Checkboxes | "Cycle Path", "Link Processing" | `QCheckBox` |
| Radio Buttons | DCIR method, analysis mode | `QRadioButton` |
| Group Boxes | "Path Input", "Analysis Options" | `QGroupBox` |
| Tables | Path configuration (5×7) | `QTableWidget` |
| Buttons | Load/Save, Analysis, Reset | `QPushButton` |
| Line Edits | Y-max, Y-min, X-range, DCIR scale | `QLineEdit` |
| Tab Widget | Result plots (nested tabs) | `QTabWidget` |
| Matplotlib Canvas | Cycle life plots | `FigureCanvas` from matplotlib.backends |

---

## Data Flow

```
User Input (LEFT panel)
     ↓
Load cycle files → Auto-detect cycler type (Toyo/PNE) → Parse data
     ↓
Select DCIR method → Configure graph options → Set analysis scope
     ↓
Click "▶ Cycle Analysis" → Process cycle data (calculate capacity, DCIR, trends)
     ↓
Generate plots → Display in RIGHT panel (matplotlib FigureCanvas)
     ↓
Optional: Configure profile view (SOC/Time, overlay/continuous) → Update plot
```

---

## Key Features & Capabilities

### Data Import
- Load from Toyo cycler (CSV format, auto-encoding detection)
- Load from PNE cycler (binary .blk format)
- Batch import multiple test groups
- Link correlated cycles (RPT, profile phases)

### Analysis Methods
- **DCIR Computation**:
  - Normal: Steady-state resistance (Rss)
  - Pulse: 1-second intercept from HPPC pulse
  - MK: Custom fitting-based extraction
  
- **Capacity Metrics**:
  - Discharge capacity ratio (Dchg)
  - Charge capacity ratio (Chg)
  - Coulombic efficiency (CE = Dchg/Chg)
  
- **Trend Analysis**:
  - Power-law fitting: Q(n) = 1 - a*n^b
  - Exponential fitting for knee detection
  - Linear regression for stable region

### Visualization Modes
- Cycle overlay: All cycles on one plot
- Cell overlay: Compare across cells
- Merged: Combined cycle + cell view
- SOC vs. Time: X-axis toggle
- Continuous vs. Overlay: Y-stacking vs. overplot

### Export & Reporting
- Save plots as PNG/PDF
- Export cycle data to CSV
- Generate analysis summary report
- Copy individual curves to clipboard

---

## Usage Tips

1. **First-time setup**:
   - Click "📁 Load Path" and select the cycler data directory
   - BDT auto-detects file format (Toyo CSV or PNE binary)
   - Verify path table shows expected tests

2. **Quick analysis**:
   - Default options (MK DCIR, Overall, Cycle merged) are pre-configured
   - Click "▶ Cycle Analysis" to run with defaults
   - Most analysis completes in <10 seconds for typical test groups

3. **Detailed profiles**:
   - Switch to "Profile Options" tab
   - Set Scope = Discharge, Continuity = Overlay, X-axis = SOC
   - Click "▶ Profile Analysis" for voltage trajectory plots

4. **DCIR extraction**:
   - Choose "Pulse DCIR" for HPPC-based measurement
   - Click "⚡ DCIR" to display resistance evolution
   - Compare at SOC70% for standard cell evaluation

5. **Multi-cell comparison**:
   - Select "All merged" view mode
   - Overlay plots show capacity spread across channels
   - Identify outlier cells or temperature-dependent behavior

---

## Notes for Development

- **Scrolling**: LEFT panel uses `QScrollArea` for responsive layout on small monitors
- **Threading**: Cycle analysis runs on `QThread` to prevent GUI blocking
- **Plot updates**: matplotlib figures embedded via `FigureCanvas` with toolbar
- **State persistence**: User selections (DCIR method, view mode) saved to config.json
- **Accessibility**: All labels have tooltips; keyboard navigation supported

---

## Related Documentation

- **UI Component Map**: See `ui-component-map.instructions.md` for full widget tree and signal connections
- **Cycle Data Processing**: See `python-style.instructions.md` for data handling conventions
- **Database Integration**: See `database.instructions.md` for Phase 1 cycle_summary schema
- **Battery Science**: See `battery-science.instructions.md` for DCIR, capacity, and degradation theory

---

**Created**: 2026-04-09  
**Version**: 1.0  
**Format**: PNG (high-resolution, 180 DPI)
