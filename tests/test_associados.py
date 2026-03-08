from pathlib import Path

import pytest

from src.associados import SistemaAssociados


def test_fluxo_cadastro_pagamentos_e_exportacao(tmp_path: Path) -> None:
    db_path = tmp_path / "teste.db"
    csv_path = tmp_path / "associados.csv"
    backup_path = tmp_path / "backup" / "teste.db"
    sistema = SistemaAssociados(str(db_path))

    associado_id = sistema.cadastrar_associado(
        nome="Maria Silva",
        cpf="12345678900",
        telefone="17999990000",
        plano="Familiar",
        valor_mensalidade=120.50,
        email="maria@email.com",
        cidade="Barretos",
        data_nascimento="1988-04-10",
    )

    assert associado_id == 1
    assert sistema.buscar_por_id(1) is not None

    pagamento_id = sistema.registrar_pagamento(
        associado_id=associado_id,
        competencia="2026-02",
        valor=120.50,
        forma_pagamento="pix",
    )
    assert pagamento_id == 1
    assert len(sistema.listar_pagamentos()) == 1

    inadimplentes = sistema.listar_inadimplentes("2026-02")
    assert inadimplentes == []

    assert sistema.exportar_associados_csv(str(csv_path)) == csv_path
    assert csv_path.exists()

    assert sistema.backup(str(backup_path)) == backup_path
    assert backup_path.exists()


def test_validacao_e_atualizacao(tmp_path: Path) -> None:
    sistema = SistemaAssociados(str(tmp_path / "validacao.db"))

    with pytest.raises(ValueError):
        sistema.cadastrar_associado(
            nome="Jo",
            cpf="123",
            telefone="111",
            plano="Basico",
            valor_mensalidade=80,
        )

    associado_id = sistema.cadastrar_associado(
        nome="João Souza",
        cpf="12345678901",
        telefone="11999990000",
        plano="Basico",
        valor_mensalidade=80,
    )

    atualizado = sistema.atualizar_associado(
        associado_id=associado_id,
        nome="João Souza Neto",
        telefone="11988887777",
        plano="Premium",
        valor_mensalidade=150,
        email="joao@email.com",
    )
    assert atualizado is True

    resumo = sistema.resumo()
    assert resumo["total"] == 1
    assert resumo["previsao_receita"] == 150


def test_voluntariado_certificados_e_carga_horaria(tmp_path: Path) -> None:
    sistema = SistemaAssociados(str(tmp_path / "voluntariado.db"))

    voluntario_id = sistema.cadastrar_voluntario(
        nome="Carlos Pereira",
        cpf="98765432100",
        telefone="11977776666",
        email="carlos@email.com",
    )
    evento_id = sistema.cadastrar_evento(
        titulo="Corrida Solidária",
        data_evento="2026-03-21",
        local="Barretos",
        carga_horaria=6,
        descricao="Apoio logístico",
    )

    participacao_id = sistema.registrar_participacao(
        voluntario_id=voluntario_id,
        evento_id=evento_id,
        funcao="Apoio",
    )

    codigo = sistema.emitir_certificado(participacao_id)
    assert codigo.startswith("CERT-")

    historico = sistema.historico_voluntario(voluntario_id)
    assert len(historico) == 1
    assert historico[0]["certificado_emitido"] == 1
    assert historico[0]["certificado"] == codigo

    assert sistema.carga_horaria_voluntario(voluntario_id) == 6


def test_arquivos_relativos_ficam_no_storage_dir(tmp_path: Path) -> None:
    sistema = SistemaAssociados("dados/associados.db", storage_dir=str(tmp_path))

    sistema.cadastrar_associado(
        nome="Ana Clara",
        cpf="11122233344",
        telefone="17988887777",
        plano="Familiar",
        valor_mensalidade=100,
    )

    csv_path = sistema.exportar_associados_csv("exports/associados.csv")
    backup_path = sistema.backup("backups/associados.db")

    assert csv_path == (tmp_path / "exports" / "associados.csv").resolve()
    assert backup_path == (tmp_path / "backups" / "associados.db").resolve()
    assert csv_path.exists()
    assert backup_path.exists()
