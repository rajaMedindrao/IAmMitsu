"""Usage: python add_google_verification.py [SITE_ROOT] [--ga-id UA-XXXX | --gtag-id G-YYYY]

Adds Google Search Console verification meta tag and optional Google Analytics
snippets to every HTML file under SITE_ROOT.

Requires: pip install beautifulsoup4
"""
import argparse
import os
from bs4 import BeautifulSoup

META_TAG = {
    "name": "google-site-verification",
    "content": "4O9wCPSJgDRQtkRsTu-t9NyclVhJYrdkTkz16eLssuY",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Inject Google verification and analytics tags into HTML files"
    )
    parser.add_argument(
        "site_root",
        nargs="?",
        default=".",
        help="Root directory of the static site",
    )
    parser.add_argument("--ga-id", help="Google Analytics UA property ID")
    parser.add_argument("--gtag-id", help="Google Analytics 4 measurement ID")
    return parser.parse_args()


def find_html_files(root):
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if name.lower().endswith(".html"):
                yield os.path.join(dirpath, name)


def has_ga_snippet(soup, ga_id):
    if soup.find("script", src="https://www.google-analytics.com/analytics.js"):
        return True
    return bool(
        soup.find(
            "script", string=lambda t: t and f"ga('create','{ga_id}'" in t
        )
    )


def has_gtag_snippet(soup, gtag_id):
    if soup.find(
        "script",
        src=f"https://www.googletagmanager.com/gtag/js?id={gtag_id}",
    ):
        return True
    return bool(
        soup.find(
            "script", string=lambda t: t and f"gtag('config','{gtag_id}'" in t
        )
    )


def main():
    args = parse_args()
    total = meta_added = ga_added = gtag_added = 0

    for html_file in find_html_files(args.site_root):
        total += 1
        with open(html_file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        head = soup.head
        if not head:
            head = soup.new_tag("head")
            if soup.html:
                soup.html.insert(0, head)
            else:
                soup.insert(0, head)

        changed = False

        if not soup.find("meta", attrs=META_TAG):
            meta_tag = soup.new_tag("meta", **META_TAG)
            head.insert(0, meta_tag)
            meta_added += 1
            changed = True

        if args.ga_id and not has_ga_snippet(soup, args.ga_id):
            script1 = soup.new_tag(
                "script",
                src="https://www.google-analytics.com/analytics.js",
            )
            script1["async"] = ""
            script2 = soup.new_tag("script")
            script2.string = (
                "window.ga=window.ga||function(){(ga.q=ga.q||[]).push(arguments)};"
                "ga.l=+new Date;ga('create','%s','auto');ga('send','pageview');" % args.ga_id
            )
            head.append(script1)
            head.append(script2)
            ga_added += 1
            changed = True

        if args.gtag_id and not has_gtag_snippet(soup, args.gtag_id):
            script1 = soup.new_tag(
                "script",
                src=f"https://www.googletagmanager.com/gtag/js?id={args.gtag_id}",
            )
            script1["async"] = ""
            script2 = soup.new_tag("script")
            script2.string = (
                "window.dataLayer=window.dataLayer||[];"
                "function gtag(){dataLayer.push(arguments);}"
                "gtag('js',new Date());gtag('config','%s');" % args.gtag_id
            )
            head.append(script1)
            head.append(script2)
            gtag_added += 1
            changed = True

        if changed:
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(str(soup))

    print(f"Scanned {total} HTML files")
    print(f"- added meta tag to {meta_added} file{'s' if meta_added!=1 else ''}")
    if args.ga_id:
        print(
            f"- added analytics.js snippet to {ga_added} file{'s' if ga_added!=1 else ''}"
        )
    if args.gtag_id:
        print(f"- added gtag snippet to {gtag_added} file{'s' if gtag_added!=1 else ''}")
    unchanged = total - meta_added - ga_added - gtag_added
    if unchanged:
        print(f"- no changes needed for {unchanged} file{'s' if unchanged!=1 else ''}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}")
        raise
