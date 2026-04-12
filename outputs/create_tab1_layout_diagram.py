"""
BDT Tab 1: 사이클데이터 (Cycle Data) UI Layout Diagram Generator

Creates a professional annotated wireframe/mockup of the Cycle Data tab showing:
- LEFT panel (Path Input, Analysis Options, Profile Options)
- RIGHT panel (Result Plots)
- Workflow annotations with numbered steps
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import numpy as np

# ============================================================================
# COLOR SCHEME
# ============================================================================
BG_LIGHT = "#F8F7F5"        # Light warm background
HEADER_NAVY = "#1B2A4A"     # Navy blue headers
SUBHEADER_TEAL = "#2C6E8A"  # Teal sub-headers
ACCENT_ORANGE = "#E67E22"   # Orange for callouts
TEXT_DARK = "#2C3E50"       # Dark text
BORDER_GRAY = "#BDC3C7"     # Light gray borders
BUTTON_BG = "#E8F4F8"       # Light button background
SUCCESS_GREEN = "#27AE60"   # Green for confirm buttons

# ============================================================================
# FIGURE SETUP
# ============================================================================
fig = plt.figure(figsize=(16, 11), dpi=180, facecolor=BG_LIGHT)
ax = fig.add_subplot(111)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def draw_rounded_rect(ax, xy, width, height, label="", color="white",
                      text_color="black", fontsize=11, bold=False, linewidth=1.5):
    """Draw rounded rectangle with label."""
    fancy_box = FancyBboxPatch(
        xy, width, height,
        boxstyle="round,pad=0.08",
        edgecolor=BORDER_GRAY,
        facecolor=color,
        linewidth=linewidth,
        zorder=1
    )
    ax.add_patch(fancy_box)
    if label:
        weight = "bold" if bold else "normal"
        ax.text(xy[0] + width/2, xy[1] + height/2, label,
                ha="center", va="center",
                fontsize=fontsize, color=text_color,
                weight=weight, zorder=2)

def draw_group_box(ax, xy, width, height, title="", title_color=SUBHEADER_TEAL):
    """Draw a group box with title (like QGroupBox)."""
    # Outer box
    box = FancyBboxPatch(
        xy, width, height,
        boxstyle="round,pad=0.05",
        edgecolor=title_color,
        facecolor="#FAFBFC",
        linewidth=1.2,
        zorder=1
    )
    ax.add_patch(box)

    # Title background
    title_height = 1.0
    title_box = Rectangle(
        (xy[0], xy[1] + height - title_height - 0.1),
        width, title_height + 0.1,
        facecolor=title_color,
        edgecolor="none",
        zorder=2,
        alpha=0.15
    )
    ax.add_patch(title_box)

    # Title text
    if title:
        ax.text(xy[0] + 0.8, xy[1] + height - 0.6,
                title, fontsize=10, weight="bold",
                color=title_color, zorder=3)

def draw_table_skeleton(ax, xy, rows, cols, label="", col_headers=None):
    """Draw a table skeleton."""
    cell_width = 6.5 / cols if cols > 0 else 6.5
    cell_height = 0.4

    # Table border
    table_rect = Rectangle(
        xy, 6.5, rows * cell_height + cell_height,
        facecolor="white", edgecolor=BORDER_GRAY,
        linewidth=1, zorder=1
    )
    ax.add_patch(table_rect)

    # Grid lines
    for i in range(rows + 2):
        y = xy[1] + i * cell_height
        ax.plot([xy[0], xy[0] + 6.5], [y, y],
                color=BORDER_GRAY, linewidth=0.5, zorder=1)

    for j in range(cols + 1):
        x = xy[0] + j * cell_width
        ax.plot([x, x], [xy[1], xy[1] + (rows + 1) * cell_height],
                color=BORDER_GRAY, linewidth=0.5, zorder=1)

    # Column headers if provided
    if col_headers:
        for j, header in enumerate(col_headers):
            x = xy[0] + j * cell_width + cell_width / 2
            y = xy[1] + (rows) * cell_height + cell_height / 2
            ax.text(x, y, header, fontsize=7, ha="center", va="center",
                   weight="bold", color=HEADER_NAVY, zorder=2)

def draw_arrow_annotation(ax, start_xy, end_xy, text="", color=ACCENT_ORANGE,
                         fontsize=9, offset=(0.3, 0.3)):
    """Draw an arrow with annotation text."""
    arrow = FancyArrowPatch(
        start_xy, end_xy,
        arrowstyle="-|>",
        color=color, linewidth=1.8,
        mutation_scale=20, zorder=3
    )
    ax.add_patch(arrow)

    if text:
        mid_x = (start_xy[0] + end_xy[0]) / 2 + offset[0]
        mid_y = (start_xy[1] + end_xy[1]) / 2 + offset[1]
        ax.text(mid_x, mid_y, text, fontsize=fontsize,
               color=color, weight="bold",
               bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                        edgecolor=color, linewidth=1),
               zorder=4)

def draw_button(ax, xy, width, height, label="", color=BUTTON_BG):
    """Draw a button-like rectangle."""
    btn = FancyBboxPatch(
        xy, width, height,
        boxstyle="round,pad=0.05",
        edgecolor=BORDER_GRAY,
        facecolor=color,
        linewidth=1,
        zorder=1
    )
    ax.add_patch(btn)
    if label:
        ax.text(xy[0] + width/2, xy[1] + height/2, label,
               ha="center", va="center",
               fontsize=8, color=TEXT_DARK, zorder=2)

def draw_checkbox(ax, xy, label="", is_checked=False):
    """Draw a checkbox with label."""
    size = 0.4
    check_box = Rectangle(xy, size, size, facecolor="white",
                         edgecolor=BORDER_GRAY, linewidth=0.8, zorder=1)
    ax.add_patch(check_box)

    if is_checked:
        ax.text(xy[0] + size/2, xy[1] + size/2, "✓",
               ha="center", va="center", fontsize=8,
               color=SUCCESS_GREEN, weight="bold", zorder=2)

    if label:
        ax.text(xy[0] + size + 0.2, xy[1] + size/2, label,
               ha="left", va="center", fontsize=8,
               color=TEXT_DARK, zorder=2)

def draw_radio_button(ax, xy, label="", is_selected=False):
    """Draw a radio button with label."""
    size = 0.4
    radio = plt.Circle((xy[0] + size/2, xy[1] + size/2), size/2,
                       facecolor="white", edgecolor=BORDER_GRAY,
                       linewidth=0.8, zorder=1)
    ax.add_patch(radio)

    if is_selected:
        inner = plt.Circle((xy[0] + size/2, xy[1] + size/2), size/3.5,
                          facecolor=SUBHEADER_TEAL, zorder=2)
        ax.add_patch(inner)

    if label:
        ax.text(xy[0] + size + 0.2, xy[1] + size/2, label,
               ha="left", va="center", fontsize=8,
               color=TEXT_DARK, zorder=2)

# ============================================================================
# MAIN TITLE
# ============================================================================
ax.text(50, 98, "BDT Tab 1: 사이클데이터 (Cycle Data) Layout",
        fontsize=18, weight="bold", ha="center",
        color=HEADER_NAVY, zorder=5)

ax.text(50, 96, "PyQt6 UI Component Architecture with Workflow Steps",
        fontsize=10, ha="center", style="italic",
        color=TEXT_DARK, zorder=5)

# ============================================================================
# LEFT PANEL HEADER
# ============================================================================
left_x_start = 1
left_panel_width = 28
left_y_start = 10

ax.text(left_x_start + left_panel_width/2, 94, "LEFT PANEL (Scrollable)",
        fontsize=11, weight="bold", ha="center",
        color=HEADER_NAVY, zorder=5,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#E3F2FD",
                 edgecolor=HEADER_NAVY, linewidth=1.5))

# ============================================================================
# 1. PATH INPUT GROUP BOX
# ============================================================================
path_group_y = 85
path_group_height = 12

draw_group_box(ax, (left_x_start, path_group_y - path_group_height),
              left_panel_width, path_group_height,
              title="1. Path Input (경로 입력)")

# Checkboxes
cb_y = path_group_y - 1.5
draw_checkbox(ax, (left_x_start + 0.5, cb_y - 0), "Cycle Path", is_checked=True)
draw_checkbox(ax, (left_x_start + 0.5, cb_y - 1.2), "Link Processing", is_checked=False)
draw_checkbox(ax, (left_x_start + 0.5, cb_y - 2.4), "ECT Path", is_checked=False)

# Table label
ax.text(left_x_start + 0.5, path_group_y - 3.8, "Path Configuration Table:",
       fontsize=8, weight="bold", color=TEXT_DARK)

# Table skeleton (simplified: 5x7)
table_xy = (left_x_start + 0.3, path_group_y - 8.5)
table_col_headers = ["Test", "Path", "Ch", "Cap", "Cyc", "Mode", "Total"]
draw_table_skeleton(ax, table_xy, 3, 7, col_headers=table_col_headers)

# Buttons
btn_y = path_group_y - 9.5
draw_button(ax, (left_x_start + 0.3, btn_y - 0.6), 3, 0.8, "📁 Load Path", BUTTON_BG)
draw_button(ax, (left_x_start + 3.5, btn_y - 0.6), 3, 0.8, "💾 Save Path", BUTTON_BG)

# ============================================================================
# 2. ANALYSIS OPTIONS SUB-TAB
# ============================================================================
analysis_y = path_group_y - path_group_height - 1.5
analysis_height = 13

draw_group_box(ax, (left_x_start, analysis_y - analysis_height),
              left_panel_width, analysis_height,
              title="2. Analysis Options (분석 옵션)")

# DCIR options
dcir_y = analysis_y - 1.5
ax.text(left_x_start + 0.5, dcir_y - 0.1, "DCIR Method:",
       fontsize=8, weight="bold", color=SUBHEADER_TEAL)
draw_radio_button(ax, (left_x_start + 0.5, dcir_y - 1.0), "Normal DCIR", False)
draw_radio_button(ax, (left_x_start + 0.5, dcir_y - 2.0), "Pulse DCIR", False)
draw_radio_button(ax, (left_x_start + 0.5, dcir_y - 3.0), "MK DCIR", True)

# Graph options
graph_y = dcir_y - 4.2
ax.text(left_x_start + 0.5, graph_y - 0.1, "Graph Options:",
       fontsize=8, weight="bold", color=SUBHEADER_TEAL)
ax.text(left_x_start + 0.8, graph_y - 0.9, "Y-max:", fontsize=7)
draw_rounded_rect(ax, (left_x_start + 1.8, graph_y - 1.1), 1.8, 0.4,
                 label="1.10", color="white", fontsize=7)

ax.text(left_x_start + 0.8, graph_y - 1.7, "Y-min:", fontsize=7)
draw_rounded_rect(ax, (left_x_start + 1.8, graph_y - 1.9), 1.8, 0.4,
                 label="0.65", color="white", fontsize=7)

ax.text(left_x_start + 0.8, graph_y - 2.5, "X-range:", fontsize=7)
draw_rounded_rect(ax, (left_x_start + 1.8, graph_y - 2.7), 1.8, 0.4,
                 label="auto", color="white", fontsize=7)

ax.text(left_x_start + 0.8, graph_y - 3.3, "DCIR scale:", fontsize=7)
draw_rounded_rect(ax, (left_x_start + 1.8, graph_y - 3.5), 1.8, 0.4,
                 label="1", color="white", fontsize=7)

# Analysis mode
mode_y = graph_y - 4.5
ax.text(left_x_start + 0.5, mode_y - 0.1, "Analysis Mode:",
       fontsize=8, weight="bold", color=SUBHEADER_TEAL)
draw_radio_button(ax, (left_x_start + 0.5, mode_y - 0.9), "Individual (개별)", False)
draw_radio_button(ax, (left_x_start + 0.5, mode_y - 1.8), "Overall (통합)", True)

# Buttons
btn_y_analysis = mode_y - 2.8
draw_button(ax, (left_x_start + 0.3, btn_y_analysis - 0.6), 6, 0.8,
           "▶ Cycle Analysis (분석)", SUCCESS_GREEN)
draw_button(ax, (left_x_start + 6.8, btn_y_analysis - 0.6), 5.5, 0.8,
           "🔄 Reset", BUTTON_BG)

# ============================================================================
# 3. PROFILE OPTIONS SUB-TAB
# ============================================================================
profile_y = analysis_y - analysis_height - 1.5
profile_height = 15

draw_group_box(ax, (left_x_start, profile_y - profile_height),
              left_panel_width, profile_height,
              title="3. Profile Options (프로필 옵션)")

# View mode
view_y = profile_y - 1.5
ax.text(left_x_start + 0.5, view_y - 0.1, "View Mode:",
       fontsize=8, weight="bold", color=SUBHEADER_TEAL)
draw_radio_button(ax, (left_x_start + 0.5, view_y - 0.9), "Cycle merged", True)
draw_radio_button(ax, (left_x_start + 0.5, view_y - 1.8), "Cell merged", False)
draw_radio_button(ax, (left_x_start + 0.5, view_y - 2.7), "All merged", False)

# Scope / Continuity / Axis
opt_y = view_y - 3.8
ax.text(left_x_start + 0.5, opt_y - 0.1, "Scope | Continuity | X-axis:",
       fontsize=7, weight="bold", color=SUBHEADER_TEAL)

ax.text(left_x_start + 0.5, opt_y - 0.7, "Scope:", fontsize=7)
draw_radio_button(ax, (left_x_start + 1.2, opt_y - 0.9), "Cycle", True)
draw_radio_button(ax, (left_x_start + 3.2, opt_y - 0.9), "Charge", False)
draw_radio_button(ax, (left_x_start + 5.2, opt_y - 0.9), "Discharge", False)

ax.text(left_x_start + 0.5, opt_y - 1.8, "Cont.:", fontsize=7)
draw_radio_button(ax, (left_x_start + 1.2, opt_y - 2.0), "Overlay", False)
draw_radio_button(ax, (left_x_start + 3.2, opt_y - 2.0), "Continuous", True)

ax.text(left_x_start + 0.5, opt_y - 2.9, "X-axis:", fontsize=7)
draw_radio_button(ax, (left_x_start + 1.2, opt_y - 3.1), "SOC", False)
draw_radio_button(ax, (left_x_start + 3.2, opt_y - 3.1), "Time", True)

# Checkboxes
check_y = opt_y - 4.2
draw_checkbox(ax, (left_x_start + 0.5, check_y - 0.1), "Include Rest", False)
draw_checkbox(ax, (left_x_start + 0.5, check_y - 0.9), "dQ/dV Analysis", False)

# Profile buttons
btn_y_profile = check_y - 1.8
draw_button(ax, (left_x_start + 0.3, btn_y_profile - 0.6), 6, 0.8,
           "▶ Profile Analysis", SUCCESS_GREEN)
draw_button(ax, (left_x_start + 6.8, btn_y_profile - 0.6), 5.5, 0.8,
           "⚡ DCIR", BUTTON_BG)

draw_button(ax, (left_x_start + 0.3, btn_y_profile - 1.6), 6, 0.8,
           "🔄 Tab Reset", BUTTON_BG)

# ============================================================================
# RIGHT PANEL HEADER
# ============================================================================
right_x_start = left_x_start + left_panel_width + 1.5
right_panel_width = 100 - right_x_start - 1

ax.text(right_x_start + right_panel_width/2, 94, "RIGHT PANEL (Results)",
        fontsize=11, weight="bold", ha="center",
        color=HEADER_NAVY, zorder=5,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#F0F4C3",
                 edgecolor=HEADER_NAVY, linewidth=1.5))

# ============================================================================
# RESULT PLOT AREA (Placeholder)
# ============================================================================
plot_y_top = 89
plot_height = 72
plot_rect = FancyBboxPatch(
    (right_x_start, plot_y_top - plot_height),
    right_panel_width, plot_height,
    boxstyle="round,pad=0.3",
    edgecolor=BORDER_GRAY,
    facecolor="#FAFBFC",
    linewidth=1.5,
    zorder=1
)
ax.add_patch(plot_rect)

# Tab widget indicator
ax.text(right_x_start + 1, plot_y_top - 1.5,
       "Cycle Life Plots (사이클 수명 분석 그래프)",
       fontsize=9, weight="bold", color=SUBHEADER_TEAL)

# Placeholder: Capacity retention curve
plot_center_x = right_x_start + right_panel_width / 2
plot_center_y = plot_y_top - plot_height / 2

# Draw sample curve
cycles = np.array([0, 100, 200, 300, 400, 500])
capacity = 1.0 - 0.0001 * cycles  # Simple linear fade for visualization

# Scale to plot area
plot_area_x_start = right_x_start + 2
plot_area_x_end = right_x_start + right_panel_width - 2
plot_area_y_start = plot_y_top - plot_height + 5
plot_area_y_end = plot_y_top - 3

for i in range(len(cycles) - 1):
    x1 = plot_area_x_start + (cycles[i] / cycles[-1]) * (plot_area_x_end - plot_area_x_start)
    y1 = plot_area_y_start + capacity[i] * (plot_area_y_end - plot_area_y_start)
    x2 = plot_area_x_start + (cycles[i+1] / cycles[-1]) * (plot_area_x_end - plot_area_x_start)
    y2 = plot_area_y_start + capacity[i+1] * (plot_area_y_end - plot_area_y_start)
    ax.plot([x1, x2], [y1, y2], color=SUBHEADER_TEAL, linewidth=2.5, zorder=2)
    ax.plot([x1, x2], [y1, y2], "o", color=SUBHEADER_TEAL, markersize=4, zorder=3)

# Axes labels
ax.text(plot_area_x_start - 1.5, plot_area_y_start + (plot_area_y_end - plot_area_y_start) / 2,
       "Capacity (%)", fontsize=8, rotation=90, va="center", ha="right", color=TEXT_DARK)
ax.text(plot_area_x_start + (plot_area_x_end - plot_area_x_start) / 2, plot_area_y_start - 1.5,
       "Cycle Number", fontsize=8, ha="center", va="top", color=TEXT_DARK)

# ============================================================================
# WORKFLOW ANNOTATIONS (Numbered Steps)
# ============================================================================

# Step 1: Load path
arrow1_start = (left_x_start + left_panel_width - 1, path_group_y - 9)
arrow1_end = (left_x_start + left_panel_width - 1, path_group_y - 9.8)
draw_arrow_annotation(ax, arrow1_start, arrow1_end,
                     "① Load cycle\npath files", color=ACCENT_ORANGE, fontsize=8)

# Step 2: Configure analysis
arrow2_start = (left_x_start + left_panel_width - 1, analysis_y - 3)
arrow2_end = (left_x_start + left_panel_width - 1, analysis_y - 3.8)
draw_arrow_annotation(ax, arrow2_start, arrow2_end,
                     "② Select DCIR\nmethod & options", color=ACCENT_ORANGE, fontsize=8)

# Step 3: Run analysis
arrow3_start = (left_x_start + 3, analysis_y - analysis_height - 0.3)
arrow3_end = (left_x_start + 3, analysis_y - analysis_height - 0.8)
draw_arrow_annotation(ax, arrow3_start, arrow3_end,
                     "③ Execute cycle\nanalysis", color=ACCENT_ORANGE, fontsize=8)

# Step 4: View results
arrow4_start = (left_x_start + left_panel_width + 0.5, plot_y_top - 20)
arrow4_end = (right_x_start + 2, plot_y_top - 20)
draw_arrow_annotation(ax, arrow4_start, arrow4_end,
                     "④ View plots in\nRIGHT panel", color=ACCENT_ORANGE, fontsize=8)

# ============================================================================
# LEGEND & REFERENCE INFO
# ============================================================================

ref_y = 8

# Info box 1: Key Features
info_box1 = FancyBboxPatch(
    (left_x_start, ref_y - 4),
    14, 4.5,
    boxstyle="round,pad=0.3",
    edgecolor=SUBHEADER_TEAL,
    facecolor="#E8F6F3",
    linewidth=1,
    zorder=1
)
ax.add_patch(info_box1)

ax.text(left_x_start + 0.5, ref_y - 0.5, "LEFT PANEL FEATURES",
       fontsize=8, weight="bold", color=SUBHEADER_TEAL)
ax.text(left_x_start + 0.5, ref_y - 1.2, "• Path import & validation", fontsize=7)
ax.text(left_x_start + 0.5, ref_y - 1.8, "• DCIR computation methods", fontsize=7)
ax.text(left_x_start + 0.5, ref_y - 2.4, "• Profile & continuity modes", fontsize=7)
ax.text(left_x_start + 0.5, ref_y - 3.0, "• SOC vs Time axis toggle", fontsize=7)
ax.text(left_x_start + 0.5, ref_y - 3.6, "• Real-time plot updates", fontsize=7)

# Info box 2: Right panel features
info_box2 = FancyBboxPatch(
    (right_x_start, ref_y - 4),
    right_panel_width, 4.5,
    boxstyle="round,pad=0.3",
    edgecolor=SUBHEADER_TEAL,
    facecolor="#FEF5E7",
    linewidth=1,
    zorder=1
)
ax.add_patch(info_box2)

ax.text(right_x_start + 0.5, ref_y - 0.5, "RIGHT PANEL OUTPUTS",
       fontsize=8, weight="bold", color=SUBHEADER_TEAL)
ax.text(right_x_start + 0.5, ref_y - 1.2, "▪ Capacity Retention Curve (용량 유지율)", fontsize=7)
ax.text(right_x_start + 0.5, ref_y - 1.8, "▪ DCIR Evolution (내부저항 추이)", fontsize=7)
ax.text(right_x_start + 0.5, ref_y - 2.4, "▪ Voltage Profile (전압 프로필)", fontsize=7)
ax.text(right_x_start + 0.5, ref_y - 3.0, "▪ dQ/dV Peaks (미분 용량 분석)", fontsize=7)
ax.text(right_x_start + 0.5, ref_y - 3.6, "▪ Multi-cell Comparison (다중 셀 비교)", fontsize=7)

# ============================================================================
# FOOTER
# ============================================================================

footer_text = (
    "Note: This is a professional wireframe. Colors and spacing follow BDT design guidelines. "
    "All widgets are PyQt6-based (QGroupBox, QRadioButton, QCheckBox, QPushButton, QTableWidget, "
    "QComboBox, QLineEdit). Plots on the RIGHT use matplotlib FigureCanvas integration."
)
ax.text(50, 1.5, footer_text, fontsize=7.5, ha="center", style="italic",
       color=TEXT_DARK, wrap=True, zorder=5)

# ============================================================================
# SAVE FIGURE
# ============================================================================

plt.tight_layout()
output_path = "/sessions/beautiful-eloquent-franklin/mnt/BDT_dev/sop_images/tab1_cycle.png"
plt.savefig(output_path, dpi=180, bbox_inches="tight", facecolor=BG_LIGHT, edgecolor="none")
print(f"✓ Diagram saved to: {output_path}")

plt.close()

print("\n" + "="*70)
print("BDT Cycle Data Tab UI Layout Diagram Created Successfully")
print("="*70)
print(f"\nFigure Details:")
print(f"  Size: 16 x 11 inches @ 180 DPI")
print(f"  Output: PNG format")
print(f"  Color scheme: Navy (#1B2A4A) + Teal (#2C6E8A) + Orange (#E67E22)")
print(f"  Annotations: 4-step workflow with callout arrows")
print(f"\nLayout Components:")
print(f"  LEFT PANEL (~30% width):")
print(f"    1. Path Input (경로 입력) - 5×7 table, Load/Save buttons")
print(f"    2. Analysis Options (분석 옵션) - DCIR method, graph params")
print(f"    3. Profile Options (프로필 옵션) - View mode, scope, continuity")
print(f"  RIGHT PANEL (~70% width):")
print(f"    Placeholder cycle life plot with capacity retention curve")
print(f"\nWorkflow Steps:")
print(f"  ① Load cycle path files")
print(f"  ② Select DCIR method & options")
print(f"  ③ Execute cycle analysis")
print(f"  ④ View plots in RIGHT panel")
print("="*70)
