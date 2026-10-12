#!/usr/bin/env python3
"""Build `Barsa.Ai.Host.exe.config` from a working Barsa installation.

The host needs two unrelated groups of settings in one file. The `AiHost.*`
keys are its own, and this script writes them. The rest -- `DBProvider`,
`DBConnectionString`, `RemotingUsage`, `RemotingUrl` -- belong to Barsa, and
cannot be written by hand: `DBConnectionString` carries a block-encrypted
payload that only Barsa can mint, and a hand-copied one is the single most
likely thing to go wrong, because it is hundreds of characters of
hyphen-separated hex that must survive a copy and an XML escape intact.

So this script does not ask anyone to retype it. It reads the config of an
application in a Barsa installation that already connects on this machine,
carries those keys across verbatim, and checks the result parses back to the
same bytes it copied.

It never prints a connection string. A value that reaches a terminal reaches
a scrollback buffer, and this one is a database credential.
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import quoteattr

# Barsa's own keys, carried across rather than authored. RemotingUrl matters
# only when RemotingUsage is a client, but it is copied whenever present so
# that a client install keeps working.
BARSA_KEYS = ("DBProvider", "DBConnectionString", "RemotingUsage",
              "RemotingUrl", "CacheEnabled", "CenterId")
REQUIRED = ("DBConnectionString",)

AI_DEFAULTS = (
    ("AiHost.HttpPrefix", "http://127.0.0.1:17840/",
     "آدرسی که HttpListener رویش می‌نشیند. حتماً با / تمام شود."),
    ("AiHost.ApiKey", "",
     "خالی بماند احراز هویت کاملاً غیرفعال است: IsAuthorized وقتی کلید "
     "خالی باشد true برمی‌گرداند."),
    ("AiHost.UserName", "LocalAccount",
     "کاربری که host با آن به بارسا login می‌کند؛ باید اجازهٔ نوشتن "
     "متامدل داشته باشد."),
    ("AiHost.Password", "",
     "خالی‌گذاشتن یعنی پیش‌فرض کد («كاربر محلي سكو»)، نه پسورد خالی."),
    ("AiHost.WorkspaceRoot", "",
     "پوشهٔ کاری host. بیرون مخزن گیت بگذارش."),
    ("AiHost.RemoveSecurityAccess", "false", None),
    ("AiHost.MetadataPackageWatcher.Enabled", "false",
     "برای مسیر کانبان لازم نیست."),
    ("AiHost.ChatBridge.Enabled", "false", None),
)


def read_app_settings(path):
    """Every appSettings key of a .NET config, as a dict."""
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise SystemExit("خواندن %s ناموفق: %s" % (path, exc))
    out = {}
    for add in root.findall("./appSettings/add"):
        key = add.get("key")
        if key is not None:
            out[key] = add.get("value") or ""
    return out


def describe(value):
    """Say what a connection string looks like without showing it."""
    parts = value.split("%")
    if len(parts) != 3:
        return ("%d بخش (انتظار ۳) — این مقدار شکل یک رشتهٔ اتصال بارسا "
                "را ندارد" % len(parts))
    head, version, payload = (p.strip() for p in parts)
    octets = [o for o in payload.split("-") if o]
    return "%s | نسخهٔ فرمت %s | payload %d بایت" % (
        head or "(بی‌سر)", version or "(بی‌نسخه)", len(octets))


def build(ai_settings, barsa):
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        "<!--",
        "  ساخته‌شده با tools/make_host_config.py",
        "",
        "  کلیدهای AiHost.* را این اسکریپت نوشته و شما باید بازبینی‌شان",
        "  کنید. کلیدهای بارسا از یک نصب کارکرده روی همین ماشین عیناً کپی",
        "  شده‌اند و دست‌کاری‌شان نکنید: DBConnectionString یک payload",
        "  رمزشده دارد که فقط خودِ بارسا می‌تواند بسازد.",
        "",
        "  این فایل پسورد دیتابیس دارد. کامیتش نکنید.",
        "-->",
        "<configuration>",
        "  <appSettings>",
        "",
        "    <!-- از نصب بارسا کپی شد. دست نزنید. -->",
    ]
    for key in BARSA_KEYS:
        if key in barsa:
            lines.append('    <add key=%s value=%s />'
                         % (quoteattr(key), quoteattr(barsa[key])))
    lines += ["", "    <!-- کلیدهای خودِ host. -->"]
    for key, value, note in ai_settings:
        if note:
            lines.append("    <!-- %s -->" % note)
        lines.append('    <add key=%s value=%s />'
                     % (quoteattr(key), quoteattr(value)))
    lines += ["", "  </appSettings>", "</configuration>", ""]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="ساخت Barsa.Ai.Host.exe.config از یک نصب بارسای کارکرده")
    ap.add_argument("--from", dest="source", required=True,
                    help="config یک برنامهٔ بارسا که روی همین ماشین وصل "
                         "می‌شود، مثلاً Barsa.Eorg.Ui.Win.exe.config")
    ap.add_argument("--out", required=True,
                    help="مسیر خروجی، کنار Barsa.Ai.Host.exe")
    ap.add_argument("--api-key", default=None,
                    help="AiHost.ApiKey. ندهید، خالی می‌ماند و احراز هویت "
                         "غیرفعال است.")
    ap.add_argument("--user", default=None, help="AiHost.UserName")
    ap.add_argument("--password", default=None, help="AiHost.Password")
    ap.add_argument("--workspace", default=None,
                    help="AiHost.WorkspaceRoot — بیرون مخزن گیت")
    ap.add_argument("--prefix", default=None, help="AiHost.HttpPrefix")
    ap.add_argument("--force", action="store_true",
                    help="رونویسی فایل موجود")
    args = ap.parse_args(argv)

    barsa_all = read_app_settings(args.source)
    carried = {k: v for k, v in barsa_all.items()
               if k in BARSA_KEYS and v.strip()}

    missing = [k for k in REQUIRED if k not in carried]
    if missing:
        raise SystemExit(
            "در %s این کلید(ها) نبود یا خالی بود: %s\n"
            "یعنی این config به دیتابیس وصل نمی‌شود. config برنامه‌ای را "
            "بدهید که روی همین ماشین واقعاً بالا می‌آید."
            % (args.source, "، ".join(missing)))

    overrides = {"AiHost.ApiKey": args.api_key,
                 "AiHost.UserName": args.user,
                 "AiHost.Password": args.password,
                 "AiHost.WorkspaceRoot": args.workspace,
                 "AiHost.HttpPrefix": args.prefix}
    ai = [(k, overrides.get(k) if overrides.get(k) is not None else v, n)
          for k, v, n in AI_DEFAULTS]

    if os.path.exists(args.out) and not args.force:
        raise SystemExit("%s از قبل هست. --force بدهید تا رونویسی شود."
                         % args.out)

    text = build(ai, carried)
    with open(args.out, "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write(text)

    # Read it back and prove every carried value survived the XML escape.
    back = read_app_settings(args.out)
    for key, want in carried.items():
        if back.get(key) != want:
            os.unlink(args.out)
            raise SystemExit(
                "خروجی بازخوانی شد و %s با مقدار اصلی نخواند؛ فایل پاک شد."
                % key)

    print("نوشته شد: %s" % args.out)
    print("کلیدهای کپی‌شده از بارسا: %s" % "، ".join(sorted(carried)))
    print("  DBConnectionString → %s"
          % describe(carried["DBConnectionString"]))
    print("  (مقدارش چاپ نمی‌شود؛ اعتبارنامهٔ دیتابیس است.)")
    if not (overrides.get("AiHost.ApiKey") or "").strip():
        print("\nهشدار: AiHost.ApiKey خالی است. تا وقتی خالی باشد هر "
              "برنامه‌ای روی این ماشین می‌تواند POST /apply بزند.")
    ru = carried.get("RemotingUsage", "")
    if ru.lower() == "client" and "RemotingUrl" not in carried:
        print("\nهشدار: RemotingUsage=client است ولی RemotingUrl کپی نشد.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
