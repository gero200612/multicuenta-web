#!/usr/bin/env python3
"""Da de alta multicuenta.punchi.dev en el VPS: registro DNS en Cloudflare (nube gris) y app en Coolify desde el repo público.

Se corre EN el VPS como root: ssh vps python3 - < vps/alta.py
Lee los tokens de /root/coolify.token y /root/cloudflare.token; no imprime ninguno. Se puede correr de nuevo: no duplica nada.
"""
import json
import urllib.request

DOMINIO = 'multicuenta.punchi.dev'
ZONA = 'punchi.dev'
IP = '158.69.192.117'
REPO = 'https://github.com/gero200612/multicuenta-web'
SERVIDOR = '9ej6of76shhzldaokrsxpe1l'
COOLIFY = 'http://localhost:8000/api/v1'


def token(ruta):
    with open(ruta) as f:
        return f.read().strip()


def pedir(metodo, url, tok, cuerpo=None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(url, data=datos, method=metodo, headers={
        'Authorization': f'Bearer {tok}', 'Content-Type': 'application/json', 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            texto = r.read().decode()
            return json.loads(texto) if texto else {}
    except urllib.error.HTTPError as e:
        raise SystemExit(f'{metodo} {url.split("?")[0]} -> {e.code}: {e.read().decode()[:400]}')


# 1. DNS
cf = token('/root/cloudflare.token')
base = 'https://api.cloudflare.com/client/v4'
zona = pedir('GET', f'{base}/zones?name={ZONA}', cf)['result'][0]['id']
existentes = pedir('GET', f'{base}/zones/{zona}/dns_records?name={DOMINIO}', cf)['result']
if existentes:
    print(f'DNS: ya existe ({existentes[0]["type"]} {existentes[0]["content"]})')
else:
    pedir('POST', f'{base}/zones/{zona}/dns_records', cf,
          {'type': 'A', 'name': DOMINIO, 'content': IP, 'proxied': False, 'ttl': 1, 'comment': 'multicuenta-web en Coolify'})
    print(f'DNS: creado A {DOMINIO} -> {IP} (nube gris)')

# 2. Coolify
co = token('/root/coolify.token')
apps = pedir('GET', f'{COOLIFY}/applications', co)
app = next((a for a in apps if DOMINIO in (a.get('fqdn') or '')), None)
if app:
    uuid = app['uuid']
    print(f'Coolify: la app ya existe ({uuid})')
else:
    proyecto = pedir('POST', f'{COOLIFY}/projects', co, {'name': 'multicuenta', 'description': 'Propuesta de contenido multicuenta'})['uuid']
    uuid = pedir('POST', f'{COOLIFY}/applications/public', co, {
        'project_uuid': proyecto, 'server_uuid': SERVIDOR, 'environment_name': 'production',
        'git_repository': REPO, 'git_branch': 'main', 'build_pack': 'dockerfile', 'ports_exposes': '80',
        'domains': f'https://{DOMINIO}', 'name': 'multicuenta-web', 'instant_deploy': False,
    })['uuid']
    print(f'Coolify: app creada ({uuid})')

pedir('POST', f'{COOLIFY}/deploy?uuid={uuid}', co)
print(f'Despliegue pedido. En 1 o 2 minutos: https://{DOMINIO}')
