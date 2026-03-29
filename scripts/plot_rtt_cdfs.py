# Re-run legend generation (two-column layout) after the environment reset
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

color_map = {
    'local':'purple',
    'diff_metro':'r',
    'same_region':'green',
    'neighboring_region':'brown',
    'non-neighboring_region':'blue',
}

label_map = {
    'local':'Local',
    'diff_metro':'Different Metro',
    'same_region':'Same Region',
    'neighboring_region':'Neighboring Region',
    'non-neighboring_region':'Non-Neighboring Region',
}

order = ['local','diff_metro','same_region','neighboring_region','non-neighboring_region']

handles = [
    Line2D([0],[0], linestyle='None', marker='o', markersize=6,
           markerfacecolor=color_map[k], markeredgecolor=color_map[k], label=label_map[k])
    for k in order
]

fig = plt.figure(figsize=(3.6, 1.6))
leg = fig.legend(
    handles=handles,
    loc="center",
    ncol=2,
    frameon=True,
    borderpad=0.8,
    labelspacing=0.6,
    columnspacing=1.8,
    handletextpad=0.6,
    markerscale=1.6
)
for text in leg.get_texts():
    text.set_fontweight('bold')
    text.set_fontsize(12)

plt.axis("off")

png_path = "graphs/shared_legend.png"
pdf_path = "graphs/shared_legend.pdf"
fig.savefig(png_path, dpi=300, bbox_inches="tight")
fig.savefig(pdf_path, bbox_inches="tight")

# legend=plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.32), ncol=2, frameon=True)


# 		legend.get_frame().set_linewidth(1.5)
# 		legend.get_frame().set_edgecolor('black')
# 		legend.get_frame().set_facecolor('white')

# 		for text in legend.get_texts():
# 			text.set_fontweight('bold')
# 			text.set_fontsize(20)

		