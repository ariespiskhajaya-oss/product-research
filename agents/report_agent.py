"""
Report Agent - Handles report formatting
Responsibility: Format and structure final output as HTML
"""

import re
from datetime import datetime
from pathlib import Path


class ReportAgent:
    def __init__(self):
        self.output_dir = Path(__file__).parent.parent / "output"
        self.output_dir.mkdir(exist_ok=True)

    def format(self, product_name: str, analysis: str) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        safe_name = product_name.lower().replace(" ", "_").replace("/", "_")
        filename = f"report_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        html = self._build_html(product_name, timestamp, analysis)

        filepath = self.output_dir / filename
        filepath.write_text(html, encoding="utf-8")

        return str(filepath)

    def _build_html(self, product_name: str, timestamp: str, analysis: str) -> str:
        content_html = self._markdown_to_html(analysis)

        return f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Riset: {product_name}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #2563eb;
            --primary-light: #3b82f6;
            --primary-dark: #1d4ed8;
            --accent: #7c3aed;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --gray-50: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-300: #d1d5db;
            --gray-400: #9ca3af;
            --gray-500: #6b7280;
            --gray-600: #4b5563;
            --gray-700: #374151;
            --gray-800: #1f2937;
            --gray-900: #111827;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.7;
            color: var(--gray-800);
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 960px;
            margin: 0 auto;
        }}

        .report-card {{
            background: white;
            border-radius: 20px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
            color: white;
            padding: 40px;
            position: relative;
            overflow: hidden;
        }}

        .header::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 100%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        }}

        .header h1 {{
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 12px;
            position: relative;
            letter-spacing: -0.5px;
        }}

        .header .meta {{
            font-size: 14px;
            opacity: 0.9;
            position: relative;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}

        .header .meta span {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .content {{
            padding: 40px;
        }}

        h1 {{
            font-size: 28px;
            font-weight: 700;
            color: var(--gray-900);
            margin: 30px 0 20px;
            padding-bottom: 12px;
            border-bottom: 3px solid var(--primary);
            letter-spacing: -0.3px;
        }}

        h2 {{
            font-size: 22px;
            font-weight: 600;
            color: var(--gray-800);
            margin: 30px 0 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        h2::before {{
            content: '';
            width: 4px;
            height: 24px;
            background: linear-gradient(180deg, var(--primary), var(--accent));
            border-radius: 2px;
        }}

        h3 {{
            font-size: 18px;
            font-weight: 600;
            color: var(--gray-700);
            margin: 24px 0 12px;
        }}

        h4 {{
            font-size: 16px;
            font-weight: 600;
            color: var(--gray-600);
            margin: 20px 0 10px;
        }}

        p {{
            margin: 12px 0;
            color: var(--gray-700);
        }}

        ul, ol {{
            margin: 12px 0;
            padding-left: 24px;
        }}

        li {{
            margin: 8px 0;
            color: var(--gray-700);
        }}

        li::marker {{
            color: var(--primary);
        }}

        table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin: 20px 0;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}

        th {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            font-weight: 600;
            text-align: left;
            padding: 14px 16px;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        td {{
            padding: 14px 16px;
            border-bottom: 1px solid var(--gray-200);
            font-size: 14px;
        }}

        tr:last-child td {{
            border-bottom: none;
        }}

        tr:nth-child(even) {{
            background: var(--gray-50);
        }}

        tr:hover {{
            background: var(--gray-100);
        }}

        code {{
            background: var(--gray-100);
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 13px;
            font-family: 'JetBrains Mono', monospace;
            color: var(--primary-dark);
        }}

        pre {{
            background: var(--gray-900);
            color: #e5e7eb;
            padding: 20px;
            border-radius: 12px;
            overflow-x: auto;
            margin: 20px 0;
        }}

        pre code {{
            background: none;
            padding: 0;
            color: inherit;
            font-size: 14px;
        }}

        blockquote {{
            border-left: 4px solid var(--primary);
            margin: 20px 0;
            padding: 16px 24px;
            background: linear-gradient(90deg, var(--gray-50) 0%, white 100%);
            border-radius: 0 8px 8px 0;
        }}

        strong {{
            color: var(--gray-900);
            font-weight: 600;
        }}

        a {{
            color: var(--primary);
            text-decoration: none;
            font-weight: 500;
        }}

        a:hover {{
            text-decoration: underline;
        }}

        .section {{
            margin-bottom: 32px;
            padding-bottom: 32px;
            border-bottom: 1px solid var(--gray-200);
        }}

        .section:last-child {{
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .badge-success {{
            background: #d1fae5;
            color: #065f46;
        }}

        .badge-warning {{
            background: #fef3c7;
            color: #92400e;
        }}

        .badge-danger {{
            background: #fee2e2;
            color: #991b1b;
        }}

        .footer {{
            text-align: center;
            padding: 24px 40px;
            background: var(--gray-50);
            border-top: 1px solid var(--gray-200);
        }}

        .footer p {{
            color: var(--gray-500);
            font-size: 13px;
            margin: 0;
        }}

        @media (max-width: 640px) {{
            .header {{
                padding: 24px;
            }}
            .header h1 {{
                font-size: 24px;
            }}
            .content {{
                padding: 24px;
            }}
            table {{
                font-size: 12px;
            }}
            th, td {{
                padding: 10px 8px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="report-card">
            <div class="header">
                <h1>🔍 {product_name}</h1>
                <div class="meta">
                    <span>📅 {timestamp}</span>
                    <span>🤖 Multi-Agent Research System</span>
                    <span>📊 7 Agents Parallel</span>
                </div>
            </div>
            <div class="content">
                {content_html}
            </div>
            <div class="footer">
                <p>Generated by Multi-Agent LFP Research System • Powered by Tavily + OpenAI</p>
            </div>
        </div>
    </div>
</body>
</html>"""

    def _markdown_to_html(self, md: str) -> str:
        html = md

        # Headers
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

        # Bold and italic
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

        # Code blocks
        html = re.sub(r'```(\w*)\n(.*?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)

        # Inline code
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)

        # Lists
        lines = html.split('\n')
        in_ul = False
        in_ol = False
        result = []

        for line in lines:
            stripped = line.strip()

            if re.match(r'^[-•] ', stripped):
                if not in_ul:
                    if in_ol:
                        result.append('</ol>')
                        in_ol = False
                    result.append('<ul>')
                    in_ul = True
                content = re.sub(r'^[-•] ', '', stripped)
                result.append(f'<li>{content}</li>')
            elif re.match(r'^\d+\. ', stripped):
                if not in_ol:
                    if in_ul:
                        result.append('</ul>')
                        in_ul = False
                    result.append('<ol>')
                    in_ol = True
                content = re.sub(r'^\d+\. ', '', stripped)
                result.append(f'<li>{content}</li>')
            else:
                if in_ul:
                    result.append('</ul>')
                    in_ul = False
                if in_ol:
                    result.append('</ol>')
                    in_ol = False
                result.append(line)

        if in_ul:
            result.append('</ul>')
        if in_ol:
            result.append('</ol>')

        html = '\n'.join(result)

        # Tables
        table_pattern = r'\|(.+)\|\n\|[-| ]+\|\n((?:\|.+\|\n?)+)'
        def replace_table(match):
            headers = [h.strip() for h in match.group(1).split('|') if h.strip()]
            rows = match.group(2).strip().split('\n')
            thead = '<thead><tr>' + ''.join(f'<th>{h}</th>' for h in headers) + '</tr></thead>'
            tbody = '<tbody>'
            for row in rows:
                cells = [c.strip() for c in row.split('|') if c.strip()]
                tbody += '<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>'
            tbody += '</tbody>'
            return f'<table>{thead}{tbody}</table>'
        html = re.sub(table_pattern, replace_table, html)

        # Paragraphs
        html = re.sub(r'\n\n+', '\n', html)
        paragraphs = html.split('\n')
        result = []
        for p in paragraphs:
            p = p.strip()
            if p and not p.startswith('<'):
                result.append(f'<p>{p}</p>')
            elif p:
                result.append(p)
        html = '\n'.join(result)

        # Clean up empty tags
        html = re.sub(r'<p></p>', '', html)
        html = re.sub(r'<p>\s*</p>', '', html)
        html = re.sub(r'\n{3,}', '\n\n', html)

        return html
