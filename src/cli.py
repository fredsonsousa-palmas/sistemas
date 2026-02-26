from __future__ import annotations

import argparse

from associados import SistemaAssociados, formatar_tabela


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="controle-associados",
        description="Sistema de controle de associados da Associação do Hospital de Amor.",
    )
    parser.add_argument("--db", default="associados.db", help="Caminho do banco SQLite.")

    sub = parser.add_subparsers(dest="comando", required=True)

    cadastrar = sub.add_parser("cadastrar", help="Cadastrar um novo associado.")
    cadastrar.add_argument("--nome", required=True)
    cadastrar.add_argument("--cpf", required=True)
    cadastrar.add_argument("--telefone", required=True)
    cadastrar.add_argument("--plano", required=True, help="Ex: Familiar, Individual")
    cadastrar.add_argument("--email", default="")
    cadastrar.add_argument("--cidade", default="")
    cadastrar.add_argument("--data-nascimento", default="")

    listar = sub.add_parser("listar", help="Listar associados cadastrados.")
    listar.add_argument("--ativos", action="store_true", help="Mostrar somente ativos.")

    buscar = sub.add_parser("buscar-cpf", help="Buscar associado por CPF.")
    buscar.add_argument("--cpf", required=True)

    status = sub.add_parser("status", help="Ativar ou inativar associado por ID.")
    status.add_argument("--id", type=int, required=True)
    status.add_argument("--ativo", choices=["sim", "nao"], required=True)

    excluir = sub.add_parser("excluir", help="Excluir associado por ID.")
    excluir.add_argument("--id", type=int, required=True)

    sub.add_parser("resumo", help="Exibir resumo de associados.")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sistema = SistemaAssociados(args.db)

    if args.comando == "cadastrar":
        associado_id = sistema.cadastrar_associado(
            nome=args.nome,
            cpf=args.cpf,
            telefone=args.telefone,
            plano=args.plano,
            email=args.email,
            cidade=args.cidade,
            data_nascimento=args.data_nascimento,
        )
        print(f"Associado cadastrado com sucesso. ID: {associado_id}")

    elif args.comando == "listar":
        associados = sistema.listar_associados(somente_ativos=args.ativos)
        print(formatar_tabela(associados))

    elif args.comando == "buscar-cpf":
        associado = sistema.buscar_por_cpf(args.cpf)
        if not associado:
            print("Associado não encontrado.")
            return
        print(formatar_tabela([associado]))

    elif args.comando == "status":
        atualizado = sistema.alterar_status(args.id, ativo=(args.ativo == "sim"))
        if atualizado:
            print("Status atualizado com sucesso.")
        else:
            print("Associado não encontrado para atualizar status.")

    elif args.comando == "excluir":
        excluido = sistema.excluir_associado(args.id)
        if excluido:
            print("Associado excluído com sucesso.")
        else:
            print("Associado não encontrado para exclusão.")

    elif args.comando == "resumo":
        resumo = sistema.resumo()
        print("Resumo de associados")
        print(f"- Total: {resumo['total']}")
        print(f"- Ativos: {resumo['ativos']}")
        print(f"- Inativos: {resumo['inativos']}")
        planos = [k for k in resumo if k.startswith('plano:')]
        if planos:
            print("- Por plano:")
            for plano_key in planos:
                plano = plano_key.split(":", maxsplit=1)[1]
                print(f"  - {plano}: {resumo[plano_key]}")


if __name__ == "__main__":
    main()
