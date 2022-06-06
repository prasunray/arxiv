
import numpy as np
import json
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from tqdm import tqdm

from plot_utils import (
    load_records,
    load_authors,
    load_metadata,
    get_decimal_date,
    unique_ify,
    in_a_not_appeared_before_in_b
)

matplotlib.style.use("matplotlibrc.paper")

try:
    records, authors, metadata
except NameError:
    records = load_records()
    authors = load_authors()
    metadata = load_metadata()

else:
    print("WARNING: Using pre-loaded records.")


ignore_ppcs = [
    "eess", "econ", # These don't go back far enough
    # These have ~zero instances throughout time:
    "astro-ph",
    "cond-mat", "gr-qc", "hep-ex", "hep-lat", "hep-ph", "hep-th",
    "math-ph", "nlin", "nucl-ex", "nucl-th",
    "quant-ph",
    "math"
]

ppcs = sorted(list(set(records["primary_parent_category"]).difference(ignore_ppcs)))

bin_max = max(records["created_decimal_year"])

bins = np.arange(2011, bin_max, 1/12)
counts = {}
totals = {}

patterns = ("pandemic", "covid", "sars-cov-2", "lockdown", "coronavirus")

q_bio_2020_ids = []

for ppc in ppcs:
    print(ppc)

    counts[ppc] = np.zeros_like(bins)
    totals[ppc] = np.zeros_like(bins)
    
    mask = (records["primary_parent_category"] == ppc)

    for arxiv_id in tqdm(records["id"][mask]):
        date = get_decimal_date(arxiv_id)
        if date < bins[0] or date > bins[-1]:
            continue

        idx = np.digitize(date, bins)
        totals[ppc][idx] += 1

        md = metadata[arxiv_id]
        context = f"{md['title']} {md['abstract']}".lower()
        for pattern in patterns:
            if pattern in context:
                counts[ppc][idx] += 1
                if ppc == "q-bio" and date > 2020 and date < 2021:
                    q_bio_2020_ids.append(arxiv_id)
                break


    in_2020 = (2021 > bins) * (bins >= 2020)
    prev_decade = (2020 > bins) * (bins >= 2010)
    print(f"{ppc}: {np.sum(counts[ppc][in_2020]):.0f} in 2020, {np.sum(counts[ppc][prev_decade]):.0f} in previous decade")

xlim = (2017, bins[-1])

fig, axes = plt.subplots(1, 2, figsize=(9, 5))

from matplotlib.cm import Dark2 as cmap

colors = [cmap(i) for i in range(len(ppcs))]
colors = """
#000000
#264653
#2A9D8F
#E9C46A
#E76F51
""".split()

labels = {
    "cs": "Computer science",
    "physics": "Physics",
    "q-bio": "Quantitative biology",
    "q-fin": "Quantitative finance",
    "stat": "Statistics"
}
#F4A261

for color, ppc in zip(colors, ppcs):
    axes[0].plot(
        bins,
        counts[ppc],
        drawstyle="steps-mid",
        label=r"$\textrm{{{0}}}$ $(\textrm{{{1}}})$".format(labels[ppc].replace(" ", "~"), ppc),
        c=color
    )

    axes[1].plot(
        bins,
        100 * counts[ppc] / totals[ppc],
        drawstyle="steps-mid",
        c=color
    )

axes[0].legend(
    loc="upper left", 
    frameon=False
)
axes[0].set_ylabel(r"$\textrm{Pre}$-$\textrm{prints~with~pandemic~keywords~per~month}$")
axes[1].set_ylabel(r"$\textrm{Percent~of~pre}$-$\textrm{prints~with~pandemic~keywords~per~month}$")

for ax in axes.flat:
    ax.axhline(0, c="#666666", lw=1, ls=":", zorder=-1)
    '''
    ax.axvspan(
        2020,
        xlim[1],
        facecolor="#DDDDDD",
        edgecolor=None,
        zorder=-1
    )
    '''
    ax.set_xlim(*xlim)

axes[1].set_xlabel(r"$\textrm{Year}$")
fig.tight_layout()
fig.savefig("article/pandemic-related-preprints.pdf", dpi=300)