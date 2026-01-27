"""
Módulo de Banco de Dados - SQLite para armazenamento de resultados
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import os


class QADatabase:
    """Gerenciador de banco de dados SQLite para resultados de QA"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            # Usa diretório do usuário para persistência
            home = Path.home()
            db_dir = home / ".pyclinac_qa"
            db_dir.mkdir(exist_ok=True)
            db_path = str(db_dir / "qa_results.db")

        self.db_path = db_path
        self.conn = None
        self._init_database()

    def _init_database(self):
        """Inicializa o banco de dados e cria tabelas"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        # Tabela de máquinas/equipamentos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS machines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                manufacturer TEXT,
                model TEXT,
                serial_number TEXT,
                location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabela de resultados de QA
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qa_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id INTEGER,
                test_type TEXT NOT NULL,
                test_date TIMESTAMP NOT NULL,
                performed_by TEXT,
                passed INTEGER,
                results_json TEXT,
                notes TEXT,
                pdf_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (machine_id) REFERENCES machines(id)
            )
        """)

        # Tabela de configurações
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabela de tolerâncias padrão
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tolerances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_type TEXT NOT NULL,
                parameter TEXT NOT NULL,
                tolerance_value REAL,
                unit TEXT,
                action_level REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(test_type, parameter)
            )
        """)

        # Inserir tolerâncias padrão se não existirem
        default_tolerances = [
            ("winston_lutz", "gantry_iso_size", 1.0, "mm", 0.75),
            ("winston_lutz", "coll_iso_size", 1.0, "mm", 0.75),
            ("winston_lutz", "couch_iso_size", 1.0, "mm", 0.75),
            ("picket_fence", "max_error", 0.5, "mm", 0.3),
            ("starshot", "wobble_radius", 1.0, "mm", 0.75),
            ("vmat_drgs", "max_deviation", 1.5, "%", 1.0),
            ("vmat_drmlc", "max_deviation", 1.5, "%", 1.0),
            ("field_analysis", "flatness", 3.0, "%", 2.0),
            ("field_analysis", "symmetry", 3.0, "%", 2.0),
            ("catphan", "hu_tolerance", 40.0, "HU", 30.0),
            ("gamma", "passing_rate", 95.0, "%", 90.0),
        ]

        for tol in default_tolerances:
            cursor.execute("""
                INSERT OR IGNORE INTO tolerances (test_type, parameter, tolerance_value, unit, action_level)
                VALUES (?, ?, ?, ?, ?)
            """, tol)

        self.conn.commit()

    def close(self):
        """Fecha a conexão com o banco"""
        if self.conn:
            self.conn.close()

    # ==========================================================================
    # MÁQUINAS
    # ==========================================================================

    def add_machine(self, name: str, manufacturer: str = None,
                   model: str = None, serial_number: str = None,
                   location: str = None) -> int:
        """Adiciona uma nova máquina"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO machines (name, manufacturer, model, serial_number, location)
            VALUES (?, ?, ?, ?, ?)
        """, (name, manufacturer, model, serial_number, location))
        self.conn.commit()
        return cursor.lastrowid

    def get_machines(self) -> List[Dict]:
        """Retorna lista de máquinas"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM machines ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]

    def get_machine_by_name(self, name: str) -> Optional[Dict]:
        """Busca máquina por nome"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM machines WHERE name = ?", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # ==========================================================================
    # RESULTADOS DE QA
    # ==========================================================================

    def save_result(self, test_type: str, results: Dict[str, Any],
                   machine_name: str = None, performed_by: str = None,
                   passed: bool = None, notes: str = None,
                   pdf_path: str = None, test_date: datetime = None) -> int:
        """Salva um resultado de QA"""

        # Obtém ou cria máquina
        machine_id = None
        if machine_name:
            machine = self.get_machine_by_name(machine_name)
            if machine:
                machine_id = machine['id']
            else:
                machine_id = self.add_machine(machine_name)

        if test_date is None:
            test_date = datetime.now()

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO qa_results (machine_id, test_type, test_date, performed_by,
                                   passed, results_json, notes, pdf_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            machine_id, test_type, test_date.isoformat(), performed_by,
            1 if passed else 0 if passed is not None else None,
            json.dumps(results), notes, pdf_path
        ))
        self.conn.commit()
        return cursor.lastrowid

    def get_results(self, test_type: str = None, machine_name: str = None,
                   start_date: datetime = None, end_date: datetime = None,
                   limit: int = 100) -> List[Dict]:
        """Busca resultados com filtros"""
        query = """
            SELECT r.*, m.name as machine_name
            FROM qa_results r
            LEFT JOIN machines m ON r.machine_id = m.id
            WHERE 1=1
        """
        params = []

        if test_type:
            query += " AND r.test_type = ?"
            params.append(test_type)

        if machine_name:
            query += " AND m.name = ?"
            params.append(machine_name)

        if start_date:
            query += " AND r.test_date >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND r.test_date <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY r.test_date DESC LIMIT ?"
        params.append(limit)

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            result = dict(row)
            if result['results_json']:
                result['results'] = json.loads(result['results_json'])
            results.append(result)

        return results

    def get_trend_data(self, test_type: str, parameter: str,
                      machine_name: str = None, days: int = 90) -> List[Dict]:
        """Obtém dados de tendência para um parâmetro específico"""
        from datetime import timedelta

        start_date = datetime.now() - timedelta(days=days)
        results = self.get_results(
            test_type=test_type,
            machine_name=machine_name,
            start_date=start_date,
            limit=500
        )

        trend_data = []
        for r in results:
            if 'results' in r and parameter in r['results']:
                trend_data.append({
                    'date': r['test_date'],
                    'value': r['results'][parameter],
                    'passed': r['passed']
                })

        return trend_data

    # ==========================================================================
    # TOLERÂNCIAS
    # ==========================================================================

    def get_tolerances(self, test_type: str = None) -> List[Dict]:
        """Retorna tolerâncias configuradas"""
        cursor = self.conn.cursor()

        if test_type:
            cursor.execute(
                "SELECT * FROM tolerances WHERE test_type = ?",
                (test_type,)
            )
        else:
            cursor.execute("SELECT * FROM tolerances ORDER BY test_type, parameter")

        return [dict(row) for row in cursor.fetchall()]

    def update_tolerance(self, test_type: str, parameter: str,
                        tolerance_value: float, action_level: float = None):
        """Atualiza uma tolerância"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE tolerances
            SET tolerance_value = ?, action_level = ?
            WHERE test_type = ? AND parameter = ?
        """, (tolerance_value, action_level, test_type, parameter))
        self.conn.commit()

    # ==========================================================================
    # CONFIGURAÇÕES
    # ==========================================================================

    def get_setting(self, key: str, default: str = None) -> str:
        """Obtém uma configuração"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row['value'] if row else default

    def set_setting(self, key: str, value: str):
        """Define uma configuração"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, value))
        self.conn.commit()

    # ==========================================================================
    # ESTATÍSTICAS
    # ==========================================================================

    def get_summary_stats(self, days: int = 30) -> Dict:
        """Retorna estatísticas resumidas"""
        from datetime import timedelta

        start_date = datetime.now() - timedelta(days=days)

        cursor = self.conn.cursor()

        # Total de testes
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END) as passed,
                   SUM(CASE WHEN passed = 0 THEN 1 ELSE 0 END) as failed
            FROM qa_results
            WHERE test_date >= ?
        """, (start_date.isoformat(),))
        overall = dict(cursor.fetchone())

        # Por tipo de teste
        cursor.execute("""
            SELECT test_type,
                   COUNT(*) as total,
                   SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END) as passed
            FROM qa_results
            WHERE test_date >= ?
            GROUP BY test_type
        """, (start_date.isoformat(),))
        by_type = [dict(row) for row in cursor.fetchall()]

        # Por máquina
        cursor.execute("""
            SELECT m.name,
                   COUNT(*) as total,
                   SUM(CASE WHEN r.passed = 1 THEN 1 ELSE 0 END) as passed
            FROM qa_results r
            JOIN machines m ON r.machine_id = m.id
            WHERE r.test_date >= ?
            GROUP BY m.name
        """, (start_date.isoformat(),))
        by_machine = [dict(row) for row in cursor.fetchall()]

        return {
            'overall': overall,
            'by_type': by_type,
            'by_machine': by_machine,
            'period_days': days
        }


# Instância global do banco de dados
_db_instance = None


def get_database() -> QADatabase:
    """Retorna instância singleton do banco de dados"""
    global _db_instance
    if _db_instance is None:
        _db_instance = QADatabase()
    return _db_instance
