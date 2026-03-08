# Sistema de Controle de Associados - Associação Hospital de Amor

Sistema completo para gestão administrativa e operacional da associação:

- Cadastro e atualização de associados.
- Controle de status ativo/inativo.
- Registro de pagamentos de mensalidade por competência.
- Relatório de inadimplentes.
- Gestão de voluntários e eventos.
- Registro de participação em eventos com histórico e carga horária total.
- Emissão de certificados para participações de voluntariado.
- Exportação CSV e backup do banco.

> Por padrão, os arquivos são gravados em `/home/sistemas` (banco, exportações e backups).
> Use `--storage-dir` para alterar o local base.

## Requisitos

- Python 3.10+
- `pytest` para rodar os testes

## Instalação rápida

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pytest
```

## Comandos principais

### Associados

```bash
python3 src/cli.py cadastrar --nome "João" --cpf 12345678901 --telefone 17999998888 --plano Familiar --valor-mensalidade 120
python3 src/cli.py listar
python3 src/cli.py atualizar --id 1 --nome "João Filho" --telefone 17999990000 --plano Premium --valor-mensalidade 180
python3 src/cli.py registrar-pagamento --associado-id 1 --competencia 2026-02 --valor 120 --forma pix
python3 src/cli.py inadimplentes --competencia 2026-02
```

### Voluntariado, eventos e certificados

```bash
python3 src/cli.py cadastrar-voluntario --nome "Carlos" --cpf 98765432100 --telefone 11977776666 --email carlos@email.com
python3 src/cli.py cadastrar-evento --titulo "Corrida Solidária" --data 2026-03-21 --local "Barretos" --carga 6 --descricao "Apoio logístico"
python3 src/cli.py registrar-participacao --voluntario-id 1 --evento-id 1 --funcao "Apoio"
python3 src/cli.py emitir-certificado --participacao-id 1
python3 src/cli.py historico-voluntario --voluntario-id 1
```

### Relatórios e utilitários

```bash
python3 src/cli.py resumo
python3 src/cli.py exportar-csv --saida associados.csv
python3 src/cli.py backup --saida backups/associados.db
python3 src/cli.py --storage-dir /home/sistemas --db associados.db resumo
```

## Testes

```bash
python3 -m pytest -q
```
