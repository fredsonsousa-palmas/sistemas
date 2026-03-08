from __future__ import annotations

import argparse

from associados import (
    SistemaAssociados,
    formatar_eventos,
    formatar_historico_voluntario,
    formatar_pagamentos,
    formatar_tabela,
    formatar_voluntarios,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="controle-associados", description="Sistema de controle da Associação do Hospital de Amor.")
    parser.add_argument("--storage-dir", default="/home/sistemas", help="Diretório base de dados/arquivos.")
    parser.add_argument("--db", default="associados.db", help="Caminho do banco SQLite.")
    sub = parser.add_subparsers(dest="comando", required=True)

    cadastrar = sub.add_parser("cadastrar", help="Cadastrar associado")
    cadastrar.add_argument("--nome", required=True)
    cadastrar.add_argument("--cpf", required=True)
    cadastrar.add_argument("--telefone", required=True)
    cadastrar.add_argument("--plano", required=True)
    cadastrar.add_argument("--valor-mensalidade", type=float, default=0)
    cadastrar.add_argument("--email", default="")
    cadastrar.add_argument("--cidade", default="")
    cadastrar.add_argument("--data-nascimento", default="")

    atualizar = sub.add_parser("atualizar", help="Atualizar associado")
    atualizar.add_argument("--id", type=int, required=True)
    atualizar.add_argument("--nome", required=True)
    atualizar.add_argument("--telefone", required=True)
    atualizar.add_argument("--plano", required=True)
    atualizar.add_argument("--valor-mensalidade", type=float, default=0)
    atualizar.add_argument("--email", default="")
    atualizar.add_argument("--cidade", default="")
    atualizar.add_argument("--data-nascimento", default="")

    listar = sub.add_parser("listar", help="Listar associados")
    listar.add_argument("--ativos", action="store_true")

    buscar = sub.add_parser("buscar-cpf", help="Buscar associado por CPF")
    buscar.add_argument("--cpf", required=True)

    status = sub.add_parser("status", help="Ativar/inativar associado")
    status.add_argument("--id", type=int, required=True)
    status.add_argument("--ativo", choices=["sim", "nao"], required=True)

    excluir = sub.add_parser("excluir", help="Excluir associado")
    excluir.add_argument("--id", type=int, required=True)

    pag = sub.add_parser("registrar-pagamento", help="Registrar pagamento")
    pag.add_argument("--associado-id", type=int, required=True)
    pag.add_argument("--competencia", required=True)
    pag.add_argument("--valor", type=float, required=True)
    pag.add_argument("--forma", default="pix")
    pag.add_argument("--observacao", default="")

    listpag = sub.add_parser("listar-pagamentos", help="Listar pagamentos")
    listpag.add_argument("--associado-id", type=int)

    inad = sub.add_parser("inadimplentes", help="Relatório de inadimplência")
    inad.add_argument("--competencia", required=True)

    volunt = sub.add_parser("cadastrar-voluntario", help="Cadastrar voluntário")
    volunt.add_argument("--nome", required=True)
    volunt.add_argument("--cpf", required=True)
    volunt.add_argument("--telefone", required=True)
    volunt.add_argument("--email", default="")

    sub.add_parser("listar-voluntarios", help="Listar voluntários")

    evento = sub.add_parser("cadastrar-evento", help="Cadastrar evento")
    evento.add_argument("--titulo", required=True)
    evento.add_argument("--data", required=True, help="YYYY-MM-DD")
    evento.add_argument("--local", required=True)
    evento.add_argument("--carga", type=float, required=True)
    evento.add_argument("--descricao", default="")

    sub.add_parser("listar-eventos", help="Listar eventos")

    part = sub.add_parser("registrar-participacao", help="Registrar participação voluntária")
    part.add_argument("--voluntario-id", type=int, required=True)
    part.add_argument("--evento-id", type=int, required=True)
    part.add_argument("--funcao", default="")
    part.add_argument("--horas", type=float)

    cert = sub.add_parser("emitir-certificado", help="Emitir certificado")
    cert.add_argument("--participacao-id", type=int, required=True)

    hist = sub.add_parser("historico-voluntario", help="Histórico e carga horária do voluntário")
    hist.add_argument("--voluntario-id", type=int, required=True)

    exportar = sub.add_parser("exportar-csv", help="Exportar associados")
    exportar.add_argument("--saida", required=True)

    backup = sub.add_parser("backup", help="Backup do banco")
    backup.add_argument("--saida", required=True)

    sub.add_parser("resumo", help="Resumo geral")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    sistema = SistemaAssociados(args.db, storage_dir=args.storage_dir)

    try:
        if args.comando == "cadastrar":
            aid = sistema.cadastrar_associado(args.nome, args.cpf, args.telefone, args.plano, args.valor_mensalidade, args.email, args.cidade, args.data_nascimento)
            print(f"Associado cadastrado com sucesso. ID: {aid}")
        elif args.comando == "atualizar":
            ok = sistema.atualizar_associado(args.id, args.nome, args.telefone, args.plano, args.valor_mensalidade, args.email, args.cidade, args.data_nascimento)
            print("Associado atualizado com sucesso." if ok else "Associado não encontrado.")
        elif args.comando == "listar":
            print(formatar_tabela(sistema.listar_associados(somente_ativos=args.ativos)))
        elif args.comando == "buscar-cpf":
            associado = sistema.buscar_por_cpf(args.cpf)
            print(formatar_tabela([associado]) if associado else "Associado não encontrado.")
        elif args.comando == "status":
            print("Status atualizado com sucesso." if sistema.alterar_status(args.id, args.ativo == "sim") else "Associado não encontrado.")
        elif args.comando == "excluir":
            print("Associado excluído com sucesso." if sistema.excluir_associado(args.id) else "Associado não encontrado.")
        elif args.comando == "registrar-pagamento":
            pid = sistema.registrar_pagamento(args.associado_id, args.competencia, args.valor, args.forma, args.observacao)
            print(f"Pagamento registrado com sucesso. ID: {pid}")
        elif args.comando == "listar-pagamentos":
            print(formatar_pagamentos(sistema.listar_pagamentos(args.associado_id)))
        elif args.comando == "inadimplentes":
            print(formatar_tabela(sistema.listar_inadimplentes(args.competencia)))
        elif args.comando == "cadastrar-voluntario":
            vid = sistema.cadastrar_voluntario(args.nome, args.cpf, args.telefone, args.email)
            print(f"Voluntário cadastrado com sucesso. ID: {vid}")
        elif args.comando == "listar-voluntarios":
            print(formatar_voluntarios(sistema.listar_voluntarios()))
        elif args.comando == "cadastrar-evento":
            eid = sistema.cadastrar_evento(args.titulo, args.data, args.local, args.carga, args.descricao)
            print(f"Evento cadastrado com sucesso. ID: {eid}")
        elif args.comando == "listar-eventos":
            print(formatar_eventos(sistema.listar_eventos()))
        elif args.comando == "registrar-participacao":
            pid = sistema.registrar_participacao(args.voluntario_id, args.evento_id, args.funcao, args.horas)
            print(f"Participação registrada com sucesso. ID: {pid}")
        elif args.comando == "emitir-certificado":
            codigo = sistema.emitir_certificado(args.participacao_id)
            print(f"Certificado emitido com sucesso. Código: {codigo}")
        elif args.comando == "historico-voluntario":
            historico = sistema.historico_voluntario(args.voluntario_id)
            print(formatar_historico_voluntario(historico))
            print(f"Carga horária total: {sistema.carga_horaria_voluntario(args.voluntario_id):.1f}h")
        elif args.comando == "exportar-csv":
            print(f"Arquivo exportado para: {sistema.exportar_associados_csv(args.saida)}")
        elif args.comando == "backup":
            print(f"Backup criado em: {sistema.backup(args.saida)}")
        elif args.comando == "resumo":
            resumo = sistema.resumo()
            print("Resumo de associados")
            print(f"- Total: {int(resumo['total'])}")
            print(f"- Ativos: {int(resumo['ativos'])}")
            print(f"- Inativos: {int(resumo['inativos'])}")
            print(f"- Previsão mensal: R$ {resumo['previsao_receita']:.2f}")
            print(f"- Total recebido: R$ {resumo['total_recebido']:.2f}")
            print(f"- Voluntários ativos: {int(resumo['voluntarios_ativos'])}")
    except Exception as exc:  # pragma: no cover
        print(f"Erro: {exc}")


if __name__ == "__main__":
    main()
