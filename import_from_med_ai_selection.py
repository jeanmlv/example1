"""Import one selected Med.ai S3 folder into a Domino dataset.

Python 3.8+ and AWS CLI required. Run in a terminal, not the RStudio console.
Temporary credentials are entered interactively and are not saved by this script.
"""
import getpass
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from urllib.parse import urlsplit

BASE = Path('/domino/datasets/local/clinical-trial-data')
REGION = 'us-east-1'


def ask(label, secret=False):
    return getpass.getpass(label) if secret else input(label).strip()


def parse_s3(value):
    parsed = urlsplit(value.strip())
    segments = parsed.path.strip('/').split('/')
    if (parsed.scheme != 's3' or not parsed.netloc or not parsed.path.strip('/')
            or parsed.query or parsed.fragment or any(x in ('.', '..', '') for x in segments)):
        raise ValueError('Informe um prefixo S3 valido: s3://bucket/pasta/subpasta/')
    return 's3://{}/{}/'.format(parsed.netloc, '/'.join(segments)), segments


def main():
    print('\n=== MED.AI S3 -> DOMINO: IMPORTACAO SELETIVA ===')
    source, segments = parse_s3(ask('Cole o caminho S3 COMPLETO da pasta desejada: '))
    name = ask('Nome da pasta do estudo no Domino (ex. CNTO1275CRD3005-STARDUST): ')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,149}', name) or name in ('.', '..'):
        raise ValueError('Nome de pasta invalido.')

    # Preserve the S3 hierarchy starting at the selected load-* directory.
    load_positions = [i for i, part in enumerate(segments) if re.fullmatch(r'load-[A-Za-z0-9_-]+', part, re.I)]
    if load_positions:
        relative = segments[load_positions[-1]:]
    else:
        print('Nao foi encontrado um diretorio load-* no caminho S3.')
        custom = ask('Subpasta relativa ao estudo para salvar (ex. extras/Metadata): ')
        relative = custom.strip('/').split('/')
        if not custom or any(p in ('', '.', '..') for p in relative):
            raise ValueError('Subpasta relativa invalida.')
    target = BASE / name
    for part in relative:
        target = target / part
    print('\nOrigem:  {}'.format(source))
    print('Destino: {}'.format(target))
    if ask('Confirmar caminhos? Digite SIM: ') != 'SIM':
        print('Cancelado.')
        return

    print('\nGere credenciais temporarias novas no Med.ai.')
    key = ask('Access Key ID: ', secret=True).strip()
    secret = ask('Secret Access Key: ', secret=True).strip()
    token = ask('Session Token: ', secret=True).strip()
    if not all((key, secret, token)):
        raise ValueError('Credenciais incompletas.')
    env = os.environ.copy()
    for item in ('AWS_PROFILE', 'AWS_DEFAULT_PROFILE', 'AWS_ROLE_ARN',
                 'AWS_WEB_IDENTITY_TOKEN_FILE', 'AWS_CONTAINER_CREDENTIALS_FULL_URI',
                 'AWS_CONTAINER_CREDENTIALS_RELATIVE_URI'):
        env.pop(item, None)
    env.update(AWS_ACCESS_KEY_ID=key, AWS_SECRET_ACCESS_KEY=secret,
               AWS_SESSION_TOKEN=token, AWS_DEFAULT_REGION=REGION,
               AWS_EC2_METADATA_DISABLED='true', AWS_PAGER='')
    del key, secret, token

    print('\n1/3 Listando arquivos da pasta selecionada...')
    listing = subprocess.run(['aws', 's3', 'ls', source, '--recursive'], env=env, check=False)
    if listing.returncode:
        raise RuntimeError('Nao foi possivel listar a pasta. Confira acesso e caminho.')
    print('\n2/3 Simulando importacao (arquivos existentes serao ignorados)...')
    args = ['aws', 's3', 'sync', source, str(target), '--ignore-existing', '--no-progress']
    dry = subprocess.run(args + ['--dryrun'], env=env, check=False)
    if dry.returncode:
        raise RuntimeError('Falha no dry-run; nada foi transferido.')
    if ask('\nDigite TRANSFERIR para importar apenas esta pasta: ') != 'TRANSFERIR':
        print('Cancelado sem transferencia.')
        return
    target.mkdir(parents=True, exist_ok=True)
    print('\n3/3 Transferindo...')
    result = subprocess.run(args, env=env, check=False)
    if result.returncode:
        raise RuntimeError('Transferencia com erro; alguns arquivos podem ter sido copiados.')
    print('\nImportacao concluida. Destino: {}'.format(target))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, EOFError, KeyboardInterrupt, FileNotFoundError) as exc:
        print('\nErro/cancelamento: {}'.format(exc), file=sys.stderr)
        sys.exit(1)
