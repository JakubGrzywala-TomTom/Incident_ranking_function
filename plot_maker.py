from os.path import join, sep

import pandas as pd
from matplotlib.figure import Figure


def create_histogram(series: pd.Series,
                     cwd: str,
                     ranking_score_capping: float,
                     limit: int) -> None:
    series_max_boundary = 1
    series_min_boundary = round(series.min(), 1)
    num_of_messages = series.count()
    if series_min_boundary >= 0:
        bin_num = int((series_max_boundary + series_min_boundary) * 100)
    else:
        bin_num = int((series_max_boundary + abs(series_min_boundary)) * 100)
    bin_seq = []
    for x in range(bin_num-1):
        bin_seq.append(round(series_min_boundary, 2))
        series_min_boundary += 0.01

    fig = Figure(figsize=(18, 9), facecolor='#ffffff')
    ax = fig.add_subplot()
    ax.set_facecolor('#e5e5e5')
    ax.hist(series, bins=bin_seq, color="#61ade0", label="num of message scores in 0.01 bins")
    ax.grid(color='#000000', linestyle="--")
    ax.axvline(ranking_score_capping, color="#df1b12", linestyle="--", linewidth=3,
               label=f"capping value ({ranking_score_capping})")
    if limit <= num_of_messages:
        limit_score_value = series.iloc[limit]
        ax.axvline(limit_score_value, color="#fdc530", linestyle="--", linewidth=3,
                   label=f"limit from configuration file ({limit})"
                         f"\nscore of last message before the limit is ~ {round(limit_score_value, 3)}")
    ax.legend(loc='upper right', fontsize=10, shadow=True, facecolor='#ffffff')
    ax.set_title(f"Unfiltered messages ({num_of_messages}), sorted by ranking score, before using capping and limit",
                 fontsize=10)
    ax.set_xlabel("Ranking score", fontsize=10)
    ax.set_ylabel("Num of messages in 0.01 bins", fontsize=10)
    fig.savefig(join(cwd + sep + 'histogram.png'))
