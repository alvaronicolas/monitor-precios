# Monitor de Precios

Sitio estático (GitHub Pages) que monitorea Jet Fuel, petróleo Brent y WTI, oro, el dólar observado (USD/CLP) y el índice dólar (DXY).

## Cómo funciona

- `scripts/fetch_data.py` descarga las series y las guarda en `data/data.json`.
- `.github/workflows/update-data.yml` ejecuta el script todos los días, 4 veces al día, y hace commit si hay datos nuevos.
- `index.html` lee `data/data.json` y muestra tarjetas con variaciones (día, semana, mes, año y YTD), un gráfico por serie y una comparación base 100.

## Fuentes

| Serie | Fuente |
|---|---|
| Jet Fuel | U.S. EIA, spot U.S. Gulf Coast (USD/galón). Publica con ~1 semana de rezago |
| Brent / WTI | Futuros ICE / NYMEX, mes próximo (vía Yahoo Finance) |
| Oro | Futuro COMEX, mes próximo (vía Yahoo Finance) |
| Dólar observado | API oficial del Banco Central de Chile, serie `F073.TCO.PRE.Z.D` (respaldos: mindicador.cl, luego Yahoo `CLP=X`) |
| DXY | ICE Futures U.S. (vía Yahoo Finance) |

## Credenciales del Banco Central

1. Regístrate gratis en https://si3.bcentral.cl/estadisticas/Principal1/Web_Services/index.htm
2. En el repositorio: **Settings → Secrets and variables → Actions → New repository secret**, crea `BCCH_USER` (tu correo de registro) y `BCCH_PASS` (tu clave).

Sin estas credenciales el sitio sigue funcionando con los respaldos.

## Uso local

```bash
pip install xlrd
python scripts/fetch_data.py
python -m http.server 8000
```

Para actualizar a mano en GitHub: pestaña **Actions → Actualizar datos → Run workflow**.
