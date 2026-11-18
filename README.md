# Monitor de Precios

Sitio estático (GitHub Pages) que monitorea Jet Fuel, petróleo Brent y WTI, oro, el dólar observado (USD/CLP) y el índice dólar (DXY).

## Cómo funciona

- `scripts/fetch_data.py` descarga las series y las guarda en `data/data.json`.
- `.github/workflows/update-data.yml` ejecuta el script de lunes a viernes, 4 veces al día, y hace commit si hay datos nuevos.
- `index.html` lee `data/data.json` y muestra tarjetas con variaciones (día, semana, mes, año y YTD), un gráfico por serie y una comparación base 100.

## Fuentes

| Serie | Fuente |
|---|---|
| Jet Fuel | U.S. EIA, spot U.S. Gulf Coast (USD/galón). Publica con ~1 semana de rezago |
| Brent / WTI | Futuros ICE / NYMEX, mes próximo (vía Yahoo Finance) |
| Oro | Futuro COMEX, mes próximo (vía Yahoo Finance) |
| Dólar observado | Banco Central de Chile vía mindicador.cl (respaldo: Yahoo `CLP=X`) |
| DXY | ICE Futures U.S. (vía Yahoo Finance) |

## Uso local

```bash
pip install xlrd
python scripts/fetch_data.py
python -m http.server 8000
```

Para actualizar a mano en GitHub: pestaña **Actions → Actualizar datos → Run workflow**.
