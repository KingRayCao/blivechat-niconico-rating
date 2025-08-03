import os

def export_result_html(title, vote_counts, total_count, labels, filename=None, mode="niconico", include_repo=False):
    if filename is None:
        result_dir = os.path.abspath("result")
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)
        filename = os.path.join(result_dir, "result.html")

    sum_raw_votes = sum(vote_counts)
    if mode == "niconico":
        nico_counts = vote_counts.copy()
        nico_counts[0] = max(total_count - sum(nico_counts[1:]), 0)
        counts = nico_counts
    else:
        counts = vote_counts
    sum_votes = sum(counts)

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>{title}</title>
        <style>
            body {{
                background: #f7f7f7;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 1000px;
                margin: 40px auto;
                padding: 20px;
                text-align: center;
            }}
            .title {{
                font-size: 1.8em;
                margin-bottom: 30px;
                font-weight: bold;
                color: #000000;
                text-shadow: 0px 0px 4px #ffffff;
            }}
            .cards {{
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 40px 40px;
            }}
            .card {{
                position: relative;
                width: 200px;
                height: 120px;
                background: #ffffff;
                border: 3px solid #B0D9FF;
                border-radius: 16px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            .card-index {{
                position: absolute;
                top: -10px;
                left: -10px;
                width: 28px;
                height: 28px;
                background: #4FC3F7;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 1px 4px rgba(0,0,0,0.2);
            }}
            .percent-badge {{
                position: absolute;
                bottom: -20px;
                left: 50%;
                transform: translateX(-50%);
                background: black;
                padding: 4px 12px;
                border-radius: 12px;
                color: #FFD700;
                font-size: 20px;
                font-weight: bold;
            }}
            .label {{
                font-size: 20px;
                color: #222;
                font-weight: bold;
            }}
            .total {{
                margin-top: 40px;
                font-size: 1.1em;
                font-weight: bold;
                text-shadow: 0px 0px 1px #ffffff;
            }}
            .repo {{
                font-size: 0.85em;
                color: #888;
                margin-top: 10px;
                text-shadow: 0px 0px 1px #ffffff;
            }}
            .repo a {{
                color: #888;
                text-decoration: none;
                text-shadow: 0px 0px 1px #ffffff;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="title">{title}</div>
            <div class="cards">
    """
    for i in range(5):
        percent = (counts[i] / max(sum_votes, 1) * 100) if sum_votes else 0
        html += f"""
                <div class="card">
                    <div class="card-index">{i + 1}</div>
                    <div class="label">{labels[i]}</div>
                    <div class="percent-badge">{percent:.1f}%</div>
                </div>
        """
    html += f"""
            </div>
            <div class="total">总票数: {sum_votes} <br>实际投票票数: {sum_raw_votes}</div>
    """
    if include_repo:
        html += """
            <div class="repo">
                项目地址： <a href="https://github.com/KingRayCao/blivechat-niconico-rating" target="_blank">https://github.com/KingRayCao/blivechat-niconico-rating</a>
            </div>
        """
    html += """
        </div>
    </body>
    </html>
    """

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)