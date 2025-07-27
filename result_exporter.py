import os

def export_result_html(title, vote_counts, total_count, labels, filename=None, mode="niconico"):
    if filename is None:
        result_dir = os.path.abspath("result")
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)
        filename = os.path.join(result_dir, "result.html")
    # 统计逻辑：niconico模式下，第一项为“总人数减去2-5项之和”，其余为原始票数
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
        <meta charset=\"utf-8\">
        <title>{title}</title>
        <style>
            body {{ background: #f7f7f7; font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; }}
            .container {{ max-width: 900px; margin: 40px auto; background: #fff; border-radius: 16px; box-shadow: 0 2px 16px #0001; padding: 32px; }}
            .title {{ font-size: 2.2em; font-weight: bold; margin-bottom: 24px; text-align: center; }}
            .cards {{ display: flex; flex-wrap: wrap; justify-content: space-around; margin-top: 32px; }}
            .card {{ width: 180px; height: 120px; background: #4FC3F7; border-radius: 16px; margin: 12px; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 2px 8px #0002; }}
            .percent {{ font-size: 2.2em; font-weight: bold; color: #FFD700; margin-bottom: 8px; }}
            .label {{ font-size: 1.1em; color: #222; }}
            .total {{ text-align: center; font-size: 1.2em; margin-top: 24px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class=\"container\">
            <div class=\"title\">{title}</div>
            <div class=\"cards\">
    """
    for i in range(5):
        percent = (counts[i] / max(sum_votes, 1) * 100) if sum_votes else 0
        html += f"""
            <div class=\"card\">
                <div class=\"percent\">{percent:.1f}%</div>
                <div class=\"label\">{labels[i]}</div>
            </div>
        """
    html += f"""
            </div>
            <div class=\"total\">总票数: {sum_votes}</div>
            <div class=\"total\">实际投票票数: {sum_raw_votes}</div>
        </div>
    </body>
    </html>
    """
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html) 