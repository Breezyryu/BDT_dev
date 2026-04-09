"""
BDT Status Tab (현황) UI Layout Diagram
Professional annotated wireframe for SOP documentation
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import numpy as np

# Set figure and DPI
fig, ax = plt.subplots(figsize=(14, 10), dpi=180)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')

# Color scheme
bg_color = '#F8F7F5'  # Light warm background
header_color = '#1B2A4A'  # Navy
widget_color = '#FFFFFF'  # White for widgets
widget_border = '#D0D0D0'  # Light gray
accent_color = '#3C5488'  # Theme blue
text_color = '#333333'  # Dark text

# Set background
fig.patch.set_facecolor(bg_color)
ax.add_patch(Rectangle((0, 0), 100, 100, facecolor=bg_color, edgecolor='none'))

# ===== TOP HEADER =====
ax.text(50, 96, 'BDT Status Tab (현황) - UI Layout',
        ha='center', va='top', fontsize=16, fontweight='bold', color=header_color)

# ===== SECTION 1: TOP CONTROL BAR =====
y_top = 88

# Top bar background
top_bar = FancyBboxPatch((2, y_top-4), 96, 4,
                         boxstyle="round,pad=0.1",
                         facecolor=header_color, edgecolor='#000000', linewidth=1.5, alpha=0.9)
ax.add_patch(top_bar)
ax.text(3, y_top-2, 'TOP CONTROL BAR (수평 레이아웃)',
        fontsize=10, fontweight='bold', color='white', va='center')

# Row 1: Three main combo boxes
y_row1 = y_top - 6

# ComboBox 1: Room Selection
combo1_x = 4
combo1_width = 20
combo1 = FancyBboxPatch((combo1_x, y_row1-2.5), combo1_width, 2,
                        boxstyle="round,pad=0.05",
                        facecolor=widget_color, edgecolor=accent_color, linewidth=1.5)
ax.add_patch(combo1)
ax.text(combo1_x + combo1_width/2, y_row1-1.5, 'Room (실험실)',
        ha='center', va='center', fontsize=8, color=text_color)
ax.text(combo1_x + combo1_width + 1.5, y_row1-1.5, 'tb_room',
        ha='left', va='center', fontsize=7, color='#666666', style='italic')

# ComboBox 2: Cycler Selection
combo2_x = combo1_x + combo1_width + 2
combo2_width = 20
combo2 = FancyBboxPatch((combo2_x, y_row1-2.5), combo2_width, 2,
                        boxstyle="round,pad=0.05",
                        facecolor=widget_color, edgecolor=accent_color, linewidth=1.5)
ax.add_patch(combo2)
ax.text(combo2_x + combo2_width/2, y_row1-1.5, 'Cycler (충방전기)',
        ha='center', va='center', fontsize=8, color=text_color)
ax.text(combo2_x + combo2_width + 1.5, y_row1-1.5, 'tb_cycler',
        ha='left', va='center', fontsize=7, color='#666666', style='italic')

# ComboBox 3: Display Info Selection
combo3_x = combo2_x + combo2_width + 2
combo3_width = 20
combo3 = FancyBboxPatch((combo3_x, y_row1-2.5), combo3_width, 2,
                        boxstyle="round,pad=0.05",
                        facecolor=widget_color, edgecolor=accent_color, linewidth=1.5)
ax.add_patch(combo3)
ax.text(combo3_x + combo3_width/2, y_row1-1.5, 'Display (표시정보)',
        ha='center', va='center', fontsize=8, color=text_color)
ax.text(combo3_x + combo3_width + 1, y_row1-1.5, 'tb_info',
        ha='left', va='center', fontsize=7, color='#666666', style='italic')

# Row 2: Search bar area
y_row2 = y_row1 - 3.5

# Search label
ax.text(4, y_row2, 'Find Text:', ha='left', va='center', fontsize=8, fontweight='bold', color=text_color)

# Search input
search_x = 10
search_w = 20
search_box = FancyBboxPatch((search_x, y_row2-1), search_w, 1.2,
                            boxstyle="round,pad=0.05",
                            facecolor=widget_color, edgecolor=widget_border, linewidth=1)
ax.add_patch(search_box)
ax.text(search_x + 0.5, y_row2-0.4, 'FindText (검색입력)',
        ha='left', va='center', fontsize=7, color='#999999', style='italic')
ax.text(search_x + search_w + 1, y_row2-0.4, 'space=OR, comma=AND',
        ha='left', va='center', fontsize=6, color='#888888')

# Highlight Button
btn_hl_x = search_x + search_w + 3
btn_hl = FancyBboxPatch((btn_hl_x, y_row2-1), 5, 1.2,
                        boxstyle="round,pad=0.05",
                        facecolor='#E8F0FF', edgecolor=accent_color, linewidth=1)
ax.add_patch(btn_hl)
ax.text(btn_hl_x + 2.5, y_row2-0.4, '강조',
        ha='center', va='center', fontsize=7, fontweight='bold', color=accent_color)

# Filter Button
btn_filt_x = btn_hl_x + 6
btn_filt = FancyBboxPatch((btn_filt_x, y_row2-1), 5, 1.2,
                          boxstyle="round,pad=0.05",
                          facecolor='#E8F0FF', edgecolor=accent_color, linewidth=1)
ax.add_patch(btn_filt)
ax.text(btn_filt_x + 2.5, y_row2-0.4, '필터링',
        ha='center', va='center', fontsize=7, fontweight='bold', color=accent_color)

# Time label
time_x = btn_filt_x + 6
ax.text(time_x, y_row2-0.4, 'Last modified: 2026-04-09 14:23',
        ha='left', va='center', fontsize=7, color='#666666')

# ===== SECTION 2: SUMMARY & LEGEND AREA =====
y_summary = y_row2 - 3

# Summary table
summary_x = 4
summary_w = 22
summary_h = 3
summary = FancyBboxPatch((summary_x, y_summary-summary_h), summary_w, summary_h,
                         boxstyle="round,pad=0.05",
                         facecolor=widget_color, edgecolor=widget_border, linewidth=1.2)
ax.add_patch(summary)
ax.text(summary_x + 0.5, y_summary-0.5, 'Available',
        ha='left', va='center', fontsize=7, fontweight='bold', color=text_color)
ax.text(summary_x + summary_w/2 + 2, y_summary-0.5, '12',
        ha='right', va='center', fontsize=8, fontweight='bold', color='#00AA00')
ax.text(summary_x + 0.5, y_summary-1.5, 'In Use',
        ha='left', va='center', fontsize=7, fontweight='bold', color=text_color)
ax.text(summary_x + summary_w/2 + 2, y_summary-1.5, '4',
        ha='right', va='center', fontsize=8, fontweight='bold', color='#0066CC')
ax.text(summary_x + summary_w/2, y_summary-summary_h+0.3, 'tb_summary',
        ha='center', va='bottom', fontsize=6, color='#666666', style='italic')

# Color legend table (Temperature)
legend_x = summary_x + summary_w + 3
legend_w = 26
legend = FancyBboxPatch((legend_x, y_summary-summary_h), legend_w, summary_h,
                        boxstyle="round,pad=0.05",
                        facecolor=widget_color, edgecolor=widget_border, linewidth=1.2)
ax.add_patch(legend)

# Legend header
ax.text(legend_x + 0.5, y_summary-0.3, 'Temperature Color Code (온도별 색상)',
        ha='left', va='center', fontsize=8, fontweight='bold', color=text_color)

# Color legend items
colors_temp = [
    ('15°C', (0, 73, 245), 'blue'),
    ('23°C', (18, 21, 23), 'black'),
    ('35°C', (140, 0, 200), 'purple'),
    ('45°C', (208, 0, 0), 'red'),
]
color_x_start = legend_x + 1
for i, (label, rgb, name) in enumerate(colors_temp):
    x_pos = color_x_start + i * 5.5
    # Color swatch
    color_swatch = Rectangle((x_pos, y_summary-1.8), 1.2, 0.8,
                             facecolor='#%02x%02x%02x' % rgb, edgecolor='#333333', linewidth=0.5)
    ax.add_patch(color_swatch)
    ax.text(x_pos + 1.8, y_summary-1.4, label,
            ha='left', va='center', fontsize=6, color=text_color)

# ===== SECTION 3: MAIN CHANNEL TABLE =====
y_table = y_summary - 4

# Table header background
table_header = FancyBboxPatch((2, y_table-2.5), 96, 2.5,
                             boxstyle="round,pad=0.05",
                             facecolor=header_color, edgecolor='#000000', linewidth=1.5, alpha=0.9)
ax.add_patch(table_header)
ax.text(50, y_table-1.25, 'CHANNEL STATUS TABLE (채널상태 메인테이블)',
        ha='center', va='center', fontsize=10, fontweight='bold', color='white')
ax.text(3, y_table-2, '16 rows × 8 columns | tb_channel',
        ha='left', va='center', fontsize=7, color='#CCCCCC')

# Table visualization (simplified grid)
y_table_start = y_table - 3.2
table_rows = 16
table_cols = 8
cell_width = 96 / table_cols
cell_height = 0.35

# Draw sample cells with different background colors
cell_colors_map = {
    (0, 0): '#D0D0D0',    # Running (light gray)
    (1, 0): '#B8D4B0',    # Idle-no cell (light green)
    (2, 0): '#90EE90',    # Completed (green)
    (3, 0): '#FFB6B6',    # Error (red)
    (4, 1): '#D0D0D0',    # Mixed
    (5, 2): '#B8D4B0',
    (6, 3): '#90EE90',
}

for row in range(min(4, table_rows)):  # Show only 4 sample rows
    for col in range(table_cols):
        x_cell = 2 + col * cell_width
        y_cell = y_table_start - row * cell_height

        cell_color = cell_colors_map.get((row, col), '#FFFFFF')
        cell = Rectangle((x_cell, y_cell - cell_height), cell_width, cell_height,
                        facecolor=cell_color, edgecolor=widget_border, linewidth=0.5)
        ax.add_patch(cell)

        # Sample text
        if col == 0:
            text_label = f'{row+1:03d}'
        else:
            text_label = '●' if row % 2 == 0 else '○'

        text_color_cell = '#CC0000' if row == 3 else ('#0066CC' if row == 0 else '#333333')
        ax.text(x_cell + cell_width/2, y_cell - cell_height/2, text_label,
                ha='center', va='center', fontsize=5, color=text_color_cell, fontweight='bold')

# Row labels on left
ax.text(0.8, y_table_start - 0.175, '001', ha='right', va='center', fontsize=6, fontweight='bold')
ax.text(0.8, y_table_start - 1*cell_height - 0.175, '002', ha='right', va='center', fontsize=6)
ax.text(0.8, y_table_start - 2*cell_height - 0.175, '003', ha='right', va='center', fontsize=6)
ax.text(0.8, y_table_start - 3*cell_height - 0.175, '004', ha='right', va='center', fontsize=6)
ax.text(0.8, y_table_start - 4*cell_height - 0.175, '...', ha='right', va='center', fontsize=6)

# Table footer
ax.text(50, y_table_start - 4*cell_height - 1, 'Sample: 001-016 channels | Status colors indicate operational state',
        ha='center', va='center', fontsize=7, color='#666666', style='italic')

# ===== ANNOTATION BOX (RIGHT SIDE) =====
annot_x = 65
annot_width = 32
annot_y = 88

# Section 1: Control Bar Annotation
annot1 = FancyBboxPatch((annot_x, annot_y-8), annot_width, 7,
                        boxstyle="round,pad=0.3",
                        facecolor='#FFFACD', edgecolor='#DAA520', linewidth=1.5, alpha=0.85)
ax.add_patch(annot1)
ax.text(annot_x + 1, annot_y-0.8, 'TOP BAR CONTROLS',
        ha='left', va='top', fontsize=9, fontweight='bold', color='#DAA520')
ax.text(annot_x + 1, annot_y-2, '• Three dropdown filters\n  Room, Cycler, Display Info\n\n• Search with OR/AND\n  Space=OR, Comma=AND\n\n• Highlight & Filter buttons',
        ha='left', va='top', fontsize=7, color='#333333', family='monospace')

# Section 2: Summary & Legend Annotation
annot2_y = annot_y - 9.5
annot2 = FancyBboxPatch((annot_x, annot2_y-8), annot_width, 7,
                        boxstyle="round,pad=0.3",
                        facecolor='#E6F3FF', edgecolor='#1B2A4A', linewidth=1.5, alpha=0.85)
ax.add_patch(annot2)
ax.text(annot_x + 1, annot2_y-0.8, 'STATUS SUMMARY & LEGEND',
        ha='left', va='top', fontsize=9, fontweight='bold', color='#1B2A4A')
ax.text(annot_x + 1, annot2_y-2, '• tb_summary: Quick count\n  Available / In Use\n\n• Color legend: Temperature\n  15°C=Blue, 23°C=Black\n  35°C=Purple, 45°C=Red',
        ha='left', va='top', fontsize=7, color='#333333', family='monospace')

# Section 3: Channel Table Annotation
annot3_y = annot2_y - 9.5
annot3 = FancyBboxPatch((annot_x, annot3_y-7), annot_width, 6.5,
                        boxstyle="round,pad=0.3",
                        facecolor='#F0FFF0', edgecolor='#228B22', linewidth=1.5, alpha=0.85)
ax.add_patch(annot3)
ax.text(annot_x + 1, annot3_y-0.8, 'MAIN TABLE (tb_channel)',
        ha='left', va='top', fontsize=9, fontweight='bold', color='#228B22')
ax.text(annot_x + 1, annot3_y-2, '• 16 rows (channels) × 8 cols\n\n• Status colors:\n  Gray=Running, Green=Idle\n  Dark Green=Done, Red=Error\n\n• Custom BorderDelegate',
        ha='left', va='top', fontsize=7, color='#333333', family='monospace')

# ===== ARROWS & CALLOUTS =====
# Arrow from control bar annotation to top bar
arrow1 = FancyArrowPatch((annot_x, annot_y-1), (combo3_x+combo3_width+5, y_row1-1),
                         arrowstyle='->', mutation_scale=15, linewidth=1.2, color='#DAA520', alpha=0.6)
ax.add_patch(arrow1)

# Arrow from summary annotation to summary table
arrow2 = FancyArrowPatch((annot_x, annot2_y-1), (summary_x+summary_w/2, y_summary-1.5),
                         arrowstyle='->', mutation_scale=15, linewidth=1.2, color='#1B2A4A', alpha=0.6)
ax.add_patch(arrow2)

# Arrow from table annotation to channel table
arrow3 = FancyArrowPatch((annot_x, annot3_y-1), (50, y_table_start-1),
                         arrowstyle='->', mutation_scale=15, linewidth=1.2, color='#228B22', alpha=0.6)
ax.add_patch(arrow3)

# ===== FOOTER =====
footer_y = 2
ax.text(50, footer_y, 'BDT UI Layout Documentation | Status Tab (현황) | For SOP & User Training',
        ha='center', va='center', fontsize=8, color='#666666', style='italic')
ax.text(50, footer_y-0.8, 'Professional wireframe showing layout, widget names (objectName), and user interaction zones',
        ha='center', va='center', fontsize=7, color='#999999')

# ===== LEGEND BOX (Bottom left) =====
legend_box_y = 5
legend_box = FancyBboxPatch((2, legend_box_y-2.5), 20, 2.5,
                            boxstyle="round,pad=0.1",
                            facecolor='#F5F5F5', edgecolor=widget_border, linewidth=1)
ax.add_patch(legend_box)
ax.text(2.5, legend_box_y-0.3, 'KEY (키)',
        ha='left', va='top', fontsize=8, fontweight='bold', color=text_color)
ax.text(2.5, legend_box_y-1, 'Yellow boxes = Annotations\nBlue/Green borders = Qt widgets\nItalic = objectName (code refs)',
        ha='left', va='top', fontsize=6, color='#666666', family='monospace')

plt.tight_layout(pad=1)
plt.savefig('/sessions/beautiful-eloquent-franklin/mnt/BDT_dev/sop_images/tab0_status.png',
            dpi=180, bbox_inches='tight', facecolor=bg_color, edgecolor='none')
print("✓ Diagram saved: /sessions/beautiful-eloquent-franklin/mnt/BDT_dev/sop_images/tab0_status.png")
plt.close()
