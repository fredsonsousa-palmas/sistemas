from pathlib import Path

from src.associados import SistemaAssociados


def test_fluxo_basico(tmp_path: Path) -> None:
    db_path = tmp_path / "teste.db"
    sistema = SistemaAssociados(str(db_path))

    associado_id = sistema.cadastrar_associado(
        nome="Maria Silva",
        cpf="12345678900",
        telefone="17999990000",
        plano="Familiar",
    )

    assert associado_id == 1

    lista = sistema.listar_associados()
    assert len(lista) == 1
    assert lista[0].nome == "Maria Silva"

    encontrado = sistema.buscar_por_cpf("12345678900")
    assert encontrado is not None
    assert encontrado.id == associado_id

    assert sistema.alterar_status(associado_id, False) is True
    inativos = sistema.listar_associados(somente_ativos=True)
    assert len(inativos) == 0

    resumo = sistema.resumo()
    assert resumo["total"] == 1
    assert resumo["inativos"] == 1

    assert sistema.excluir_associado(associado_id) is True
    assert sistema.listar_associados() == []
