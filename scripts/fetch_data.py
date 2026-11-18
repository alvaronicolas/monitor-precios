"""Descarga series de precios desde fuentes públicas y las guarda en data/data.json.

Fuentes:
  - Jet Fuel: U.S. EIA (Energy Information Administration), spot U.S. Gulf Coast.
  - Petróleo Brent / WTI, Oro, Índice dólar (DXY): cotizaciones diarias de bolsa
    (ICE / NYMEX / COMEX) vía Yahoo Finance.
  - Dólar observado USD/CLP: Banco Central de Chile vía mindicador.cl.

Si una fuente falla, se conserva la serie anterior guardada (no se borra nada).
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "data.json")
YEARS = 5
UA = {"User-Agent": "Mozilla/5.0 (compatible; price-monitor/1.0)"}

SERIES = [
    {
        "id": "jetfuel", "name": "Jet Fuel", "detail": "Spot U.S. Gulf Coast (kerosene-type)",
        "unit": "USD/galón", "decimals": 3, "kind": "eia", "code": "EER_EPJK_PF4_RGC_DPG",
        "source": "U.S. Energy Information Administration (EIA)",
        "source_url": "https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=EER_EPJK_PF4_RGC_DPG&f=D",
        "note": "La EIA publica los datos diarios con ~1 semana de rezago (actualiza los miércoles).",
    },
    {
        "id": "brent", "name": "Petróleo Brent", "detail": "Futuro ICE, mes próximo",
        "unit": "USD/barril", "decimals": 2, "kind": "yahoo", "code": "BZ=F",
        "source": "ICE Futures Europe (vía Yahoo Finance)",
        "source_url": "https://finance.yahoo.com/quote/BZ%3DF/",
    },
    {
        "id": "wti", "name": "Petróleo WTI", "detail": "Futuro NYMEX, mes próximo",
        "unit": "USD/barril", "decimals": 2, "kind": "yahoo", "code": "CL=F",
        "source": "NYMEX / CME Group (vía Yahoo Finance)",
        "source_url": "https://finance.yahoo.com/quote/CL%3DF/",
    },
    {
        "id": "oro", "name": "Oro", "detail": "Futuro COMEX, mes próximo",
        "unit": "USD/onza troy", "decimals": 1, "kind": "yahoo", "code": "GC=F",
        "source": "COMEX / CME Group (vía Yahoo Finance)",
        "source_url": "https://finance.yahoo.com/quote/GC%3DF/",
    },
    {
        "id": "usdclp", "name": "Dólar observado", "detail": "USD/CLP, Banco Central de Chile",
        "unit": "CLP por USD", "decimals": 2, "kind": "mindicador", "code": "dolar",
        "fallback": ("yahoo", "CLP=X"),
        "source": "Banco Central de Chile (vía mindicador.cl)",
        "source_url": "https://mindicador.cl/",
    },
    {
        "id": "dxy", "name": "Índice Dólar (DXY)", "detail": "Dólar vs. canasta de 6 monedas",
        "unit": "puntos", "decimals": 2, "kind": "yahoo", "code": "DX-Y.NYB",
        "source": "ICE Futures U.S. (vía Yahoo Finance)",
        "source_url": "https://finance.yahoo.com/quote/DX-Y.NYB/",
    },
]


def get(url, timeout=90):
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3 * (attempt + 1))
    raise last


def start_date():
    return dt.date.today() - dt.timedelta(days=365 * YEARS + 2)


def fetch_yahoo(code):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(code)}?range={YEARS}y&interval=1d"
    res = json.loads(get(url))["chart"]["result"][0]
    ts = res["timestamp"]
    closes = res["indicators"]["quote"][0]["close"]
    off = res["meta"].get("gmtoffset", 0)
    pts = {}
    for t, v in zip(ts, closes):
        if v is None:
            continue
        d = dt.datetime.fromtimestamp(t + off, dt.timezone.utc).date().isoformat()
        pts[d] = v
    return pts


def fetch_eia(code):
    import xlrd  # instalado en el workflow

    raw = get(f"https://www.eia.gov/dnav/pet/hist_xls/{code}d.xls")
    sheet = xlrd.open_workbook(file_contents=raw).sheet_by_name("Data 1")
    pts = {}
    for r in range(3, sheet.nrows):
        serial, val = sheet.cell_value(r, 0), sheet.cell_value(r, 1)
        if not isinstance(serial, float) or val in ("", None):
            continue
        d = xlrd.xldate_as_datetime(serial, 0).date()
        pts[d.isoformat()] = float(val)
    return pts


def fetch_mindicador(code):
    pts = {}
    for year in range(start_date().year, dt.date.today().year + 1):
        data = json.loads(get(f"https://mindicador.cl/api/{code}/{year}"))
        for item in data.get("serie", []):
            # fechas vienen como 2026-11-18T03:00:00.000Z (medianoche hora Chile)
            pts[item["fecha"][:10]] = float(item["valor"])
    return pts


FETCHERS = {"yahoo": fetch_yahoo, "eia": fetch_eia, "mindicador": fetch_mindicador}


def main():
    old = {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            old = {s["id"]: s for s in json.load(f).get("series", [])}

    cutoff = start_date().isoformat()
    out_series, errors = [], []
    for spec in SERIES:
        meta = {k: v for k, v in spec.items() if k not in ("kind", "code", "fallback")}
        try:
            try:
                pts = FETCHERS[spec["kind"]](spec["code"])
            except Exception as e:  # noqa: BLE001
                if "fallback" not in spec:
                    raise
                kind, code = spec["fallback"]
                print(f"WARN {spec['id']:8} fuente principal falló ({e!r}); usando respaldo {code}", file=sys.stderr)
                pts = FETCHERS[kind](code)
                meta["source"] += " — respaldo: Yahoo Finance " + code
            points = [[d, round(v, 4)] for d, v in sorted(pts.items()) if d >= cutoff]
            if len(points) < 10:
                raise ValueError(f"muy pocos datos ({len(points)})")
            meta["points"] = points
            meta["updated"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes")
            meta["status"] = "ok"
            print(f"OK   {spec['id']:8} {len(points)} puntos, último {points[-1]}")
        except Exception as e:  # noqa: BLE001
            errors.append(spec["id"])
            print(f"FAIL {spec['id']:8} {e!r}", file=sys.stderr)
            prev = old.get(spec["id"])
            meta["points"] = prev["points"] if prev else []
            meta["updated"] = prev.get("updated") if prev else None
            meta["status"] = "stale"
        out_series.append(meta)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(
            {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"), "series": out_series},
            f, ensure_ascii=False, separators=(",", ":"),
        )
    if len(errors) == len(SERIES):
        sys.exit("Todas las fuentes fallaron")


if __name__ == "__main__":
    main()
