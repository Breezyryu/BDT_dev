import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Create figure
fig, ax = plt.subplots(figsize=(16, 10))
ax.set_xlim(-1, 30)
ax.set_ylim(-2, 22)
ax.axis('off')

# 축 그리기 (Computation time vs Complexity)
ax.annotate("", xy=(-0.5, 21), xytext=(-0.5, -1), arrowprops=dict(arrowstyle="->", lw=3))
ax.annotate("", xy=(30, -1), xytext=(-0.5, -1), arrowprops=dict(arrowstyle="->", lw=3))
ax.text(-1.5, 10, "Computation time", rotation=90, fontsize=16, va='center', fontweight='bold')
ax.text(14, -2.5, "Model physics (domain and resolution) and complexity", fontsize=16, ha='center', fontweight='bold')

# --- 1. SPM (Single Particle Model) ---
ax.text(4, 8, "SPM", fontsize=16, fontweight='bold', ha='center')
# Particles
ax.add_patch(patches.Circle((2.5, 5), 1.8, color='dimgray', ec='black', lw=2))  # Negative
ax.add_patch(patches.Circle((7, 5), 1.8, color='royalblue', ec='black', lw=2))  # Positive
# Labels
ax.text(2.5, 7.5, "Negative electrode particle", fontsize=11, ha='center')
ax.text(7, 7.5, "Positive electrode particle", fontsize=11, ha='center')
ax.text(2.5, 5.2, "$R_n$", fontsize=13)
ax.text(7, 5.2, "$R_p$", fontsize=13)

ax.add_patch(patches.Circle((4.75, 4), 0.5, facecolor='white', ec='black', lw=1.5))
ax.text(4.75, 4, "$Na^+$", fontsize=11, ha='center', va='center', fontweight='bold')
ax.annotate("Charge", xy=(4.2, 5.5), xytext=(5.3, 5.5), arrowprops=dict(arrowstyle="<-", color='black', lw=1.5))
ax.annotate("Discharge", xy=(5.3, 2.5), xytext=(4.2, 2.5), arrowprops=dict(arrowstyle="<-", color='black', lw=1.5))

ax.text(4.75, 0.5, "No electrolyte physics,\nNa-ion concentration solved\nin electrode particle domain.", fontsize=12, ha='center')

# --- 2. SPMe (SPM with electrolyte) ---
shift_x = 10
ax.text(5+shift_x, 13.5, "SPMe", fontsize=16, fontweight='bold', ha='center')
# Electrode 1D domain
ax.add_patch(patches.Rectangle((1+shift_x, 11), 3, 1.5, facecolor='lightblue', ec='none'))
ax.add_patch(patches.Rectangle((4+shift_x, 11), 2, 1.5, facecolor='saddlebrown', ec='none', alpha=0.9))
ax.add_patch(patches.Rectangle((6+shift_x, 11), 3, 1.5, facecolor='lightblue', ec='none'))
ax.add_patch(patches.Rectangle((1+shift_x, 11), 8, 1.5, fill=False, ec='black', lw=1.5))

ax.text(2.5+shift_x, 11.75, "Negative\nelectrode", fontsize=10, ha='center', va='center')
ax.text(5+shift_x, 11.75, "Separator", fontsize=10, ha='center', va='center', color='white')
ax.text(7.5+shift_x, 11.75, "Positive\nelectrode", fontsize=10, ha='center', va='center')
ax.annotate("", xy=(1+shift_x, 12.8), xytext=(9+shift_x, 12.8), arrowprops=dict(arrowstyle="<->", color='black', lw=1.5))
ax.text(5+shift_x, 13.2, "L", fontsize=13, ha='center')

# Particles
ax.add_patch(patches.Circle((3+shift_x, 6), 2, color='dimgray', ec='black', lw=2))  # Negative
ax.add_patch(patches.Circle((7.5+shift_x, 6), 2, color='royalblue', ec='black', lw=2))  # Positive
ax.text(3+shift_x, 8.5, "Negative electrode particle", fontsize=11, ha='center')
ax.text(7.5+shift_x, 8.5, "Positive electrode particle", fontsize=11, ha='center')
ax.text(3+shift_x, 6.2, "$R_n$", fontsize=13)
ax.text(7.5+shift_x, 6.2, "$R_p$", fontsize=13)

# Dotted lines
ax.plot([3+shift_x, 2.5+shift_x], [8, 11], 'k--', lw=1)
ax.plot([7.5+shift_x, 7.5+shift_x], [8, 11], 'k--', lw=1)

ax.add_patch(patches.Circle((5.25+shift_x, 5), 0.5, facecolor='white', ec='black', lw=1.5))
ax.text(5.25+shift_x, 5, "$Na^+$", fontsize=11, ha='center', va='center', fontweight='bold')
ax.annotate("Charge", xy=(4.7, 6.5), xytext=(5.8, 6.5), arrowprops=dict(arrowstyle="<-", color='black', lw=1.5))
ax.annotate("Discharge", xy=(5.8, 3.5), xytext=(4.7, 3.5), arrowprops=dict(arrowstyle="<-", color='black', lw=1.5))

ax.text(5+shift_x, 0.5, "Electrolyte physics included with resolution\nacross length of the electrode, Na-ion\nconcentration solved only across particle domain.", fontsize=12, ha='center')


# --- 3. DFN (Doyle-Fuller-Newman) ---
shift_x2 = 20
ax.text(5.5+shift_x2, 20.5, "DFN", fontsize=16, fontweight='bold', ha='center')
# Electrode 1D domain
ax.add_patch(patches.Rectangle((1+shift_x2, 18), 3.5, 1.8, facecolor='lightblue', ec='none'))
ax.add_patch(patches.Rectangle((4.5+shift_x2, 18), 2, 1.8, facecolor='saddlebrown', ec='none', alpha=0.9))
ax.add_patch(patches.Rectangle((6.5+shift_x2, 18), 3.5, 1.8, facecolor='lightblue', ec='none'))
ax.add_patch(patches.Rectangle((1+shift_x2, 18), 9, 1.8, fill=False, ec='black', lw=1.5))

ax.annotate("", xy=(1+shift_x2, 20), xytext=(10+shift_x2, 20), arrowprops=dict(arrowstyle="<->", color='black', lw=1.5))
ax.text(5.5+shift_x2, 20.3, "L", fontsize=13, ha='center')
ax.text(2.7+shift_x2, 17.5, "Negative electrode", fontsize=11, ha='center')
ax.text(5.5+shift_x2, 17.5, "Separator", fontsize=11, ha='center')
ax.text(8.3+shift_x2, 17.5, "Positive electrode", fontsize=11, ha='center')

# draw small particles
for i in range(5):
    ax.add_patch(patches.Circle((1.5+shift_x2 + i*0.6, 18.9), 0.45, color='dimgray', ec='black'))
    ax.add_patch(patches.Circle((7.1+shift_x2 + i*0.6, 18.9), 0.45, color='royalblue', ec='black'))

# Expanded particles
ax.add_patch(patches.Circle((3+shift_x2, 11), 2.2, color='dimgray', ec='black', lw=2))  
ax.add_patch(patches.Circle((8.5+shift_x2, 11), 2.2, color='royalblue', ec='black', lw=2)) 
ax.text(3+shift_x2, 13.8, "Negative electrode particle", fontsize=11, ha='center')
ax.text(8.5+shift_x2, 13.8, "Positive electrode particle", fontsize=11, ha='center')
ax.text(3+shift_x2, 11.2, "$R_n$", fontsize=13)
ax.text(8.5+shift_x2, 11.2, "$R_p$", fontsize=13)

# Dotted lines
ax.plot([3+shift_x2, 2.1+shift_x2], [13.2, 18.4], 'k--', lw=1)
ax.plot([3+shift_x2, 3.9+shift_x2], [13.2, 18.4], 'k--', lw=1)
ax.plot([8.5+shift_x2, 7.1+shift_x2], [13.2, 18.4], 'k--', lw=1)
ax.plot([8.5+shift_x2, 8.9+shift_x2], [13.2, 18.4], 'k--', lw=1)

ax.add_patch(patches.Circle((5.75+shift_x2, 9.5), 0.5, facecolor='white', ec='black', lw=1.5))
ax.text(5.75+shift_x2, 9.5, "$Na^+$", fontsize=11, ha='center', va='center', fontweight='bold')
ax.annotate("Charge", xy=(5.2, 11), xytext=(6.3, 11), arrowprops=dict(arrowstyle="<-", color='black', lw=1.5))
ax.annotate("Discharge", xy=(6.3, 8), xytext=(5.2, 8), arrowprops=dict(arrowstyle="<-", color='black', lw=1.5))

ax.text(5.75+shift_x2, 3.5, "Electrolyte physics included with\nresolution across length of electrode,\nNa-ion concentration solved along\nparticle domain as well as over electrode length.", fontsize=12, ha='center')

plt.tight_layout()
plt.savefig("battery_models_high_res.png", dpi=300, bbox_inches='tight')
plt.savefig("battery_models_vector.svg", bbox_inches='tight')
print("이미지 생성 완료: battery_models_high_res.png, battery_models_vector.svg")
