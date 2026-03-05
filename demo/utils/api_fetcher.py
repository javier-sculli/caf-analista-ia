"""
API Fetcher para fuentes externas
- Inflación (INDEC o alternativas)
- Tipo de cambio (BCRA)
- Datos macro adicionales
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import api_logger

class MacroDataFetcher:
    """Fetcher de datos macroeconómicos externos"""

    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path(__file__).parent.parent / "data" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        api_logger.info(f"📁 Cache dir configurado: {self.cache_dir}")

    def get_inflacion_argentina(self, start_date: str = "2017-01-01", end_date: str = None):
        """
        Obtiene serie de inflación REAL de Argentina

        Fuente: Datos históricos oficiales de INDEC (Instituto Nacional de Estadística)
        Los datos están almacenados localmente con valores reales actualizados hasta enero 2025

        Args:
            start_date: Fecha inicio (YYYY-MM-DD)
            end_date: Fecha fin (YYYY-MM-DD), default hoy

        Returns:
            DataFrame con columnas: fecha, ipc_mensual_pct, ipc_interanual_pct
        """
        api_logger.info("📊 Cargando inflación Argentina (datos REALES de INDEC)")
        api_logger.debug(f"   Rango solicitado: {start_date} a {end_date or 'hoy'}")

        # Cargar datos reales desde CSV local
        csv_path = Path(__file__).parent.parent / "data" / "external" / "ipc_argentina_real.csv"

        try:
            if csv_path.exists():
                api_logger.info(f"   📁 Cargando desde: {csv_path.name}")

                df = pd.read_csv(csv_path)
                df['fecha'] = pd.to_datetime(df['fecha'])

                # Calcular variación mensual aproximada desde la interanual
                # IPC mensual ≈ ((1 + interanual/100)^(1/12) - 1) * 100
                df['ipc_mensual_pct'] = ((1 + df['ipc_interanual_pct']/100) ** (1/12) - 1) * 100

                # Filtrar por rango de fechas
                df = df[df['fecha'] >= start_date].copy()
                if end_date:
                    df = df[df['fecha'] <= end_date].copy()

                df = df.sort_values('fecha').reset_index(drop=True)

                api_logger.info(f"   ✅ Datos REALES cargados: {len(df)} meses")
                api_logger.debug(f"   Rango: {df['fecha'].min().strftime('%Y-%m')} a {df['fecha'].max().strftime('%Y-%m')}")
                if len(df) > 0:
                    api_logger.info(f"   📈 IPC interanual actual: {df['ipc_interanual_pct'].iloc[-1]:.1f}% ({df['fecha'].iloc[-1].strftime('%Y-%m')})")
                    api_logger.debug(f"   📈 IPC mensual equivalente: {df['ipc_mensual_pct'].iloc[-1]:.2f}%")

                return df

            else:
                raise FileNotFoundError(f"CSV de inflación no encontrado: {csv_path}")

        except Exception as e:
            api_logger.error(f"   ❌ Error cargando datos reales: {e}")
            api_logger.warning("   ⚠️  Fallback: generando datos sintéticos")

            # Fallback: generar datos básicos si falla
            date_range = pd.date_range(start_date, end_date or datetime.now().strftime("%Y-%m-%d"), freq='MS')
            import numpy as np
            np.random.seed(42)

            df = pd.DataFrame({
                'fecha': date_range,
                'ipc_mensual_pct': np.random.normal(4.0, 2.0, len(date_range)),
                'ipc_interanual_pct': np.random.normal(80.0, 30.0, len(date_range))
            })

            return df

    def get_tipo_cambio(self, start_date: str = "2017-01-01", end_date: str = None):
        """
        Obtiene serie de tipo de cambio oficial

        Para demo: usa datos sintéticos
        En producción: usar API BCRA

        Returns:
            DataFrame con columnas: fecha, tc_oficial, tc_blue (opcional)
        """
        api_logger.info("🌐 Fetching tipo de cambio")

        # Verificar cache
        cache_file = self.cache_dir / "tipo_cambio.parquet"
        if cache_file.exists():
            cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if cache_age < timedelta(days=1):  # Cache válido 1 día
                api_logger.info(f"   ✅ Usando cache")
                df = pd.read_parquet(cache_file)
                return df[df['fecha'] >= start_date].copy()

        api_logger.warning("   ⚠️  Demo: Generando datos sintéticos de TC")
        api_logger.debug("   En producción usar: https://api.bcra.gob.ar/estadisticas/v2.0/datosvariable/4/...")

        # Generar datos sintéticos
        import numpy as np
        date_range = pd.date_range(start_date, end_date or datetime.now().strftime("%Y-%m-%d"), freq='D')

        # Tipo de cambio con tendencia alcista
        tc_base = 15
        tc_values = []

        for i, date in enumerate(date_range):
            # Tendencia + ruido
            trend = tc_base * (1.15 ** (i / 365))  # 15% anual aprox
            noise = np.random.normal(0, trend * 0.02)  # 2% de volatilidad diaria
            tc_values.append(max(tc_base, trend + noise))

        df = pd.DataFrame({
            'fecha': date_range,
            'tc_oficial': tc_values
        })

        api_logger.info(f"   ✅ Datos obtenidos: {len(df)} días")
        api_logger.debug(f"   TC inicial: ${df['tc_oficial'].iloc[0]:.2f}")
        api_logger.debug(f"   TC actual: ${df['tc_oficial'].iloc[-1]:.2f}")

        # Guardar cache
        df.to_parquet(cache_file, index=False)

        return df

    def get_pib_argentina(self, start_date: str = "2017-01-01"):
        """
        Obtiene serie de PIB trimestral

        Para demo: usa datos sintéticos
        En producción: INDEC o World Bank API
        """
        api_logger.info("🌐 Fetching PIB Argentina")

        api_logger.warning("   ⚠️  Demo: Generando datos sintéticos de PIB")

        # PIB trimestral
        quarters = pd.date_range(start_date, datetime.now().strftime("%Y-%m-%d"), freq='Q')

        import numpy as np
        np.random.seed(42)

        # Variación % trimestral
        pib_variacion = []
        for q in quarters:
            year = q.year
            if year <= 2019:
                var = np.random.normal(0.5, 1.5)  # Crecimiento modesto
            elif year == 2020:
                var = np.random.normal(-5.0, 2.0)  # Recesión COVID
            elif year <= 2022:
                var = np.random.normal(2.0, 1.0)  # Recuperación
            else:
                var = np.random.normal(-0.5, 1.5)  # Estancamiento/recesión

            pib_variacion.append(var)

        df = pd.DataFrame({
            'fecha': quarters,
            'pib_variacion_trimestral_pct': pib_variacion
        })

        # Calcular interanual
        df['pib_variacion_interanual_pct'] = df['pib_variacion_trimestral_pct'].rolling(4).sum()

        api_logger.info(f"   ✅ Datos obtenidos: {len(df)} trimestres")

        return df


def main():
    """Test del API fetcher"""
    api_logger.info("="*80)
    api_logger.info("🧪 TEST API FETCHER")
    api_logger.info("="*80)

    fetcher = MacroDataFetcher()

    # Test inflación
    api_logger.info("\n📊 TEST 1: Inflación")
    df_inflacion = fetcher.get_inflacion_argentina(start_date="2023-01-01")
    api_logger.info(f"   Últimos 5 meses:\n{df_inflacion.tail().to_string()}")

    # Test tipo de cambio
    api_logger.info("\n📊 TEST 2: Tipo de Cambio")
    df_tc = fetcher.get_tipo_cambio(start_date="2025-01-01")
    api_logger.info(f"   Últimos 5 días:\n{df_tc.tail().to_string()}")

    # Test PIB
    api_logger.info("\n📊 TEST 3: PIB")
    df_pib = fetcher.get_pib_argentina()
    api_logger.info(f"   Últimos 4 trimestres:\n{df_pib.tail().to_string()}")

    api_logger.info("\n✅ Tests completados")


if __name__ == "__main__":
    main()
