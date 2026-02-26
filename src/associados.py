from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


@dataclass
class Associado:
    id: int
    nome: str
    cpf: str
    telefone: str
    email: str
    cidade: str
    data_nascimento: str
    plano: str
    ativo: bool
    criado_em: str


class SistemaAssociados:
    def __init__(self, db_path: str = "associados.db") -> None:
        self.db_path = Path(db_path)
        self._criar_tabelas()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _criar_tabelas(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS associados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    cpf TEXT NOT NULL UNIQUE,
                    telefone TEXT NOT NULL,
                    email TEXT,
                    cidade TEXT,
                    data_nascimento TEXT,
                    plano TEXT NOT NULL,
                    ativo INTEGER NOT NULL DEFAULT 1,
                    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def cadastrar_associado(
        self,
        nome: str,
        cpf: str,
        telefone: str,
        plano: str,
        email: str = "",
        cidade: str = "",
        data_nascimento: str = "",
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO associados (
                    nome, cpf, telefone, email, cidade, data_nascimento, plano
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (nome, cpf, telefone, email, cidade, data_nascimento, plano),
            )
            return int(cursor.lastrowid)

    def listar_associados(self, somente_ativos: bool = False) -> list[Associado]:
        query = "SELECT * FROM associados"
        params: list[object] = []
        if somente_ativos:
            query += " WHERE ativo = ?"
            params.append(1)
        query += " ORDER BY nome ASC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_para_associado(row) for row in rows]

    def buscar_por_cpf(self, cpf: str) -> Optional[Associado]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM associados WHERE cpf = ?", (cpf,)
            ).fetchone()
            return self._row_para_associado(row) if row else None

    def alterar_status(self, associado_id: int, ativo: bool) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE associados SET ativo = ? WHERE id = ?",
                (1 if ativo else 0, associado_id),
            )
            return cursor.rowcount > 0

    def excluir_associado(self, associado_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM associados WHERE id = ?", (associado_id,))
            return cursor.rowcount > 0

    def resumo(self) -> dict[str, int]:
        with self._connect() as conn:
            totais = conn.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN ativo = 1 THEN 1 ELSE 0 END) AS ativos,
                    SUM(CASE WHEN ativo = 0 THEN 1 ELSE 0 END) AS inativos
                FROM associados
                """
            ).fetchone()
            por_plano = conn.execute(
                """
                SELECT plano, COUNT(*) AS quantidade
                FROM associados
                GROUP BY plano
                ORDER BY quantidade DESC
                """
            ).fetchall()

        resumo = {
            "total": int(totais["total"] or 0),
            "ativos": int(totais["ativos"] or 0),
            "inativos": int(totais["inativos"] or 0),
        }
        for row in por_plano:
            resumo[f"plano:{row['plano']}"] = int(row["quantidade"])
        return resumo

    @staticmethod
    def _row_para_associado(row: sqlite3.Row) -> Associado:
        return Associado(
            id=int(row["id"]),
            nome=str(row["nome"]),
            cpf=str(row["cpf"]),
            telefone=str(row["telefone"]),
            email=str(row["email"] or ""),
            cidade=str(row["cidade"] or ""),
            data_nascimento=str(row["data_nascimento"] or ""),
            plano=str(row["plano"]),
            ativo=bool(row["ativo"]),
            criado_em=str(row["criado_em"]),
        )


def formatar_tabela(associados: Iterable[Associado]) -> str:
    cabecalho = ["ID", "Nome", "CPF", "Telefone", "Plano", "Status"]
    linhas = [cabecalho]
    for a in associados:
        linhas.append(
            [
                str(a.id),
                a.nome,
                a.cpf,
                a.telefone,
                a.plano,
                "Ativo" if a.ativo else "Inativo",
            ]
        )

    if len(linhas) == 1:
        return "Nenhum associado encontrado."

    larguras = [max(len(linha[i]) for linha in linhas) for i in range(len(cabecalho))]
    resultado = []
    for idx, linha in enumerate(linhas):
        resultado.append(" | ".join(valor.ljust(larguras[i]) for i, valor in enumerate(linha)))
        if idx == 0:
            resultado.append("-+-".join("-" * largura for largura in larguras))
    return "\n".join(resultado)
