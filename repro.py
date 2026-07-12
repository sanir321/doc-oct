"""Reproduce the generate_ieee_html function locally - inline version."""

def generate_ieee_html(title, authors, abstract, sections, keywords, domain, references=None):
    """Copy of backend.main.generate_ieee_html"""
    authors_html = ""
    if authors:
        affil_map = {}
        counter = 1
        author_parts = []
        for a in authors:
            affil = a.get("affiliation", "")
            if affil:
                if affil not in affil_map:
                    affil_map[affil] = counter
                    counter += 1
                sup = f'<sup>{affil_map[affil]}</sup>'
            else:
                sup = ""
            author_parts.append(
                f'<div class="author">{a["name"]}{sup}<br><span class="affil">{affil}</span></div>'
            )
        authors_html = "".join(author_parts)

    sections_html = "".join(
        f'<div class="section"><h2>{s["title"]}</h2><p>{s["content"].replace(chr(10), "<br>")}</p></div>'
        for s in sections
    )
    keywords_str = ", ".join(keywords)

    refs_html = ""
    if references:
        ref_list = "\n".join(
            f'<p>[{i}] {r["citation"]}</p>' for i, r in enumerate(references, 1)
        )
        refs_html = f'<div class="references"><h2>References</h2>\n{ref_list}\n</div>'

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>{title}</title>
<style>
  @page {{ size: letter; margin: 0.75in 0.65in; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: "Times New Roman", Times, serif; font-size: 10pt; line-height: 1.15; color: #000; background: #fff; }}
  .paper {{ max-width: 7.5in; margin: 0 auto; }}
  h1 {{ font-size: 24pt; text-align: center; font-weight: bold; margin-bottom: 16px; font-family: "Times New Roman", Times, serif; letter-spacing: normal; }}
  .authors {{ text-align: center; font-size: 12pt; margin-bottom: 18px; font-family: "Times New Roman", Times, serif; }}
  .author {{ display: inline-block; margin: 0 16px; }}
  .affil {{ font-size: 10pt; font-style: italic; }}
  sup {{ font-size: 8pt; vertical-align: super; line-height: 1; }}
  .abstract {{ margin: 12px 0; padding: 0; }}
  .abstract-label {{ font-size: 10pt; font-weight: bold; font-style: italic; }}
  .abstract p {{ font-size: 10pt; font-weight: bold; font-style: italic; text-align: justify; display: inline; }}
  .kw-label {{ font-size: 10pt; font-weight: bold; font-style: italic; }}
  .keywords {{ font-size: 10pt; margin-bottom: 12px; font-style: italic; }}
  .content {{ column-count: 2; column-gap: 0.25in; }}
  .section {{ margin-bottom: 0; }}
  .section h2 {{ font-size: 10pt; font-variant: small-caps; font-weight: bold; text-align: left; margin: 12pt 0 6pt 0; font-family: "Times New Roman", Times, serif; letter-spacing: 0.5pt; }}
  .section h3 {{ font-size: 10pt; font-style: italic; font-weight: normal; text-align: left; margin: 9pt 0 3pt 0; font-family: "Times New Roman", Times, serif; }}
  .section p {{ text-align: justify; text-indent: 0.17in; margin-bottom: 0; line-height: 1.15; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 9pt; margin: 8px 0; }}
  th, td {{ border: 0.5pt solid black; padding: 3px 6px; text-align: center; }}
  .references {{ margin-top: 12px; }}
  .references h2 {{ font-size: 10pt; font-variant: small-caps; font-weight: bold; text-align: left; margin: 12pt 0 6pt 0; font-family: "Times New Roman", Times, serif; }}
  .references p {{ font-size: 9pt; margin-left: 0.25in; text-indent: -0.25in; line-height: 1.15; margin-bottom: 6pt; text-align: left; }}
  @media print {{ body {{ padding: 0; }} }}
</style></head><body>
<div class="paper">
  <h1>{title}</h1>
  <div class="authors">{authors_html}</div>
  <div class="abstract"><span class="abstract-label">Abstract — </span><p>{abstract}</p></div>
  <div class="keywords"><span class="kw-label">Index Terms — </span>{keywords_str}</div>
  <div class="content">{sections_html}</div>
  {refs_html}
</div>
</body></html>"""

# Test with actual data pattern
authors_data = [
    {"name": "Author A", "affiliation": "Department of Natural Language Processing / Machine Learning"},
    {"name": "Author B", "affiliation": "Department of Natural Language Processing / Machine Learning"},
]

html = generate_ieee_html(
    title="Test Paper",
    authors=authors_data,
    abstract="Test abstract here.",
    sections=[{"title": "Intro", "content": "Test content for the paper."}],
    keywords=["test", "keywords"],
    domain="Engineering",
    references=[{"citation": "J. Smith, test, 2023."}]
)

print("AUTHORS DIV:")
import re
au_div = re.search(r'<div class="authors">(.*?)</div>', html, re.DOTALL)
print(f"  Content: '{au_div.group(1) if au_div else 'NOT FOUND'}'")
print(f"  Has content: {bool(au_div and au_div.group(1).strip())}")

print("\nFull HTML preview:")
print(html[:600])
