import os
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

DEFAULT_SHEET_ID = os.environ.get('WORLD_CUP_SHEET_ID') or '110V6txY9pnkPZwS2ZX0FJMvrBP2KuqPU475dmfr2uyA'

FLAG_MAP = {
    'Mexico': '🇲🇽',
    'South Korea': '🇰🇷',
    'South Africa': '🇿🇦',
    'Czechia': '🇨🇿',
    'Canada': '🇨🇦',
    'Switzerland': '🇨🇭',
    'Qatar': '🇶🇦',
    'Bosnia': '🇧🇦',
    'Brazil': '🇧🇷',
    'Morocco': '🇲🇦',
    'Scotland': '\U0001F3F4\U000E0067\U000E0062\U000E0073\U000E0063\U000E0074\U000E007F',
    'Haiti': '🇭🇹',
    'USA': '🇺🇸',
    'Australia': '🇦🇺',
    'Paraguay': '🇵🇾',
    'Turkey': '🇹🇷',
    'Germany': '🇩🇪',
    'Ecuador': '🇪🇨',
    'Ivory Coast': '🇨🇮',
    'Curacao': '🇨🇼',
    'Netherlands': '🇳🇱',
    'Japan': '🇯🇵',
    'Tunisia': '🇹🇳',
    'Sweden': '🇸🇪',
    'Belgium': '🇧🇪',
    'Egypt': '🇪🇬',
    'Iran': '🇮🇷',
    'New Zealand': '🇳🇿',
    'Spain': '🇪🇸',
    'Uruguay': '🇺🇾',
    'Saudi Arabia': '🇸🇦',
    'Cape Verde': '🇨🇻',
    'France': '🇫🇷',
    'Senegal': '🇸🇳',
    'Norway': '🇳🇴',
    'Iraq': '🇮🇶',
    'Argentina': '🇦🇷',
    'Austria': '🇦🇹',
    'Algeria': '🇩🇿',
    'Jordan': '🇯🇴',
    'Portugal': '🇵🇹',
    'Colombia': '🇨🇴',
    'Uzbekistan': '🇺🇿',
    'Congo': '🇨🇩',
    'England': '\U0001F3F4\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F',
    'Croatia': '🇭🇷',
    'Panama': '🇵🇦',
    'Ghana': '🇬🇭',
}

round_cols = ['Group stage', 'R32', 'R16', 'QF', 'SF', 'F']


def build_sheet_url(sheet_id: str) -> str:
    return f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx'


def load_pool_data(sheet_id: str = DEFAULT_SHEET_ID):
    sheet_url = build_sheet_url(sheet_id)
    entries_df = pd.read_excel(sheet_url, sheet_name='Entries')
    countries_df = pd.read_excel(sheet_url, sheet_name='Countries')

    entries_df = entries_df.map(lambda x: x.strip() if isinstance(x, str) else x)

    round_scores = countries_df[round_cols].apply(pd.to_numeric, errors='coerce')
    countries_df['total_points'] = round_scores.sum(axis=1, min_count=1)
    countries_df['alive'] = countries_df['Eliminated'].fillna(0).astype(int).eq(0)

    return entries_df, countries_df


def flag_with_tooltip(country: str) -> str:
    flag = FLAG_MAP.get(country, country)
    return f'<span class="flag tooltip" data-tooltip="{country}">{flag}</span>'


def generate_report_html(sheet_id: str = DEFAULT_SHEET_ID) -> str:
    entries_df, countries_df = load_pool_data(sheet_id)

    player_rows = []
    country_points = countries_df.set_index('Country')['total_points'].fillna(0).to_dict()

    for player in entries_df.columns:
        picks = entries_df[player].dropna().astype(str).tolist()
        total = sum(country_points.get(country, 0) for country in picks)
        teams_remaining = sum(countries_df[countries_df['Country'].isin(picks)]['alive'])
        remaining_flags = []
        eliminated_flags = []

        for country in picks:
            tooltip_flag = flag_with_tooltip(country)
            if countries_df.loc[countries_df['Country'] == country, 'alive'].any():
                remaining_flags.append(tooltip_flag)
            else:
                eliminated_flags.append(tooltip_flag)

        remaining_label = '<span class="pick-group-label tooltip" data-tooltip="Remaining countries">✅</span>'
        eliminated_label = '<span class="pick-group-label tooltip" data-tooltip="Eliminated countries">❌</span>'

        # Build picks with remaining on the first line and eliminated on the second (if present)
        picks_lines = []
        if remaining_flags:
            picks_lines.append(f"{remaining_label} {' '.join(remaining_flags)}")
        if eliminated_flags:
            # only show eliminated label/flags if any eliminated teams exist
            picks_lines.append(f"{eliminated_label} {' '.join(eliminated_flags)}")

        # join with a line break so the two groups appear on separate lines in the table cell
        picks = '<br/>'.join(picks_lines)

        player_rows.append({
            'Player': player,
            'Picks': picks,
            'Remaining': f"{teams_remaining} / 12",
            'Remaining count': teams_remaining,
            'Total points': int(total),
        })

    player_report = pd.DataFrame(player_rows).sort_values(
        by=['Total points', 'Remaining count'],
        ascending=[False, False]
    ).drop(columns=['Remaining count'])

    player_report['Total points'] = player_report['Total points'].apply(
        lambda v: f"<strong>{v}</strong>"
    )

    country_report = countries_df[['Country', 'Group', 'Pot', 'Eliminated'] + round_cols + ['total_points']].rename(
        columns={'Country': 'Country', 'Group': 'Group', 'Pot': 'Pot', 'total_points': 'Total points'}
    )

    # Sort by Total points (desc), then Group (asc), then Pot (asc) for tie-breaking
    country_report = country_report.sort_values(
        by=['Total points', 'Group', 'Pot'],
        ascending=[False, True, True],
        na_position='last'
    )

    country_report['Country'] = country_report['Country'].apply(
        lambda name: f"{FLAG_MAP.get(name, '')} {name}" if pd.notna(name) else name
    )

    for col in round_cols:
        country_report[col] = country_report[col].apply(
            lambda v: '' if pd.isna(v) else int(v)
        )

    country_report['Total points'] = country_report['Total points'].apply(
        lambda v: '' if pd.isna(v) else f"<strong>{int(v)}</strong>"
    )

    for col in ['Country', 'Group', 'Pot', 'Total points'] + round_cols:
        country_report[col] = country_report.apply(
            lambda row: f"<span style='color:#999;'>{row[col]}</span>" if row['Eliminated'] == 1 else row[col],
            axis=1,
        )

    country_report = country_report.drop(columns=['Eliminated'])

    player_html = player_report.to_html(index=False, escape=False, classes='report-table player-table')
    country_html = country_report.to_html(index=False, escape=False, classes='report-table country-table')

    # timestamp for when this report was generated (North American Eastern Time)
    timestamp = datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m-%d %H:%M %Z')

    html = f"""
<html>
<head>
  <meta charset="utf-8">
  <title>World Cup Pool Standings</title>
  <style>
    body {{ font-family: Inter, Arial, sans-serif; background: #f5f7fb; color: #111; margin: 0; padding: 24px; }}
    h1 {{ margin-top: 0; font-size: 2rem; color: #111; }}
    h2 {{ margin-bottom: 12px; color: #1f2937; }}
    .report-table {{ border-collapse: collapse; width: 100%; margin-bottom: 32px; background: #fff; box-shadow: 0 1px 4px rgba(15, 23, 42, 0.08); }}
    .report-table th, .report-table td {{ border: 1px solid #e2e8f0; padding: 12px 14px; text-align: left; }}
    .report-table th {{ background: #111827; color: #f9fafb; position: sticky; top: 0; z-index: 1; }}
    .report-table tr:nth-child(even) td {{ background: #f8fafc; }}
    .report-table tr:hover td {{ background: #eef2ff; }}
    .report-table caption {{ font-size: 1.2em; margin-bottom: 10px; font-weight: 700; text-align: left; caption-side: top; }}
    .flag {{
      position: relative;
      display: inline-block;
      margin-right: 4px;
      cursor: default;
      font-size: 16px;
      line-height: 1;
    }}
    .pick-group-label {{
      position: relative;
      display: inline-block;
      padding: 0;
      color: #111827;
      font-weight: 700;
      margin-right: 6px;
      cursor: default;
      line-height: 1;
    }}
    .tooltip::after {{
      content: attr(data-tooltip);
      position: absolute;
      left: 50%;
      bottom: 100%;
      transform: translate(-50%, -8px);
      white-space: nowrap;
      background: rgba(15, 23, 42, 0.92);
      color: #fff;
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 0.8em;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.15s ease, transform 0.15s ease;
      z-index: 2;
    }}
    .tooltip:hover::after {{
      opacity: 1;
      transform: translate(-50%, -12px);
    }}
    .player-table th:nth-child(2), .player-table td:nth-child(2) {{ min-width: 240px; }}
    .player-table th:nth-child(3), .player-table td:nth-child(3) {{ width: 120px; }}
    .player-table th:nth-child(4), .player-table td:nth-child(4) {{ width: 120px; }}
        .updated {{ font-size: 0.9em; color: #666; margin-top: 12px; }}
        </style>
</head>
<body>
  <h1>World Cup Pool Standings</h1>
  <h2>Player standings</h2>
  {player_html}
  <h2>Country points</h2>
  {country_html}
    <div class="updated">Last updated: {timestamp}</div>
</body>
</html>
"""

    return html


def write_report(output_file: str = 'world_cup_pool.html', sheet_id: str = DEFAULT_SHEET_ID):
    html = generate_report_html(sheet_id)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Report written to {output_file}')


if __name__ == '__main__':
    write_report()
