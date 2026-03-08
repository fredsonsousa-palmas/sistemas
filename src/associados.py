from __future__ import annotations

import csv
import re
import secrets
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Optional

CPF_RE = re.compile(r"\d{11}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TELEFONE_RE = re.compile(r"^\d{10,11}$")


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


@dataclass
class Pagamento:
    id: int
    associado_id: int
    competencia: str
    valor: float
    pago_em: str
    forma_pagamento: str
    observacao: str


@dataclass
class Voluntario:
    id: int
    nome: str
    cpf: str
    telefone: str
    email: str
    ativo: bool
    criado_em: str


@dataclass
class Evento:
    id: int
    titulo: str
    data_evento: str
    local: str
    carga_horaria: float
    descricao: str
    criado_em: str


@dataclass
class ParticipacaoVoluntaria:
    id: int
    voluntario_id: int
    evento_id: int
    funcao: str
    horas_realizadas: float
    certificado_emitido: bool
    registrado_em: str


class SistemaAssociados:
    def __init__(self, db_path: str = "associados.db") -> None:
        self.db_path = Path(db_path)
        self._criar_tabelas()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
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
                    valor_mensalidade REAL NOT NULL DEFAULT 0,
                    ativo INTEGER NOT NULL DEFAULT 1,
                    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self._migrar_schema(conn)

    def _migrar_schema(self, conn: sqlite3.Connection) -> None:
        colunas = {row[1] for row in conn.execute("PRAGMA table_info(associados)").fetchall()}
        if "valor_mensalidade" not in colunas:
            conn.execute("ALTER TABLE associados ADD COLUMN valor_mensalidade REAL NOT NULL DEFAULT 0")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pagamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                associado_id INTEGER NOT NULL,
                competencia TEXT NOT NULL,
                valor REAL NOT NULL,
                pago_em TEXT NOT NULL,
                forma_pagamento TEXT NOT NULL DEFAULT 'pix',
                observacao TEXT NOT NULL DEFAULT '',
                UNIQUE(associado_id, competencia),
                FOREIGN KEY (associado_id) REFERENCES associados(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS voluntarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cpf TEXT NOT NULL UNIQUE,
                telefone TEXT NOT NULL,
                email TEXT,
                ativo INTEGER NOT NULL DEFAULT 1,
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS eventos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                data_evento TEXT NOT NULL,
                local TEXT NOT NULL,
                carga_horaria REAL NOT NULL,
                descricao TEXT NOT NULL DEFAULT '',
                criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS participacoes_voluntarias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                voluntario_id INTEGER NOT NULL,
                evento_id INTEGER NOT NULL,
                funcao TEXT NOT NULL DEFAULT '',
                horas_realizadas REAL NOT NULL,
                certificado_emitido INTEGER NOT NULL DEFAULT 0,
                registrado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(voluntario_id, evento_id),
                FOREIGN KEY (voluntario_id) REFERENCES voluntarios(id) ON DELETE CASCADE,
                FOREIGN KEY (evento_id) REFERENCES eventos(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS certificados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participacao_id INTEGER NOT NULL UNIQUE,
                codigo TEXT NOT NULL UNIQUE,
                emitido_em TEXT NOT NULL,
                FOREIGN KEY (participacao_id) REFERENCES participacoes_voluntarias(id) ON DELETE CASCADE
            )
            """
        )

    def _validar_contato(self, nome: str, cpf: str, telefone: str, email: str) -> None:
        if len(nome.strip()) < 3:
            raise ValueError("Nome deve possuir ao menos 3 caracteres.")
        if cpf and not CPF_RE.match(cpf):
            raise ValueError("CPF deve conter exatamente 11 dígitos numéricos.")
        if not TELEFONE_RE.match(telefone):
            raise ValueError("Telefone deve conter 10 ou 11 dígitos numéricos.")
        if email and not EMAIL_RE.match(email):
            raise ValueError("Email inválido.")

    def cadastrar_associado(
        self,
        nome: str,
        cpf: str,
        telefone: str,
        plano: str,
        valor_mensalidade: float,
        email: str = "",
        cidade: str = "",
        data_nascimento: str = "",
    ) -> int:
        self._validar_contato(nome, cpf, telefone, email)
        if data_nascimento:
            datetime.strptime(data_nascimento, "%Y-%m-%d")
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO associados (
                    nome, cpf, telefone, email, cidade, data_nascimento, plano, valor_mensalidade
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (nome, cpf, telefone, email, cidade, data_nascimento, plano, valor_mensalidade),
            )
            return int(cursor.lastrowid)

    def atualizar_associado(
        self,
        associado_id: int,
        nome: str,
        telefone: str,
        plano: str,
        valor_mensalidade: float,
        email: str = "",
        cidade: str = "",
        data_nascimento: str = "",
    ) -> bool:
        self._validar_contato(nome, "", telefone, email)
        if data_nascimento:
            datetime.strptime(data_nascimento, "%Y-%m-%d")
        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE associados
                SET nome = ?, telefone = ?, email = ?, cidade = ?,
                    data_nascimento = ?, plano = ?, valor_mensalidade = ?
                WHERE id = ?
                """,
                (nome, telefone, email, cidade, data_nascimento, plano, valor_mensalidade, associado_id),
            )
            return cursor.rowcount > 0

    def listar_associados(self, somente_ativos: bool = False) -> list[Associado]:
        query = "SELECT * FROM associados"
        params: list[object] = []
        if somente_ativos:
            query += " WHERE ativo = 1"
        query += " ORDER BY nome ASC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_para_associado(row) for row in rows]

    def buscar_por_cpf(self, cpf: str) -> Optional[Associado]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM associados WHERE cpf = ?", (cpf,)).fetchone()
            return self._row_para_associado(row) if row else None

    def buscar_por_id(self, associado_id: int) -> Optional[Associado]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM associados WHERE id = ?", (associado_id,)).fetchone()
            return self._row_para_associado(row) if row else None

    def alterar_status(self, associado_id: int, ativo: bool) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("UPDATE associados SET ativo = ? WHERE id = ?", (1 if ativo else 0, associado_id))
            return cursor.rowcount > 0

    def excluir_associado(self, associado_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM associados WHERE id = ?", (associado_id,))
            return cursor.rowcount > 0

    def registrar_pagamento(
        self,
        associado_id: int,
        competencia: str,
        valor: float,
        forma_pagamento: str = "pix",
        observacao: str = "",
    ) -> int:
        datetime.strptime(competencia, "%Y-%m")
        if valor <= 0:
            raise ValueError("Valor do pagamento deve ser maior que zero.")
        pago_em = date.today().isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO pagamentos (
                    associado_id, competencia, valor, pago_em, forma_pagamento, observacao
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (associado_id, competencia, valor, pago_em, forma_pagamento, observacao),
            )
            return int(cursor.lastrowid)

    def listar_pagamentos(self, associado_id: Optional[int] = None) -> list[Pagamento]:
        query = "SELECT * FROM pagamentos"
        params: list[object] = []
        if associado_id is not None:
            query += " WHERE associado_id = ?"
            params.append(associado_id)
        query += " ORDER BY competencia DESC, pago_em DESC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_para_pagamento(row) for row in rows]

    def listar_inadimplentes(self, competencia: str) -> list[Associado]:
        datetime.strptime(competencia, "%Y-%m")
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT a.* FROM associados a
                WHERE a.ativo = 1
                  AND NOT EXISTS (
                    SELECT 1 FROM pagamentos p
                    WHERE p.associado_id = a.id AND p.competencia = ?
                  )
                ORDER BY a.nome ASC
                """,
                (competencia,),
            ).fetchall()
            return [self._row_para_associado(row) for row in rows]

    def cadastrar_voluntario(self, nome: str, cpf: str, telefone: str, email: str = "") -> int:
        self._validar_contato(nome, cpf, telefone, email)
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO voluntarios (nome, cpf, telefone, email) VALUES (?, ?, ?, ?)",
                (nome, cpf, telefone, email),
            )
            return int(cursor.lastrowid)

    def listar_voluntarios(self, somente_ativos: bool = True) -> list[Voluntario]:
        query = "SELECT * FROM voluntarios"
        if somente_ativos:
            query += " WHERE ativo = 1"
        query += " ORDER BY nome ASC"
        with self._connect() as conn:
            rows = conn.execute(query).fetchall()
            return [self._row_para_voluntario(row) for row in rows]

    def cadastrar_evento(self, titulo: str, data_evento: str, local: str, carga_horaria: float, descricao: str = "") -> int:
        if carga_horaria <= 0:
            raise ValueError("Carga horária deve ser maior que zero.")
        datetime.strptime(data_evento, "%Y-%m-%d")
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO eventos (titulo, data_evento, local, carga_horaria, descricao) VALUES (?, ?, ?, ?, ?)",
                (titulo, data_evento, local, carga_horaria, descricao),
            )
            return int(cursor.lastrowid)

    def listar_eventos(self) -> list[Evento]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM eventos ORDER BY data_evento DESC").fetchall()
            return [self._row_para_evento(row) for row in rows]

    def registrar_participacao(self, voluntario_id: int, evento_id: int, funcao: str = "", horas_realizadas: Optional[float] = None) -> int:
        with self._connect() as conn:
            evento = conn.execute("SELECT carga_horaria FROM eventos WHERE id = ?", (evento_id,)).fetchone()
            if evento is None:
                raise ValueError("Evento não encontrado.")
            horas = float(evento["carga_horaria"]) if horas_realizadas is None else horas_realizadas
            if horas <= 0:
                raise ValueError("Horas realizadas deve ser maior que zero.")
            cursor = conn.execute(
                """
                INSERT INTO participacoes_voluntarias (voluntario_id, evento_id, funcao, horas_realizadas)
                VALUES (?, ?, ?, ?)
                """,
                (voluntario_id, evento_id, funcao, horas),
            )
            return int(cursor.lastrowid)

    def emitir_certificado(self, participacao_id: int) -> str:
        codigo = f"CERT-{date.today().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
        emitido_em = date.today().isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO certificados (participacao_id, codigo, emitido_em) VALUES (?, ?, ?)",
                (participacao_id, codigo, emitido_em),
            )
            conn.execute(
                "UPDATE participacoes_voluntarias SET certificado_emitido = 1 WHERE id = ?",
                (participacao_id,),
            )
        return codigo

    def historico_voluntario(self, voluntario_id: int) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT pv.id AS participacao_id, e.titulo, e.data_evento, e.local,
                       pv.funcao, pv.horas_realizadas, pv.certificado_emitido,
                       c.codigo AS certificado
                FROM participacoes_voluntarias pv
                JOIN eventos e ON e.id = pv.evento_id
                LEFT JOIN certificados c ON c.participacao_id = pv.id
                WHERE pv.voluntario_id = ?
                ORDER BY e.data_evento DESC
                """,
                (voluntario_id,),
            ).fetchall()

    def carga_horaria_voluntario(self, voluntario_id: int) -> float:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT SUM(horas_realizadas) AS total FROM participacoes_voluntarias WHERE voluntario_id = ?",
                (voluntario_id,),
            ).fetchone()
            return float(row["total"] or 0)

    def exportar_associados_csv(self, output_path: str) -> Path:
        associados = self.listar_associados()
        path = Path(output_path)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "nome", "cpf", "telefone", "email", "cidade", "data_nascimento", "plano", "ativo", "criado_em"])
            for a in associados:
                writer.writerow([a.id, a.nome, a.cpf, a.telefone, a.email, a.cidade, a.data_nascimento, a.plano, int(a.ativo), a.criado_em])
        return path

    def backup(self, backup_path: str) -> Path:
        destino = Path(backup_path)
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.db_path, destino)
        return destino

    def resumo(self) -> dict[str, float]:
        with self._connect() as conn:
            totais = conn.execute(
                "SELECT COUNT(*) AS total, SUM(CASE WHEN ativo = 1 THEN 1 ELSE 0 END) AS ativos, SUM(CASE WHEN ativo = 0 THEN 1 ELSE 0 END) AS inativos, SUM(valor_mensalidade) AS previsao_receita FROM associados"
            ).fetchone()
            receita_real = conn.execute("SELECT SUM(valor) AS total_recebido FROM pagamentos").fetchone()
            voluntarios = conn.execute("SELECT COUNT(*) AS total FROM voluntarios WHERE ativo = 1").fetchone()

        return {
            "total": float(totais["total"] or 0),
            "ativos": float(totais["ativos"] or 0),
            "inativos": float(totais["inativos"] or 0),
            "previsao_receita": float(totais["previsao_receita"] or 0),
            "total_recebido": float(receita_real["total_recebido"] or 0),
            "voluntarios_ativos": float(voluntarios["total"] or 0),
        }

    @staticmethod
    def _row_para_associado(row: sqlite3.Row) -> Associado:
        return Associado(int(row["id"]), str(row["nome"]), str(row["cpf"]), str(row["telefone"]), str(row["email"] or ""), str(row["cidade"] or ""), str(row["data_nascimento"] or ""), str(row["plano"]), bool(row["ativo"]), str(row["criado_em"]))

    @staticmethod
    def _row_para_pagamento(row: sqlite3.Row) -> Pagamento:
        return Pagamento(int(row["id"]), int(row["associado_id"]), str(row["competencia"]), float(row["valor"]), str(row["pago_em"]), str(row["forma_pagamento"]), str(row["observacao"]))

    @staticmethod
    def _row_para_voluntario(row: sqlite3.Row) -> Voluntario:
        return Voluntario(int(row["id"]), str(row["nome"]), str(row["cpf"]), str(row["telefone"]), str(row["email"] or ""), bool(row["ativo"]), str(row["criado_em"]))

    @staticmethod
    def _row_para_evento(row: sqlite3.Row) -> Evento:
        return Evento(int(row["id"]), str(row["titulo"]), str(row["data_evento"]), str(row["local"]), float(row["carga_horaria"]), str(row["descricao"]), str(row["criado_em"]))


def _formatar_tabela_generica(cabecalho: list[str], linhas: list[list[str]], vazio: str) -> str:
    if not linhas:
        return vazio
    tabela = [cabecalho] + linhas
    larguras = [max(len(linha[i]) for linha in tabela) for i in range(len(cabecalho))]
    out: list[str] = []
    for idx, linha in enumerate(tabela):
        out.append(" | ".join(valor.ljust(larguras[i]) for i, valor in enumerate(linha)))
        if idx == 0:
            out.append("-+-".join("-" * largura for largura in larguras))
    return "\n".join(out)


def formatar_tabela(associados: Iterable[Associado]) -> str:
    linhas = [[str(a.id), a.nome, a.cpf, a.telefone, a.plano, "Ativo" if a.ativo else "Inativo"] for a in associados]
    return _formatar_tabela_generica(["ID", "Nome", "CPF", "Telefone", "Plano", "Status"], linhas, "Nenhum associado encontrado.")


def formatar_pagamentos(pagamentos: Iterable[Pagamento]) -> str:
    linhas = [[str(p.id), str(p.associado_id), p.competencia, f"R$ {p.valor:.2f}", p.pago_em, p.forma_pagamento] for p in pagamentos]
    return _formatar_tabela_generica(["ID", "Assoc.", "Competência", "Valor", "Pago em", "Forma"], linhas, "Nenhum pagamento encontrado.")


def formatar_voluntarios(voluntarios: Iterable[Voluntario]) -> str:
    linhas = [[str(v.id), v.nome, v.cpf, v.telefone, "Ativo" if v.ativo else "Inativo"] for v in voluntarios]
    return _formatar_tabela_generica(["ID", "Nome", "CPF", "Telefone", "Status"], linhas, "Nenhum voluntário encontrado.")


def formatar_eventos(eventos: Iterable[Evento]) -> str:
    linhas = [[str(e.id), e.titulo, e.data_evento, e.local, f"{e.carga_horaria:.1f}h"] for e in eventos]
    return _formatar_tabela_generica(["ID", "Evento", "Data", "Local", "Carga"], linhas, "Nenhum evento encontrado.")


def formatar_historico_voluntario(historico: Iterable[sqlite3.Row]) -> str:
    linhas = []
    for r in historico:
        linhas.append([
            str(r["participacao_id"]),
            str(r["titulo"]),
            str(r["data_evento"]),
            f"{float(r['horas_realizadas']):.1f}h",
            "Sim" if bool(r["certificado_emitido"]) else "Não",
            str(r["certificado"] or "-"),
        ])
    return _formatar_tabela_generica(["ID", "Evento", "Data", "Horas", "Certificado", "Código"], linhas, "Nenhum histórico de voluntariado.")
