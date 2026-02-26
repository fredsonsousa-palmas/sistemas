# Sistema de Controle de Associados - Associação Hospital de Amor

Este projeto implementa um sistema simples para cadastro e gestão de associados usando **Python + SQLite**.

## Funcionalidades

- Cadastro de associados.
- Listagem completa ou somente associados ativos.
- Busca por CPF.
- Alteração de status (ativo/inativo).
- Exclusão de associado.
- Resumo com totais e quantidade por plano.

## Requisitos

- Python 3.10+

## Como usar

No diretório do projeto:

```bash
python3 src/cli.py --help
```

### Cadastrar associado

```bash
python3 src/cli.py cadastrar \
  --nome "João da Silva" \
  --cpf "12345678901" \
  --telefone "17999998888" \
  --plano "Familiar" \
  --email "joao@email.com" \
  --cidade "Barretos" \
  --data-nascimento "1985-10-20"
```

### Listar associados

```bash
python3 src/cli.py listar
python3 src/cli.py listar --ativos
```

### Buscar por CPF

```bash
python3 src/cli.py buscar-cpf --cpf "12345678901"
```

### Alterar status

```bash
python3 src/cli.py status --id 1 --ativo nao
python3 src/cli.py status --id 1 --ativo sim
```

### Excluir associado

```bash
python3 src/cli.py excluir --id 1
```

### Resumo

```bash
python3 src/cli.py resumo
```

## Testes

```bash
python3 -m pytest -q
```
